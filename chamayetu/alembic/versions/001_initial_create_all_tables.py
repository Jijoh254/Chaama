"""Initial migration - create all tables

Revision ID: 001_initial
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create enum types
    sa.Enum('admin', 'member', name='userrole').create(op.get_bind())
    sa.Enum('active', 'paused', 'completed', name='groupstatus').create(op.get_bind())
    sa.Enum('daily', 'weekly', 'monthly', name='groupfrequency').create(op.get_bind())
    sa.Enum('pending', 'active', 'completed', 'disbursed', name='cyclestatus').create(op.get_bind())
    sa.Enum('pending', 'confirmed', 'failed', name='contributionstatus').create(op.get_bind())
    sa.Enum('pending', 'processing', 'completed', 'failed', name='payoutstatus').create(op.get_bind())
    
    # Users table
    op.create_table('users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('full_name', sa.String(length=100), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('phone_number', sa.String(length=20), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('role', sa.Enum('admin', 'member', name='userrole'), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    op.create_index(op.f('ix_users_phone_number'), 'users', ['phone_number'], unique=True)
    
    # Groups table
    op.create_table('groups',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('contribution_amount', sa.Float(), nullable=False),
        sa.Column('frequency', sa.Enum('daily', 'weekly', 'monthly', name='groupfrequency'), nullable=False),
        sa.Column('max_members', sa.Integer(), nullable=False),
        sa.Column('invite_code', sa.String(length=8), nullable=False),
        sa.Column('status', sa.Enum('active', 'paused', 'completed', name='groupstatus'), nullable=False),
        sa.Column('created_by', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_groups_id'), 'groups', ['id'], unique=False)
    op.create_index(op.f('ix_groups_invite_code'), 'groups', ['invite_code'], unique=True)
    
    # Group members table (junction table)
    op.create_table('group_members',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('group_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('queue_position', sa.Integer(), nullable=False),
        sa.Column('has_received', sa.Boolean(), nullable=False),
        sa.Column('joined_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['group_id'], ['groups.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('group_id', 'queue_position', name='uq_group_queue'),
        sa.UniqueConstraint('group_id', 'user_id', name='uq_group_member')
    )
    op.create_index(op.f('ix_group_members_id'), 'group_members', ['id'], unique=False)
    
    # Cycles table
    op.create_table('cycles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('group_id', sa.Integer(), nullable=False),
        sa.Column('cycle_number', sa.Integer(), nullable=False),
        sa.Column('beneficiary_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.Enum('pending', 'active', 'completed', 'disbursed', name='cyclestatus'), nullable=False),
        sa.Column('start_date', sa.DateTime(), nullable=True),
        sa.Column('end_date', sa.DateTime(), nullable=True),
        sa.Column('total_collected', sa.Float(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['beneficiary_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['group_id'], ['groups.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_cycles_id'), 'cycles', ['id'], unique=False)
    
    # Contributions table
    op.create_table('contributions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('cycle_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('status', sa.Enum('pending', 'confirmed', 'failed', name='contributionstatus'), nullable=False),
        sa.Column('mpesa_checkout_id', sa.String(length=100), nullable=True),
        sa.Column('mpesa_receipt_number', sa.String(length=50), nullable=True),
        sa.Column('phone_number', sa.String(length=20), nullable=False),
        sa.Column('initiated_at', sa.DateTime(), nullable=False),
        sa.Column('confirmed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['cycle_id'], ['cycles.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_contributions_id'), 'contributions', ['id'], unique=False)
    
    # Payouts table
    op.create_table('payouts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('cycle_id', sa.Integer(), nullable=False),
        sa.Column('recipient_id', sa.Integer(), nullable=False),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('status', sa.Enum('pending', 'processing', 'completed', 'failed', name='payoutstatus'), nullable=False),
        sa.Column('mpesa_conversation_id', sa.String(length=100), nullable=True),
        sa.Column('mpesa_transaction_id', sa.String(length=50), nullable=True),
        sa.Column('phone_number', sa.String(length=20), nullable=False),
        sa.Column('initiated_at', sa.DateTime(), nullable=False),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('failure_reason', sa.String(length=255), nullable=True),
        sa.ForeignKeyConstraint(['cycle_id'], ['cycles.id'], ),
        sa.ForeignKeyConstraint(['recipient_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('cycle_id')
    )
    op.create_index(op.f('ix_payouts_id'), 'payouts', ['id'], unique=False)
    
    # Notifications table
    op.create_table('notifications',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('is_read', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_notifications_id'), 'notifications', ['id'], unique=False)


def downgrade() -> None:
    op.drop_table('notifications')
    op.drop_table('payouts')
    op.drop_table('contributions')
    op.drop_table('cycles')
    op.drop_table('group_members')
    op.drop_table('groups')
    op.drop_table('users')
    
    # Drop enum types
    sa.Enum(name='userrole').drop(op.get_bind())
    sa.Enum(name='groupstatus').drop(op.get_bind())
    sa.Enum(name='groupfrequency').drop(op.get_bind())
    sa.Enum(name='cyclestatus').drop(op.get_bind())
    sa.Enum(name='contributionstatus').drop(op.get_bind())
    sa.Enum(name='payoutstatus').drop(op.get_bind())
