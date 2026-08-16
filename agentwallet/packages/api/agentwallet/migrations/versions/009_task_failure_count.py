"""Add failure_count to tasks for worker retry cap.

Revision ID: 009_task_failure_count
Revises: 008_tasks
Create Date: 2026-08-16 00:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "009_task_failure_count"
down_revision: Union[str, None] = "008_tasks"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("tasks", sa.Column("failure_count", sa.Integer, server_default="0", nullable=False))


def downgrade() -> None:
    op.drop_column("tasks", "failure_count")
