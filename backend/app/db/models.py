"""SQLAlchemy database models for EconChat.

These models define the database schema for:
- User sessions and preferences
- Conversation history
- Extracted entities
- Cached data
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    Boolean,
    DateTime,
    Text,
    JSON,
    ForeignKey,
    Index,
)
from sqlalchemy.orm import relationship, DeclarativeBase
from sqlalchemy.dialects.postgresql import UUID, ARRAY
import uuid


class Base(DeclarativeBase):
    """Base class for all models."""

    pass


class Session(Base):
    """User chat session."""

    __tablename__ = "sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=False)
    user_id = Column(String(255), nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Session metadata
    preferences = Column(JSON, default=dict)
    is_archived = Column(Boolean, default=False)

    # Relationships
    messages = relationship("Message", back_populates="session", cascade="all, delete-orphan")
    entities = relationship("Entity", back_populates="session", cascade="all, delete-orphan")


class Message(Base):
    """Chat message within a session."""

    __tablename__ = "messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id"), nullable=False, index=True)
    role = Column(String(20), nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Message metadata
    data = Column(JSON, nullable=True)  # Economic data if any
    visualization = Column(JSON, nullable=True)  # Viz config
    sources = Column(JSON, nullable=True)  # Data sources
    tool_calls = Column(JSON, nullable=True)  # Tools used

    # For RAG - embedding vector (requires pgvector extension)
    # embedding = Column(Vector(1536), nullable=True)

    # Relationships
    session = relationship("Session", back_populates="messages")

    __table_args__ = (
        Index("ix_messages_session_created", "session_id", "created_at"),
    )


class Entity(Base):
    """Extracted entity from conversations (countries, indicators, etc.)."""

    __tablename__ = "entities"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id"), nullable=False, index=True)
    entity_type = Column(String(50), nullable=False)  # country, indicator, time_period
    value = Column(JSON, nullable=False)  # Entity data
    first_mentioned = Column(DateTime, default=datetime.utcnow)
    mention_count = Column(Integer, default=1)

    # Relationships
    session = relationship("Session", back_populates="entities")

    __table_args__ = (
        Index("ix_entities_session_type", "session_id", "entity_type"),
    )


class CachedData(Base):
    """Cached API responses to reduce external calls."""

    __tablename__ = "cached_data"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cache_key = Column(String(512), unique=True, nullable=False, index=True)
    data = Column(JSON, nullable=False)
    source = Column(String(50), nullable=False)  # world_bank, imf, etc.
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=False)

    # Metadata
    indicator_code = Column(String(100), nullable=True, index=True)
    country_codes = Column(ARRAY(String), nullable=True)
    start_year = Column(Integer, nullable=True)
    end_year = Column(Integer, nullable=True)


class Document(Base):
    """Indexed internal document for RAG."""

    __tablename__ = "documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(500), nullable=False)
    source = Column(String(100), nullable=False)  # google_drive, sharepoint
    source_id = Column(String(255), nullable=True)  # External ID
    url = Column(Text, nullable=True)
    content = Column(Text, nullable=True)  # Full text content
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Document metadata
    doc_type = Column(String(50), nullable=True)  # pdf, docx, etc.
    file_size = Column(Integer, nullable=True)
    metadata = Column(JSON, default=dict)

    # For RAG - embedding vector
    # embedding = Column(Vector(1536), nullable=True)

    # Related entities
    countries = Column(ARRAY(String), nullable=True)
    indicators = Column(ARRAY(String), nullable=True)


class UserFeedback(Base):
    """User feedback on responses for improvement."""

    __tablename__ = "user_feedback"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    message_id = Column(UUID(as_uuid=True), ForeignKey("messages.id"), nullable=False)
    rating = Column(Integer, nullable=False)  # 1-5
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


# Database setup functions
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker


def get_engine(database_url: str):
    """Create async database engine."""
    return create_async_engine(database_url, echo=True)


def get_session_maker(engine):
    """Create async session maker."""
    return sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
