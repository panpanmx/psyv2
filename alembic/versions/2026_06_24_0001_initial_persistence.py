"""initial persistence

Revision ID: 2026_06_24_0001
Revises:
Create Date: 2026-06-24
"""


import sqlalchemy as sa

from alembic import op

revision = "2026_06_24_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("nickname", sa.String(length=120), nullable=False),
        sa.Column("age_group", sa.String(length=40), nullable=False),
        sa.Column("school_stage", sa.String(length=120), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "conversations",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("user_id", sa.String(length=64), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_conversations_user_id", "conversations", ["user_id"])
    op.create_table(
        "messages",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column(
            "conversation_id",
            sa.String(length=64),
            sa.ForeignKey("conversations.id"),
            nullable=False,
        ),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("content_hash", sa.String(length=128), nullable=False),
        sa.Column("risk_snapshot", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_messages_conversation_id", "messages", ["conversation_id"])
    op.create_index("ix_messages_content_hash", "messages", ["content_hash"])
    op.create_table(
        "user_profiles",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("user_id", sa.String(length=64), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("profile_json", sa.JSON(), nullable=False),
        sa.Column("latest_summary", sa.Text(), nullable=False),
        sa.Column("risk_trend_json", sa.JSON(), nullable=False),
        sa.Column("updated_by_message_id", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_user_profiles_user_id", "user_profiles", ["user_id"], unique=True)
    op.create_table(
        "assessments",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("user_id", sa.String(length=64), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("conversation_id", sa.String(length=64), nullable=True),
        sa.Column("scale_type", sa.String(length=40), nullable=False),
        sa.Column("answers", sa.JSON(), nullable=False),
        sa.Column("score", sa.Integer(), nullable=True),
        sa.Column("severity", sa.String(length=80), nullable=False),
        sa.Column("interpretation", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_assessments_user_id", "assessments", ["user_id"])
    op.create_index("ix_assessments_conversation_id", "assessments", ["conversation_id"])
    op.create_index("ix_assessments_scale_type", "assessments", ["scale_type"])
    op.create_table(
        "risk_assessments",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("user_id", sa.String(length=64), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("conversation_id", sa.String(length=64), nullable=True),
        sa.Column("message_id", sa.String(length=64), nullable=True),
        sa.Column("depression_risk", sa.String(length=40), nullable=False),
        sa.Column("anxiety_risk", sa.String(length=40), nullable=False),
        sa.Column("sleep_risk", sa.String(length=40), nullable=False),
        sa.Column("crisis_level", sa.String(length=10), nullable=False),
        sa.Column("function_impairment_level", sa.String(length=40), nullable=False),
        sa.Column("evidence", sa.JSON(), nullable=False),
        sa.Column("recommended_next_step", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_risk_assessments_user_id", "risk_assessments", ["user_id"])
    op.create_index("ix_risk_assessments_conversation_id", "risk_assessments", ["conversation_id"])
    op.create_index("ix_risk_assessments_message_id", "risk_assessments", ["message_id"])
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("request_id", sa.String(length=120), nullable=False),
        sa.Column("user_id", sa.String(length=64), nullable=True),
        sa.Column("conversation_id", sa.String(length=64), nullable=True),
        sa.Column("event_type", sa.String(length=120), nullable=False),
        sa.Column("event_payload", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_audit_logs_request_id", "audit_logs", ["request_id"])
    op.create_index("ix_audit_logs_user_id", "audit_logs", ["user_id"])
    op.create_index("ix_audit_logs_conversation_id", "audit_logs", ["conversation_id"])
    op.create_index("ix_audit_logs_event_type", "audit_logs", ["event_type"])


def downgrade() -> None:
    op.drop_index("ix_audit_logs_event_type", table_name="audit_logs")
    op.drop_index("ix_audit_logs_conversation_id", table_name="audit_logs")
    op.drop_index("ix_audit_logs_user_id", table_name="audit_logs")
    op.drop_index("ix_audit_logs_request_id", table_name="audit_logs")
    op.drop_table("audit_logs")
    op.drop_index("ix_risk_assessments_message_id", table_name="risk_assessments")
    op.drop_index("ix_risk_assessments_conversation_id", table_name="risk_assessments")
    op.drop_index("ix_risk_assessments_user_id", table_name="risk_assessments")
    op.drop_table("risk_assessments")
    op.drop_index("ix_assessments_scale_type", table_name="assessments")
    op.drop_index("ix_assessments_conversation_id", table_name="assessments")
    op.drop_index("ix_assessments_user_id", table_name="assessments")
    op.drop_table("assessments")
    op.drop_index("ix_user_profiles_user_id", table_name="user_profiles")
    op.drop_table("user_profiles")
    op.drop_index("ix_messages_content_hash", table_name="messages")
    op.drop_index("ix_messages_conversation_id", table_name="messages")
    op.drop_table("messages")
    op.drop_index("ix_conversations_user_id", table_name="conversations")
    op.drop_table("conversations")
    op.drop_table("users")
