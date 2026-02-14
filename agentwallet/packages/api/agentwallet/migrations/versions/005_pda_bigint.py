"""Widen PDA wallet limit columns from Integer to BigInteger (u64 compat).

Revision ID: 005_pda_bigint
Revises: 004_pda_wallets
Create Date: 2026-02-14 00:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "005_pda_bigint"
down_revision: Union[str, None] = "004_pda_wallets"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column("pda_wallets", "spending_limit_per_tx", type_=sa.BigInteger, existing_nullable=False)
    op.alter_column("pda_wallets", "daily_limit", type_=sa.BigInteger, existing_nullable=False)


def downgrade() -> None:
    op.alter_column("pda_wallets", "spending_limit_per_tx", type_=sa.Integer, existing_nullable=False)
    op.alter_column("pda_wallets", "daily_limit", type_=sa.Integer, existing_nullable=False)
