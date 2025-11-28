"""Sync with existing violation_logs table

Revision ID: 0994e45dd12f
Revises: many_to_many_zones
Create Date: 2025-11-28 15:14:54.878937

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0994e45dd12f'
down_revision: Union[str, Sequence[str], None] = 'many_to_many_zones'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # This migration acknowledges that violation_logs table already exists
    # No changes needed - just syncing Alembic state with reality
    pass


def downgrade() -> None:
    """Downgrade schema."""
    # No changes were made, so no downgrade needed
    pass
