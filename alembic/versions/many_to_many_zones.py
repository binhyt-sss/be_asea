"""Change user-zone relationship to many-to-many

Revision ID: many_to_many_zones
Revises: initial
Create Date: 2025-11-27

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'many_to_many_zones'
down_revision: Union[str, None] = '37b75d3e0369'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Upgrade: Change from one-to-many to many-to-many relationship
    
    Steps:
    1. Create user_zone_association table
    2. Migrate existing data (user.zone_id -> association table)
    3. Drop user.zone_id column
    4. Drop old index
    """
    # Create association table
    op.create_table(
        'user_zone_association',
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('zone_id', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['zone_id'], ['working_zone.zone_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('user_id', 'zone_id')
    )
    
    # Migrate existing data
    op.execute("""
        INSERT INTO user_zone_association (user_id, zone_id, created_at)
        SELECT id, zone_id, NOW()
        FROM "user"
        WHERE zone_id IS NOT NULL
    """)
    
    # Drop old index
    op.drop_index('idx_user_zone_id', table_name='user')
    
    # Drop old foreign key and column
    op.drop_constraint('user_zone_id_fkey', 'user', type_='foreignkey')
    op.drop_column('user', 'zone_id')


def downgrade() -> None:
    """
    Downgrade: Change back from many-to-many to one-to-many
    
    Warning: This will only keep the FIRST zone for each user!
    """
    # Add zone_id column back
    op.add_column('user', sa.Column('zone_id', sa.String(), nullable=True))
    
    # Add foreign key
    op.create_foreign_key('user_zone_id_fkey', 'user', 'working_zone', ['zone_id'], ['zone_id'], ondelete='SET NULL')
    
    # Create index
    op.create_index('idx_user_zone_id', 'user', ['zone_id'])
    
    # Migrate data back (keep only FIRST zone per user)
    op.execute("""
        UPDATE "user" u
        SET zone_id = (
            SELECT zone_id
            FROM user_zone_association uza
            WHERE uza.user_id = u.id
            ORDER BY uza.created_at
            LIMIT 1
        )
    """)
    
    # Drop association table
    op.drop_table('user_zone_association')
