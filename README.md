# Lindy Meeting

A FastAPI backend for managing meeting notes. Users register and log in with JWT authentication, create meetings, write notes, and use Claude (Anthropic API) to automatically extract action items — each with a task, owner, and due date — from those notes. Data is stored in PostgreSQL.

## Features

- Email/password registration and login (bcrypt-hashed passwords, JWT bearer tokens)
- Create, list, view, and delete meetings — every query is scoped to the logged-in user
- Add or update notes on a meeting
- AI action-item extraction: sends the meeting's title and notes to Claude, then saves the returned action items
- CORS enabled for a frontend at `http://localhost:3000`

## Tech stack

Python 3.10+ (developed on 3.13) · FastAPI · Uvicorn · PostgreSQL (psycopg2) · python-jose (JWT) · passlib + bcrypt · Anthropic Python SDK

## Setup

**1. Clone and create a virtual environment**

```sh
git clone https://github.com/atiman-rohatgi/lindy_meeting.git
cd lindy_meeting
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

**2. Configure environment variables**

```sh
cp .env.example .env
```

Then edit `.env`:

| Variable | Description |
|---|---|
| `DATABASE_URL` | Postgres connection string, e.g. `postgresql://user:password@localhost:5432/meeting` |
| `JWT_SECRET` | Long random string used to sign tokens. Generate one with `python3 -c "import secrets; print(secrets.token_urlsafe(64))"` |
| `JWT_ALGORITHM` | Signing algorithm, `HS256` |
| `JWT_EXPIRY_MINUTES` | Token lifetime in minutes, e.g. `30` |
| `ANTHROPIC_API_KEY` | Your Anthropic API key (starts with `sk-ant-`) |

`.env` is git-ignored; never commit it.

**3. Create the database**

With PostgreSQL running:

```sh
createdb meeting
psql -d meeting -f schema.sql
```

**4. Run the server**

```sh
python main.py
# or: uvicorn main:app --reload
```

The API runs at `http://localhost:8000`. Interactive docs are at `http://localhost:8000/docs`.

## API endpoints

All `/meetings` routes require an `Authorization: Bearer <token>` header, using the token returned by `/auth/login`.

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Health check |
| `POST` | `/auth/register` | Create a user (`email`, `password`) |
| `POST` | `/auth/login` | Log in and receive a JWT access token |
| `GET` | `/meetings` | List your meetings |
| `POST` | `/meetings` | Create a meeting (`title`, `attendees`, `date`) |
| `GET` | `/meetings/{id}` | Get a meeting and its action items |
| `PATCH` | `/meetings/{id}/notes` | Update a meeting's notes |
| `POST` | `/meetings/{id}/action-items` | Extract action items from the notes with Claude (replaces existing ones) |
| `DELETE` | `/meetings/{id}` | Delete a meeting and its action items |

## Project files

| File | Contents |
|---|---|
| `main.py` | Entry point: creates the FastAPI app, configures CORS, registers the auth and meeting routers, defines `/health`, and runs Uvicorn on port 8000 |
| `auth.py` | `/auth/register` and `/auth/login` routes: checks for duplicate emails, hashes passwords, verifies credentials, and issues JWTs |
| `meeting.py` | All `/meetings` routes (create, list, get, update notes, delete) plus the Claude-powered action-item extraction |
| `security.py` | Password hashing and verification (bcrypt), JWT creation and decoding, and the `get_current_user` dependency that protects routes |
| `database.py` | Postgres connection pool (1–10 connections) and the `get_db()` context manager, which commits on success and rolls back on error |
| `schema.sql` | Creates the `users`, `meetings`, and `action_items` tables with UUID primary keys and cascading deletes |
| `requirements.txt` | Pinned Python dependencies |
| `.env.example` | Template listing the required environment variables |
| `.gitignore` | Keeps `.env`, `.venv/`, `__pycache__/`, and editor/OS files out of git |
