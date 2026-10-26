"""drop_academic_tables_finalize_media_schema

Revision ID: c8e19f3b7d12
Revises: 6662fb76ebf3
Create Date: 2026-10-26 14:50:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c8e19f3b7d12'
down_revision: Union[str, None] = '6662fb76ebf3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Safely drop obsolete academic tables in dependency order
    op.drop_table('search_analytics_events')
    op.drop_table('source_records')
    op.drop_table('publications')
    op.drop_table('researchers')
    op.drop_table('institutions')


def downgrade() -> None:
    # Recreate academic tables if downgrade is requested
    op.create_table('institutions',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('normalized_name', sa.String(length=255), nullable=False),
        sa.Column('country', sa.String(length=100), nullable=True),
        sa.Column('city', sa.String(length=100), nullable=True),
        sa.Column('is_synthetic', sa.Boolean(), nullable=False),
        sa.Column('source_record_id', sa.String(length=64), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_table('researchers',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=False),
        sa.Column('institution_id', sa.String(length=64), nullable=True),
        sa.Column('country', sa.String(length=100), nullable=True),
        sa.Column('department', sa.String(length=255), nullable=True),
        sa.Column('research_interests', sa.JSON(), nullable=True),
        sa.Column('is_synthetic', sa.Boolean(), nullable=False),
        sa.Column('source_record_id', sa.String(length=64), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['institution_id'], ['institutions.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_table('publications',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('title', sa.String(length=500), nullable=False),
        sa.Column('authors', sa.JSON(), nullable=False),
        sa.Column('publication_year', sa.Integer(), nullable=True),
        sa.Column('venue', sa.String(length=255), nullable=True),
        sa.Column('keywords', sa.JSON(), nullable=True),
        sa.Column('is_synthetic', sa.Boolean(), nullable=False),
        sa.Column('source_record_id', sa.String(length=64), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_table('source_records',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('entity_type', sa.String(length=50), nullable=False),
        sa.Column('source_name', sa.String(length=100), nullable=False),
        sa.Column('raw_payload', sa.JSON(), nullable=False),
        sa.Column('payload_hash', sa.String(length=64), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_table('search_analytics_events',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('query_text', sa.String(length=500), nullable=False),
        sa.Column('normalized_query', sa.String(length=500), nullable=False),
        sa.Column('filters_applied', sa.JSON(), nullable=True),
        sa.Column('result_count', sa.Integer(), nullable=False),
        sa.Column('execution_duration_ms', sa.Float(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
