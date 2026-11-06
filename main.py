# Entry point for the FastAPI server — initializes the app and wires in the auth and meeting routers.

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from auth import router as auth_router
from meeting import router as meeting_router

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(meeting_router)

@app.get("/health")
def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
