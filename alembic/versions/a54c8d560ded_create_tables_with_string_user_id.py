"""create_tables_with_string_user_id

Revision ID: a54c8d560ded
Revises: e4188e7ff2c8
Create Date: 2025-06-08 00:00:35.854511

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a54c8d560ded'
down_revision: Union[str, None] = 'e4188e7ff2c8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Drop the foreign key constraint first
    op.drop_constraint('chat_sessions_litefarm_user_id_fkey', 'chat_sessions', type_='foreignkey')
    
    # Change the column types
    op.alter_column('users', 'litefarm_user_id',
               existing_type=sa.UUID(),
               type_=sa.String(),
               existing_nullable=False)
    
    op.alter_column('chat_sessions', 'litefarm_user_id',
               existing_type=sa.UUID(),
               type_=sa.String(),
               existing_nullable=True)
    
    # Recreate the foreign key constraint
    op.create_foreign_key('chat_sessions_litefarm_user_id_fkey', 'chat_sessions', 'users', 
                         ['litefarm_user_id'], ['litefarm_user_id'], ondelete='CASCADE')


def downgrade() -> None:
    """Downgrade schema."""
    # Drop the foreign key constraint first
    op.drop_constraint('chat_sessions_litefarm_user_id_fkey', 'chat_sessions', type_='foreignkey')
    
    # Change the column types back
    op.alter_column('chat_sessions', 'litefarm_user_id',
               existing_type=sa.String(),
               type_=sa.UUID(),
               existing_nullable=True)
    
    op.alter_column('users', 'litefarm_user_id',
               existing_type=sa.String(),
               type_=sa.UUID(),
               existing_nullable=False)
    
    # Recreate the foreign key constraint
    op.create_foreign_key('chat_sessions_litefarm_user_id_fkey', 'chat_sessions', 'users', 
                         ['litefarm_user_id'], ['litefarm_user_id'], ondelete='CASCADE')
