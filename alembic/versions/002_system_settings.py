"""Add system_settings table for UI settings

Revision ID: 002
Revises: 001
Create Date: 2026-03-01
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "system_settings",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("payload", postgresql.JSONB(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("system_settings")

