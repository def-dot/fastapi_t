"""remove hashed_refresh_token from user

Revision ID: a2b3c4d5e6f7
Revises: 431f152c61c9
Create Date: 2026-04-16 12:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "a2b3c4d5e6f7"
down_revision: Union[str, Sequence[str], None] = "431f152c61c9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_column("users", "hashed_refresh_token")


def downgrade() -> None:
    op.add_column("users", sa.Column("hashed_refresh_token", sa.String(255), nullable=True))
