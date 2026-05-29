"""Epic/Phase hierarchy: add kind/parent_slug/phase_index/phase_label/depends_on
to sessions_history (D2 — extend the table, no separate epics table).

Legacy rows backfill automatically via the column server-defaults
(kind='epic', parent_slug=NULL, depends_on='[]') so existing single-session
history renders as single-Phase Epics (D9).

Revision ID: 0002
Revises: 0001
Create Date: 2026-05-30

"""
from typing import Sequence, Union

from alembic import op

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # One statement per op.execute (asyncpg does not support multi-statement strings).
    op.execute("ALTER TABLE sessions_history ADD COLUMN kind TEXT NOT NULL DEFAULT 'epic'")
    op.execute("ALTER TABLE sessions_history ADD COLUMN parent_slug TEXT")
    op.execute("ALTER TABLE sessions_history ADD COLUMN phase_index INT")
    op.execute("ALTER TABLE sessions_history ADD COLUMN phase_label TEXT")
    op.execute(
        "ALTER TABLE sessions_history ADD COLUMN depends_on JSONB NOT NULL DEFAULT '[]'::jsonb"
    )
    op.execute(
        "ALTER TABLE sessions_history "
        "ADD CONSTRAINT ck_sessions_history_kind CHECK (kind IN ('epic','phase'))"
    )
    op.execute(
        "CREATE INDEX idx_history_project_parent "
        "ON sessions_history(project_id, parent_slug)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_history_project_parent")
    op.execute(
        "ALTER TABLE sessions_history DROP CONSTRAINT IF EXISTS ck_sessions_history_kind"
    )
    for col in ("depends_on", "phase_label", "phase_index", "parent_slug", "kind"):
        op.execute(f"ALTER TABLE sessions_history DROP COLUMN IF EXISTS {col}")
