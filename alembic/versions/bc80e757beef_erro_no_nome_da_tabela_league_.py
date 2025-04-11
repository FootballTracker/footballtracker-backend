"""Erro no nome da tabela league_classification

Revision ID: bc80e757beef
Revises: 14a71933dcac
Create Date: 2025-04-10 12:24:57.663095

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'bc80e757beef'
down_revision: Union[str, None] = '14a71933dcac'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
