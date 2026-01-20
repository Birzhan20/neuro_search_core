"""CRUD operations for chat sessions and messages."""
from __future__ import annotations

import uuid

from sqlalchemy import select

from app.core.database import db
from app.models.chat import ChatSession, Message


async def get_session(session_id: str) -> ChatSession | None:
    """Get chat session by ID."""
    try:
        sid = uuid.UUID(session_id)
    except ValueError:
        return None

    async with db.get_session() as session:
        result = await session.execute(
            select(ChatSession).where(ChatSession.id == sid)
        )
        return result.scalar_one_or_none()


async def create_session() -> ChatSession:
    """Create new chat session."""
    async with db.get_session() as session:
        new_session = ChatSession()
        session.add(new_session)
        await session.commit()
        await session.refresh(new_session)
        return new_session


async def get_or_create_session(session_id: str | None) -> tuple[uuid.UUID, bool]:
    """Get existing session or create new one. Returns (session_id, is_new)."""
    if session_id:
        existing = await get_session(session_id)
        if existing:
            return existing.id, False

    new_session = await create_session()
    return new_session.id, True


async def get_messages(session_id: uuid.UUID, limit: int = 10) -> list[Message]:
    """Get recent messages from session."""
    async with db.get_session() as session:
        result = await session.execute(
            select(Message)
            .where(Message.session_id == session_id)
            .order_by(Message.created_at.desc())
            .limit(limit)
        )
        messages = list(result.scalars().all())
        messages.reverse()
        return messages


async def save_message(session_id: uuid.UUID, role: str, content: str) -> Message:
    """Save message to session."""
    async with db.get_session() as session:
        msg = Message(session_id=session_id, role=role, content=content)
        session.add(msg)
        await session.commit()
        await session.refresh(msg)
        return msg
