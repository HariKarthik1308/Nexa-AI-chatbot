"""create initial tables

Revision ID: 001_initial_tables
Revises: 
Create Date: 2026-11-16 18:30:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '001_initial_tables'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. users table
    op.create_table(
        'users',
        sa.Column('id', sa.String(length=36), primary_key=True, nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_users_id', 'users', ['id'])
    op.create_index('ix_users_email', 'users', ['email'], unique=True)

    # 2. conversations table
    op.create_table(
        'conversations',
        sa.Column('id', sa.String(length=36), primary_key=True, nullable=False),
        sa.Column('user_id', sa.String(length=36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False, server_default='New Conversation'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_conversations_id', 'conversations', ['id'])
    op.create_index('ix_conversations_user_id', 'conversations', ['user_id'])
    op.create_index('ix_conversations_user_created', 'conversations', ['user_id', 'created_at'])

    # 3. messages table
    op.create_table(
        'messages',
        sa.Column('id', sa.String(length=36), primary_key=True, nullable=False),
        sa.Column('conversation_id', sa.String(length=36), sa.ForeignKey('conversations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('role', sa.String(length=32), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='complete'),
        sa.Column('model_provider', sa.String(length=64), nullable=True),
        sa.Column('model_name', sa.String(length=128), nullable=True),
        sa.Column('input_tokens', sa.Integer(), nullable=True),
        sa.Column('output_tokens', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_messages_id', 'messages', ['id'])
    op.create_index('ix_messages_conversation_id', 'messages', ['conversation_id'])
    op.create_index('ix_messages_conv_created', 'messages', ['conversation_id', 'created_at'])

    # 4. usage_records table
    op.create_table(
        'usage_records',
        sa.Column('id', sa.String(length=36), primary_key=True, nullable=False),
        sa.Column('user_id', sa.String(length=36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('provider', sa.String(length=64), nullable=False),
        sa.Column('model', sa.String(length=128), nullable=False),
        sa.Column('input_tokens', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('output_tokens', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('estimated_cost', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_usage_records_id', 'usage_records', ['id'])
    op.create_index('ix_usage_records_user_id', 'usage_records', ['user_id'])
    op.create_index('ix_usage_user_created', 'usage_records', ['user_id', 'created_at'])

    # 5. message_feedback table
    op.create_table(
        'message_feedback',
        sa.Column('id', sa.String(length=36), primary_key=True, nullable=False),
        sa.Column('message_id', sa.String(length=36), sa.ForeignKey('messages.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', sa.String(length=36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('rating', sa.String(length=16), nullable=False),
        sa.Column('comment', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_message_feedback_id', 'message_feedback', ['id'])
    op.create_index('ix_message_feedback_message_id', 'message_feedback', ['message_id'])
    op.create_index('ix_message_feedback_user_id', 'message_feedback', ['user_id'])


def downgrade() -> None:
    op.drop_table('message_feedback')
    op.drop_table('usage_records')
    op.drop_table('messages')
    op.drop_table('conversations')
    op.drop_table('users')
