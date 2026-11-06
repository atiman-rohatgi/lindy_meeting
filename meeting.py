# Contains all meeting-related routes: create, list, get, update notes, extract action items, delete.

import os
import json
import anthropic
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from psycopg2 import DataError
from database import get_db
from security import get_current_user

router = APIRouter()

# instantiated once at startup so the same client is reused across all requests
anthropic_client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# --- Pydantic models ---

class CreateMeetingRequest(BaseModel):
    title: str
    attendees: str
    date: str

class ActionItem(BaseModel):
    id: str
    task: str
    owner: str
    due_date: str

class UpdateNotesRequest(BaseModel):
    notes: str

# --- Routes ---

# decodes jwt, queries all meetings for that user, returns empty list if none
@router.get("/meetings")
def get_meetings(user_id: str = Depends(get_current_user)):
    with get_db() as (_, cursor):
        cursor.execute(
            "SELECT id, title, attendees, date, status, notes, created_at FROM meetings WHERE user_id = %s",
            (user_id,)
        )
        rows = cursor.fetchall()

    return [dict(row) for row in rows]

# pydantic validates body, decodes jwt, inserts meeting into db, returns created object with 201
@router.post("/meetings", status_code=201)
def create_meeting(data: CreateMeetingRequest, user_id: str = Depends(get_current_user)):
    with get_db() as (_, cursor):
        cursor.execute(
            """INSERT INTO meetings (title, attendees, date, user_id)
               VALUES (%s, %s, %s, %s)
               RETURNING id, title, attendees, date, status, notes, created_at""",
            (data.title, data.attendees, data.date, user_id)
        )
        meeting = cursor.fetchone()

    return dict(meeting)

# decodes jwt, fetches the meeting by id scoped to the user, attaches its action items — 404 if not found or invalid uuid
@router.get("/meetings/{meeting_id}")
def get_meeting(meeting_id: str, user_id: str = Depends(get_current_user)):
    try:
        with get_db() as (_, cursor):
            cursor.execute(
                "SELECT id, title, attendees, date, status, notes, created_at FROM meetings WHERE id = %s AND user_id = %s",
                (meeting_id, user_id)
            )
            meeting = cursor.fetchone()

            if not meeting:
                raise HTTPException(status_code=404, detail="Meeting not found")

            cursor.execute(
                "SELECT id, task, owner, due_date FROM action_items WHERE meeting_id = %s",
                (meeting_id,)
            )
            action_items = cursor.fetchall()
    except DataError:
        raise HTTPException(status_code=404, detail="Meeting not found")

    result = dict(meeting)
    result["action_items"] = [dict(item) for item in action_items]
    return result

# decodes jwt, updates notes on the meeting scoped to user, returns full meeting object with action items — 404 if not found
@router.patch("/meetings/{meeting_id}/notes")
def update_notes(meeting_id: str, data: UpdateNotesRequest, user_id: str = Depends(get_current_user)):
    try:
        with get_db() as (_, cursor):
            cursor.execute(
                """UPDATE meetings SET notes = %s
                   WHERE id = %s AND user_id = %s
                   RETURNING id, title, attendees, date, status, notes, created_at""",
                (data.notes, meeting_id, user_id)
            )
            meeting = cursor.fetchone()

            if not meeting:
                raise HTTPException(status_code=404, detail="Meeting not found")

            cursor.execute(
                "SELECT id, task, owner, due_date FROM action_items WHERE meeting_id = %s",
                (meeting_id,)
            )
            action_items = cursor.fetchall()
    except DataError:
        raise HTTPException(status_code=404, detail="Meeting not found")

    result = dict(meeting)
    result["action_items"] = [dict(item) for item in action_items]
    return result

# decodes jwt, fetches meeting title+notes, sends to anthropic, persists extracted action items, returns them
@router.post("/meetings/{meeting_id}/action-items")
def extract_action_items(meeting_id: str, user_id: str = Depends(get_current_user)):
    try:
        with get_db() as (_, cursor):
            cursor.execute(
                "SELECT title, notes FROM meetings WHERE id = %s AND user_id = %s",
                (meeting_id, user_id)
            )
            meeting = cursor.fetchone()

            if not meeting:
                raise HTTPException(status_code=404, detail="Meeting not found")

            prompt = f"""You are a meeting assistant. Given the following meeting title and notes, extract all action items mentioned.

Meeting title: {meeting['title']}
Meeting notes: {meeting['notes']}

Return a JSON array of action items. Each item must have:
- task: what needs to be done
- owner: who is responsible (if mentioned, otherwise "Unassigned")
- due_date: when it's due (if mentioned, otherwise "TBD")

Return only valid JSON. No explanation. No markdown. Example format:
[
  {{"task": "Send follow-up email", "owner": "Alice", "due_date": "2025-04-25"}},
  {{"task": "Review proposal", "owner": "Unassigned", "due_date": "TBD"}}
]"""

            message = anthropic_client.messages.create(
                model="claude-opus-4-7",
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}]
            )

            try:
                items = json.loads(message.content[0].text)
            except json.JSONDecodeError:
                raise HTTPException(status_code=500, detail="LLM returned malformed JSON, could not parse action items")

            cursor.execute("DELETE FROM action_items WHERE meeting_id = %s", (meeting_id,))

            inserted = []
            for item in items:
                cursor.execute(
                    """INSERT INTO action_items (task, owner, due_date, meeting_id)
                       VALUES (%s, %s, %s, %s)
                       RETURNING id, task, owner, due_date""",
                    (item["task"], item["owner"], item["due_date"], meeting_id)
                )
                inserted.append(dict(cursor.fetchone()))

    except DataError:
        raise HTTPException(status_code=404, detail="Meeting not found")

    return {"action_items": inserted}

# decodes jwt, deletes meeting scoped to user — cascade removes action items — 404 if not found or not authorized
@router.delete("/meetings/{meeting_id}")
def delete_meeting(meeting_id: str, user_id: str = Depends(get_current_user)):
    try:
        with get_db() as (_, cursor):
            cursor.execute(
                "DELETE FROM meetings WHERE id = %s AND user_id = %s RETURNING id",
                (meeting_id, user_id)
            )
            deleted = cursor.fetchone()

            if not deleted:
                raise HTTPException(status_code=404, detail="Meeting not found")
    except DataError:
        raise HTTPException(status_code=404, detail="Meeting not found")

    return {"message": "Meeting deleted"}
