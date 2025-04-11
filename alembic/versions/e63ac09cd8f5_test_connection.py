"""test_connection

Revision ID: e63ac09cd8f5
Revises: bc80e757beef
Create Date: 2025-04-11 17:24:53.070223

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e63ac09cd8f5'
down_revision: Union[str, None] = 'bc80e757beef'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
