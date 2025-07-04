"""Initial chat history table

Revision ID: 290eb81a6e68
Revises: 
Create Date: 2025-06-14 07:23:32.027358

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '290eb81a6e68'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('chat_history',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('session_id', sa.String(length=255), nullable=False),
    sa.Column('user_message', sa.Text(), nullable=False),
    sa.Column('bot_response', sa.Text(), nullable=False),
    sa.Column('timestamp', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('chat_history')
    # ### end Alembic commands ###
