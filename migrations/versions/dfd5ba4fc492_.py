"""empty message

Revision ID: dfd5ba4fc492
Revises: c51cbb8c1f25
Create Date: 2020-04-23 13:22:28.773244

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'dfd5ba4fc492'
down_revision = 'c51cbb8c1f25'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_unique_constraint(None, 'comments', ['id'])
    op.create_unique_constraint(None, 'event_comments', ['id'])
    op.create_unique_constraint(None, 'event_posts', ['id'])
    op.create_unique_constraint(None, 'posts', ['id'])
    op.add_column('users', sa.Column('title', sa.String(length=80), nullable=True))
    op.create_unique_constraint(None, 'users', ['id'])
    op.drop_column('users', 'friend_id')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('users', sa.Column('friend_id', sa.INTEGER(), nullable=True))
    op.drop_constraint(None, 'users', type_='unique')
    op.drop_column('users', 'title')
    op.drop_constraint(None, 'posts', type_='unique')
    op.drop_constraint(None, 'event_posts', type_='unique')
    op.drop_constraint(None, 'event_comments', type_='unique')
    op.drop_constraint(None, 'comments', type_='unique')
    # ### end Alembic commands ###
