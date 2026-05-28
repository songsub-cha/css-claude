"""Initial schema: projects, sessions_history, gate_audit_log, daemon_runs

Revision ID: 0001
Revises:
Create Date: 2026-05-28

"""
from typing import Sequence, Union

from alembic import op

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Each statement is executed separately (asyncpg does not support multi-statement strings)
    op.execute("""
        CREATE TABLE projects (
          id SERIAL PRIMARY KEY,
          repo_root TEXT UNIQUE NOT NULL,
          repo_name TEXT NOT NULL,
          color TEXT NOT NULL DEFAULT '#3b82f6',
          registered_at TIMESTAMPTZ NOT NULL DEFAULT now(),
          last_seen_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """)
    op.execute("""
        CREATE TABLE sessions_history (
          id SERIAL PRIMARY KEY,
          project_id INT REFERENCES projects(id) ON DELETE CASCADE,
          session_id TEXT NOT NULL,
          idea TEXT NOT NULL,
          started_at TIMESTAMPTZ NOT NULL,
          finished_at TIMESTAMPTZ,
          final_phase TEXT NOT NULL,
          outcome TEXT NOT NULL CHECK (outcome IN ('completed','failed','aborted')),
          pr_url TEXT,
          phase_durations JSONB NOT NULL,
          snapshot JSONB NOT NULL,
          archived_at TIMESTAMPTZ NOT NULL DEFAULT now(),
          UNIQUE (project_id, session_id, archived_at)
        )
    """)
    op.execute("""
        CREATE TABLE gate_audit_log (
          id SERIAL PRIMARY KEY,
          project_id INT REFERENCES projects(id),
          session_id TEXT NOT NULL,
          gate TEXT NOT NULL CHECK (gate IN ('gate2_pre_execute','gate3_pre_pr')),
          reached_at TIMESTAMPTZ NOT NULL,
          approved_at TIMESTAMPTZ,
          approval_source TEXT CHECK (approval_source IN ('dashboard_drag','terminal_ask')),
          resume_status TEXT CHECK (resume_status IN ('success','failed','retrying')),
          retry_count INT NOT NULL DEFAULT 0,
          error_message TEXT
        )
    """)
    op.execute("""
        CREATE TABLE daemon_runs (
          id SERIAL PRIMARY KEY,
          session_id TEXT NOT NULL,
          command TEXT NOT NULL,
          started_at TIMESTAMPTZ NOT NULL,
          finished_at TIMESTAMPTZ,
          exit_code INT,
          stdout_tail TEXT,
          stderr_tail TEXT
        )
    """)
    op.execute(
        "CREATE INDEX idx_history_project_finished ON sessions_history(project_id, finished_at DESC)"
    )
    op.execute(
        "CREATE INDEX idx_audit_session ON gate_audit_log(session_id, reached_at DESC)"
    )
    op.execute(
        "CREATE INDEX idx_runs_session ON daemon_runs(session_id, started_at DESC)"
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS daemon_runs")
    op.execute("DROP TABLE IF EXISTS gate_audit_log")
    op.execute("DROP TABLE IF EXISTS sessions_history")
    op.execute("DROP TABLE IF EXISTS projects")
