"""Add AI priority fields to emergency events.

Revision ID: 002_priority_fields
Revises: 001_initial_schema
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "002_priority_fields"
down_revision: Union[str, None] = "001_initial_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("emergency_events", sa.Column("priority_code", sa.Integer(), nullable=True))
    op.add_column("emergency_events", sa.Column("priority_label", sa.String(length=20), nullable=True))


def downgrade() -> None:
    op.drop_column("emergency_events", "priority_label")
    op.drop_column("emergency_events", "priority_code")