"""Added next_plan for user

Revision ID: c3cd674b9bcd
Revises: 21226bc711ac
Create Date: 2024-11-07 12:45:51.159960

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c3cd674b9bcd'
down_revision = '21226bc711ac'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('next_plans',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('data_limit', sa.BigInteger(), nullable=False),
    sa.Column('expire', sa.Integer(), nullable=True),
    sa.Column('add_remaining_traffic', sa.Boolean(), server_default='0', nullable=False),
    sa.Column('fire_on_either', sa.Boolean(), server_default='0', nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('next_plans')
    # ### end Alembic commands ###
