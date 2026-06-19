"""add send tracking fields

Revision ID: 202606190002
Revises: 202606190001
Create Date: 2026-06-19
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "202606190002"
down_revision: str | None = "202606190001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "notifications",
        sa.Column(
            "attempt_count",
            sa.Integer(),
            server_default="0",
            nullable=False,
        ),
    )
    op.add_column(
        "notifications",
        sa.Column("max_attempts", sa.Integer(), server_default="3", nullable=False),
    )
    op.add_column(
        "notifications",
        sa.Column("last_attempt_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "notifications",
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "notifications",
        sa.Column("last_error", sa.String(length=500), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("notifications", "last_error")
    op.drop_column("notifications", "sent_at")
    op.drop_column("notifications", "last_attempt_at")
    op.drop_column("notifications", "max_attempts")
    op.drop_column("notifications", "attempt_count")
