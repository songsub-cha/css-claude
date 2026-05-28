"""SQLAlchemy 2.x ORM models for the CSS Pipeline Dashboard.

4 tables mirroring the Alembic DDL in 0001_initial.py:
  - projects
  - sessions_history
  - gate_audit_log
  - daemon_runs
"""
from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from sqlalchemy import TIMESTAMP


class Base(DeclarativeBase):
    pass


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    repo_root: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    repo_name: Mapped[str] = mapped_column(Text, nullable=False)
    color: Mapped[str] = mapped_column(
        Text, nullable=False, server_default="#3b82f6"
    )
    registered_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False, server_default=func.now()
    )
    last_seen_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False, server_default=func.now()
    )

    # Relationships
    sessions: Mapped[list[SessionHistory]] = relationship(
        "SessionHistory", back_populates="project", cascade="all, delete-orphan"
    )
    gate_logs: Mapped[list[GateAuditLog]] = relationship(
        "GateAuditLog", back_populates="project"
    )


class SessionHistory(Base):
    __tablename__ = "sessions_history"
    __table_args__ = (
        CheckConstraint(
            "outcome IN ('completed','failed','aborted')", name="ck_sessions_history_outcome"
        ),
        UniqueConstraint("project_id", "session_id", "archived_at", name="uq_sessions_history"),
        Index("idx_history_project_finished", "project_id", "finished_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=True
    )
    session_id: Mapped[str] = mapped_column(Text, nullable=False)
    idea: Mapped[str] = mapped_column(Text, nullable=False)
    started_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False
    )
    finished_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True
    )
    final_phase: Mapped[str] = mapped_column(Text, nullable=False)
    outcome: Mapped[str] = mapped_column(Text, nullable=False)
    pr_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    phase_durations: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    snapshot: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    archived_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False, server_default=func.now()
    )

    project: Mapped[Project | None] = relationship("Project", back_populates="sessions")


class GateAuditLog(Base):
    __tablename__ = "gate_audit_log"
    __table_args__ = (
        CheckConstraint(
            "gate IN ('gate2_pre_execute','gate3_pre_pr')", name="ck_gate_audit_log_gate"
        ),
        CheckConstraint(
            "approval_source IN ('dashboard_drag','terminal_ask') OR approval_source IS NULL",
            name="ck_gate_audit_log_approval_source",
        ),
        CheckConstraint(
            "resume_status IN ('success','failed','retrying') OR resume_status IS NULL",
            name="ck_gate_audit_log_resume_status",
        ),
        Index("idx_audit_session", "session_id", "reached_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("projects.id"), nullable=True
    )
    session_id: Mapped[str] = mapped_column(Text, nullable=False)
    gate: Mapped[str] = mapped_column(Text, nullable=False)
    reached_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False
    )
    approved_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True
    )
    approval_source: Mapped[str | None] = mapped_column(Text, nullable=True)
    resume_status: Mapped[str | None] = mapped_column(Text, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    project: Mapped[Project | None] = relationship("Project", back_populates="gate_logs")


class DaemonRun(Base):
    __tablename__ = "daemon_runs"
    __table_args__ = (
        Index("idx_runs_session", "session_id", "started_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    session_id: Mapped[str] = mapped_column(Text, nullable=False)
    command: Mapped[str] = mapped_column(Text, nullable=False)
    started_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False
    )
    finished_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True
    )
    exit_code: Mapped[int | None] = mapped_column(Integer, nullable=True)
    stdout_tail: Mapped[str | None] = mapped_column(Text, nullable=True)
    stderr_tail: Mapped[str | None] = mapped_column(Text, nullable=True)
