"""add priority to proxy hosts

Revision ID: 9765715643a1
Revises: 68edca039166
Create Date: 2025-02-24 22:29:49.063544

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "9765715643a1"
down_revision = "68edca039166"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column("hosts", sa.Column("priority", sa.Integer(), nullable=True))
    op.execute("UPDATE hosts SET priority = id")

    # Make priority column non-nullable with default
    with op.batch_alter_table("hosts") as batch_op:
        batch_op.alter_column("priority", existing_type=sa.Integer(), nullable=False)

        batch_op.alter_column("inbound_tag", existing_type=sa.VARCHAR(length=256), nullable=True)

    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("hosts") as batch_op:
        batch_op.alter_column("inbound_tag", existing_type=sa.VARCHAR(length=256), nullable=False)
    op.drop_column("hosts", "priority")
    # ### end Alembic commands ###
