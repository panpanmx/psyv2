from typing import Any

from sqlalchemy import JSON, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, CreatedAtMixin, TimestampMixin


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    nickname: Mapped[str] = mapped_column(String(120), default="")
    age_group: Mapped[str] = mapped_column(String(40), default="unknown")
    school_stage: Mapped[str] = mapped_column(String(120), default="")

    conversations: Mapped[list["Conversation"]] = relationship(back_populates="user")
    profile: Mapped["UserProfile | None"] = relationship(back_populates="user")


class Conversation(TimestampMixin, Base):
    __tablename__ = "conversations"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    title: Mapped[str] = mapped_column(String(200), default="心理支持对话")

    user: Mapped[User] = relationship(back_populates="conversations")
    messages: Mapped[list["Message"]] = relationship(back_populates="conversation")


class Message(CreatedAtMixin, Base):
    __tablename__ = "messages"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    conversation_id: Mapped[str] = mapped_column(ForeignKey("conversations.id"), index=True)
    role: Mapped[str] = mapped_column(String(20))
    content: Mapped[str] = mapped_column(Text)
    content_hash: Mapped[str] = mapped_column(String(128), index=True)
    risk_snapshot: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)

    conversation: Mapped[Conversation] = relationship(back_populates="messages")


class UserProfile(TimestampMixin, Base):
    __tablename__ = "user_profiles"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), unique=True, index=True)
    profile_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    latest_summary: Mapped[str] = mapped_column(Text, default="")
    risk_trend_json: Mapped[list[dict[str, str]]] = mapped_column(JSON, default=list)
    updated_by_message_id: Mapped[str | None] = mapped_column(String(64), nullable=True)

    user: Mapped[User] = relationship(back_populates="profile")


class Assessment(CreatedAtMixin, Base):
    __tablename__ = "assessments"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    conversation_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    scale_type: Mapped[str] = mapped_column(String(40), index=True)
    answers: Mapped[list[int] | dict[str, Any]] = mapped_column(JSON)
    score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    severity: Mapped[str] = mapped_column(String(80), default="")
    interpretation: Mapped[str] = mapped_column(Text, default="")


class RiskAssessment(CreatedAtMixin, Base):
    __tablename__ = "risk_assessments"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    conversation_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    message_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    depression_risk: Mapped[str] = mapped_column(String(40), default="unknown")
    anxiety_risk: Mapped[str] = mapped_column(String(40), default="unknown")
    sleep_risk: Mapped[str] = mapped_column(String(40), default="unknown")
    crisis_level: Mapped[str] = mapped_column(String(10), default="s0")
    function_impairment_level: Mapped[str] = mapped_column(String(40), default="unknown")
    evidence: Mapped[list[dict[str, str]]] = mapped_column(JSON, default=list)
    recommended_next_step: Mapped[dict[str, str]] = mapped_column(JSON, default=dict)


class AuditLog(CreatedAtMixin, Base):
    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    request_id: Mapped[str] = mapped_column(String(120), index=True)
    user_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    conversation_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    event_type: Mapped[str] = mapped_column(String(120), index=True)
    event_payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)


class KnowledgeChunkModel(TimestampMixin, Base):
    __tablename__ = "knowledge_chunks"

    chunk_id: Mapped[str] = mapped_column(String(160), primary_key=True)
    doc_id: Mapped[str] = mapped_column(String(120), index=True)
    title: Mapped[str] = mapped_column(String(240), default="")
    source_path: Mapped[str] = mapped_column(String(500), default="")
    section: Mapped[str] = mapped_column(String(240), default="")
    content: Mapped[str] = mapped_column(Text)
    ordinal: Mapped[int] = mapped_column(Integer)
    embedding: Mapped[list[float]] = mapped_column(JSON, default=list)
    content_hash: Mapped[str] = mapped_column(String(128), index=True)
