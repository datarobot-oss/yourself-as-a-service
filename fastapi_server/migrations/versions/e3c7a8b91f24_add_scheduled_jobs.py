"""add_scheduled_jobs

Revision ID: e3c7a8b91f24
Revises: 64fc4ee522e6
Create Date: 2026-04-04 00:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlmodel.sql.sqltypes import AutoString

# revision identifiers, used by Alembic.
revision: str = "e3c7a8b91f24"
down_revision: Union[str, Sequence[str], None] = "64fc4ee522e6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema"""
    op.create_table(
        "scheduledjob",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", AutoString(), nullable=False),
        sa.Column("cron", AutoString(), nullable=False),
        sa.Column("prompt", AutoString(), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("user_uuid", sa.Uuid(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_uuid"], ["user.uuid"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name="pk_scheduledjob"),
        sa.UniqueConstraint("id", name="uq_scheduledjob_id"),
    )
    op.create_index(
        op.f("ix_scheduledjob_user_uuid"), "scheduledjob", ["user_uuid"], unique=False
    )


def downgrade() -> None:
    """Downgrade schema"""
    op.drop_index(op.f("ix_scheduledjob_user_uuid"), table_name="scheduledjob")
    op.drop_table("scheduledjob")
