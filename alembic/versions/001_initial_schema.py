"""Initial database schema migration

Revision ID: 001
Revises: 
Create Date: 2026-02-22
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# Revision identifiers
revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── alerts ────────────────────────────────────────────────────────────────
    op.create_table(
        "alerts",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source_integration", sa.String(50), nullable=False),
        sa.Column("external_id", sa.String(100), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column("raw_data", postgresql.JSONB(), nullable=False),
        sa.Column("normalized_data", postgresql.JSONB(), nullable=True),
        sa.Column("risk_score", sa.Integer(), nullable=True),
        sa.Column("severity", sa.String(20), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="New"),
        sa.CheckConstraint("risk_score >= 0 AND risk_score <= 100"),
        sa.CheckConstraint("severity IN ('Info','Low','Medium','High','Critical')"),
        sa.CheckConstraint("status IN ('New','InProgress','Closed','FalsePositive')"),
        sa.PrimaryKeyConstraint("id"),
    )

    # ── playbooks ─────────────────────────────────────────────────────────────
    op.create_table(
        "playbooks",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(100), nullable=False, unique=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("trigger_severity", postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column("steps_definition", postgresql.JSONB(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    # ── enrichment_results ────────────────────────────────────────────────────
    op.create_table(
        "enrichment_results",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("alert_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("observable_type", sa.String(50), nullable=False),
        sa.Column("observable_value", sa.Text(), nullable=False),
        sa.Column("source_provider", sa.String(50), nullable=False),
        sa.Column("result_data", postgresql.JSONB(), nullable=True),
        sa.Column("reputation_score", sa.Float(), nullable=True),
        sa.Column("queried_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["alert_id"], ["alerts.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    # ── action_logs ───────────────────────────────────────────────────────────
    op.create_table(
        "action_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("alert_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("playbook_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("action_name", sa.String(100), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("output_log", sa.Text(), nullable=True),
        sa.Column("executed_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column("executed_by", sa.String(100), server_default="system"),
        sa.CheckConstraint("status IN ('Pending','Success','Failure','Skipped')"),
        sa.ForeignKeyConstraint(["alert_id"], ["alerts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["playbook_id"], ["playbooks.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    # ── users ─────────────────────────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("username", sa.String(50), nullable=False, unique=True),
        sa.Column("email", sa.String(100), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("role", sa.String(20), nullable=False, server_default="Analyst"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.CheckConstraint("role IN ('Admin','Analyst','Auditor')"),
        sa.PrimaryKeyConstraint("id"),
    )

    # ── indexes ───────────────────────────────────────────────────────────────
    op.create_index("ix_alerts_status", "alerts", ["status"])
    op.create_index("ix_alerts_severity", "alerts", ["severity"])
    op.create_index("ix_alerts_created_at", "alerts", ["created_at"])
    op.create_index("ix_enrichment_results_alert_id", "enrichment_results", ["alert_id"])
    op.create_index("ix_enrichment_results_observable_value", "enrichment_results", ["observable_value"])


def downgrade() -> None:
    op.drop_table("action_logs")
    op.drop_table("enrichment_results")
    op.drop_table("playbooks")
    op.drop_table("users")
    op.drop_table("alerts")
