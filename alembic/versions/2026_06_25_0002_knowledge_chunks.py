"""knowledge chunks

Revision ID: 2026_06_25_0002
Revises: 2026_06_24_0001
Create Date: 2026-06-25
"""

import sqlalchemy as sa

from alembic import op

revision = "2026_06_25_0002"
down_revision = "2026_06_24_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.create_table(
        "knowledge_chunks",
        sa.Column("chunk_id", sa.String(length=160), primary_key=True),
        sa.Column("doc_id", sa.String(length=120), nullable=False),
        sa.Column("title", sa.String(length=240), nullable=False),
        sa.Column("source_path", sa.String(length=500), nullable=False),
        sa.Column("section", sa.String(length=240), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("ordinal", sa.Integer(), nullable=False),
        sa.Column("embedding", sa.JSON(), nullable=False),
        sa.Column("content_hash", sa.String(length=128), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_knowledge_chunks_doc_id", "knowledge_chunks", ["doc_id"])
    op.create_index("ix_knowledge_chunks_content_hash", "knowledge_chunks", ["content_hash"])


def downgrade() -> None:
    op.drop_index("ix_knowledge_chunks_content_hash", table_name="knowledge_chunks")
    op.drop_index("ix_knowledge_chunks_doc_id", table_name="knowledge_chunks")
    op.drop_table("knowledge_chunks")
