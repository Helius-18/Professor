"""Add api_method column to tools table

Revision ID: 9ee961c70cfd
Revises: 342ed722c0d2
Create Date: 2026-02-08 17:54:28.098881

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '9ee961c70cfd'
down_revision: Union[str, Sequence[str], None] = '342ed722c0d2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add api_method column to tools table
    op.add_column('tools', sa.Column('api_method', sa.Enum('GET', 'POST', 'PUT', 'DELETE', name='apimethod'), nullable=False, server_default='GET'))


def downgrade() -> None:
    """Downgrade schema."""
    # Remove api_method column from tools table
    op.drop_column('tools', 'api_method')
