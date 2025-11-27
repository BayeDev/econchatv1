"""Chat API endpoints for query processing."""

from typing import Optional
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import json

from app.orchestration.router import QueryRouter
from app.context.manager import ContextManager
from app.config import get_settings

router = APIRouter()
settings = get_settings()


class ChatRequest(BaseModel):
    """Request model for chat endpoint."""

    query: str
    session_id: Optional[str] = None
    stream: bool = True


class ChatResponse(BaseModel):
    """Response model for chat endpoint."""

    message_id: str
    content: str
    data: Optional[dict] = None
    visualization: Optional[dict] = None
    sources: Optional[list[dict]] = None
    suggested_followups: Optional[list[str]] = None


# Initialize components
query_router = QueryRouter()
context_manager = ContextManager()


@router.post("")
async def chat(request: ChatRequest):
    """
    Process a user query with intelligent orchestration.

    This endpoint:
    1. Retrieves conversation context
    2. Routes query through Claude for intent classification
    3. Executes appropriate tools (data fetch, document search, etc.)
    4. Generates response with visualization config
    5. Streams response back to client
    """
    try:
        # Get conversation context
        context = await context_manager.get_context(request.session_id)

        if request.stream:
            # Stream response using Server-Sent Events
            return StreamingResponse(
                stream_response(request.query, context, request.session_id),
                media_type="text/event-stream",
            )
        else:
            # Return full response at once
            result = await query_router.process(request.query, context)
            return ChatResponse(
                message_id=result.message_id,
                content=result.content,
                data=result.data,
                visualization=result.visualization,
                sources=result.sources,
                suggested_followups=result.suggested_followups,
            )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def stream_response(query: str, context: dict, session_id: Optional[str]):
    """Generator for streaming response via SSE."""

    # Send initial event
    yield f"data: {json.dumps({'type': 'start', 'message': 'Processing query...'})}\n\n"

    try:
        # Process through orchestration layer
        async for event in query_router.process_stream(query, context):
            if event["type"] == "thinking":
                yield f"data: {json.dumps({'type': 'thinking', 'content': event['content']})}\n\n"

            elif event["type"] == "tool_call":
                yield f"data: {json.dumps({'type': 'tool', 'tool': event['tool'], 'status': 'calling'})}\n\n"

            elif event["type"] == "tool_result":
                yield f"data: {json.dumps({'type': 'tool', 'tool': event['tool'], 'status': 'complete', 'data': event.get('data')})}\n\n"

            elif event["type"] == "content":
                yield f"data: {json.dumps({'type': 'content', 'content': event['content']})}\n\n"

            elif event["type"] == "visualization":
                yield f"data: {json.dumps({'type': 'visualization', 'config': event['config'], 'data': event['data']})}\n\n"

        # Save to context if session provided
        if session_id:
            await context_manager.save_message(session_id, query, event)

        # Send completion event
        yield f"data: {json.dumps({'type': 'done'})}\n\n"

    except Exception as e:
        yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"


@router.get("/context/{session_id}")
async def get_context(session_id: str):
    """Get the current conversation context for a session."""
    context = await context_manager.get_context(session_id)
    return {
        "session_id": session_id,
        "entities": context.get("entities", {}),
        "recent_queries": context.get("recent_queries", []),
        "preferences": context.get("preferences", {}),
    }


@router.post("/feedback")
async def submit_feedback(
    message_id: str,
    rating: int,
    comment: Optional[str] = None,
):
    """Submit feedback on a response for improvement."""
    # Store feedback for training/improvement
    return {"status": "received", "message_id": message_id}
