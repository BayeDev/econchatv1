"""Session management API endpoints."""

from typing import Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import uuid

router = APIRouter()


# In-memory session storage (will be replaced with database)
sessions_store: dict = {}


class SessionCreate(BaseModel):
    """Request model for creating a session."""

    title: Optional[str] = None
    user_id: Optional[str] = None


class SessionResponse(BaseModel):
    """Response model for session data."""

    id: str
    title: str
    created_at: datetime
    updated_at: datetime
    message_count: int
    entities: dict


class SessionListResponse(BaseModel):
    """Response model for session list."""

    sessions: list[SessionResponse]
    total: int


@router.post("", response_model=SessionResponse)
async def create_session(request: SessionCreate):
    """Create a new chat session."""
    session_id = str(uuid.uuid4())
    now = datetime.utcnow()

    session = {
        "id": session_id,
        "title": request.title or f"Session {now.strftime('%Y-%m-%d %H:%M')}",
        "created_at": now,
        "updated_at": now,
        "user_id": request.user_id,
        "messages": [],
        "entities": {
            "countries": [],
            "indicators": [],
            "time_periods": [],
        },
        "preferences": {},
    }

    sessions_store[session_id] = session

    return SessionResponse(
        id=session_id,
        title=session["title"],
        created_at=session["created_at"],
        updated_at=session["updated_at"],
        message_count=0,
        entities=session["entities"],
    )


@router.get("", response_model=SessionListResponse)
async def list_sessions(
    user_id: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
):
    """List all sessions, optionally filtered by user."""
    all_sessions = list(sessions_store.values())

    if user_id:
        all_sessions = [s for s in all_sessions if s.get("user_id") == user_id]

    # Sort by updated_at descending
    all_sessions.sort(key=lambda s: s["updated_at"], reverse=True)

    # Paginate
    paginated = all_sessions[offset : offset + limit]

    return SessionListResponse(
        sessions=[
            SessionResponse(
                id=s["id"],
                title=s["title"],
                created_at=s["created_at"],
                updated_at=s["updated_at"],
                message_count=len(s["messages"]),
                entities=s["entities"],
            )
            for s in paginated
        ],
        total=len(all_sessions),
    )


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(session_id: str):
    """Get a specific session by ID."""
    session = sessions_store.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    return SessionResponse(
        id=session["id"],
        title=session["title"],
        created_at=session["created_at"],
        updated_at=session["updated_at"],
        message_count=len(session["messages"]),
        entities=session["entities"],
    )


@router.get("/{session_id}/messages")
async def get_session_messages(
    session_id: str,
    limit: int = 50,
    before: Optional[str] = None,
):
    """Get messages for a session."""
    session = sessions_store.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    messages = session["messages"]

    # Filter if 'before' cursor provided
    if before:
        messages = [m for m in messages if m["id"] < before]

    # Return most recent messages
    return {
        "messages": messages[-limit:],
        "total": len(session["messages"]),
    }


@router.delete("/{session_id}")
async def delete_session(session_id: str):
    """Delete a session."""
    if session_id not in sessions_store:
        raise HTTPException(status_code=404, detail="Session not found")

    del sessions_store[session_id]
    return {"status": "deleted", "session_id": session_id}


@router.patch("/{session_id}")
async def update_session(session_id: str, title: Optional[str] = None):
    """Update session metadata."""
    session = sessions_store.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if title:
        session["title"] = title
    session["updated_at"] = datetime.utcnow()

    return SessionResponse(
        id=session["id"],
        title=session["title"],
        created_at=session["created_at"],
        updated_at=session["updated_at"],
        message_count=len(session["messages"]),
        entities=session["entities"],
    )
