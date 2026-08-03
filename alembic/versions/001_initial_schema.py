"""Initial PostgreSQL schema setup

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-08-02

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. nodes table
    op.create_table(
        'nodes',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('node_id', sa.String(length=100), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='ONLINE'),
        sa.Column('battery', sa.Float(), nullable=False),
        sa.Column('last_seen', sa.DateTime(timezone=True), nullable=False),
        sa.Column('latitude', sa.Float(), nullable=True),
        sa.Column('longitude', sa.Float(), nullable=True),
        sa.Column('rssi', sa.Integer(), nullable=True),
        sa.Column('snr', sa.Float(), nullable=True),
        sa.Column('current_emergency', sa.String(length=100), nullable=True),
        sa.Column('packet_type', sa.String(length=50), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('node_id')
    )
    op.create_index('ix_nodes_node_id', 'nodes', ['node_id'], unique=True)

    # 2. sensor_logs table
    op.create_table(
        'sensor_logs',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('emergency_id', sa.String(length=100), nullable=False),
        sa.Column('node_id', sa.String(length=100), nullable=False),
        sa.Column('sequence_number', sa.Integer(), nullable=False),
        sa.Column('packet_type', sa.String(length=50), nullable=True),
        sa.Column('latitude', sa.Float(), nullable=False),
        sa.Column('longitude', sa.Float(), nullable=False),
        sa.Column('heart_rate', sa.Integer(), nullable=True),
        sa.Column('spo2', sa.Float(), nullable=True),
        sa.Column('temperature', sa.Float(), nullable=True),
        sa.Column('fall_detected', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('sos', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('battery', sa.Float(), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['node_id'], ['nodes.node_id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_sensor_logs_emergency_id', 'sensor_logs', ['emergency_id'], unique=False)
    op.create_index('ix_sensor_logs_node_id', 'sensor_logs', ['node_id'], unique=False)

    # 3. packet_logs table (Requirement 3: includes delivery_confirmed & delivery_confirmation_time)
    op.create_table(
        'packet_logs',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('packet_id', sa.String(length=100), nullable=False),
        sa.Column('emergency_id', sa.String(length=100), nullable=False),
        sa.Column('sequence_number', sa.Integer(), nullable=False),
        sa.Column('source_node_id', sa.String(length=100), nullable=False),
        sa.Column('previous_hop_id', sa.String(length=100), nullable=True),
        sa.Column('destination_id', sa.String(length=100), nullable=True),
        sa.Column('packet_type', sa.String(length=50), nullable=False),
        sa.Column('ack_status', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('retry_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('rssi', sa.Integer(), nullable=True),
        sa.Column('snr', sa.Float(), nullable=True),
        sa.Column('delivery_confirmed', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('delivery_confirmation_time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('packet_id')
    )
    op.create_index('ix_packet_logs_packet_id', 'packet_logs', ['packet_id'], unique=True)
    op.create_index('ix_packet_logs_emergency_id', 'packet_logs', ['emergency_id'], unique=False)

    # 4. emergency_events table
    op.create_table(
        'emergency_events',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('emergency_id', sa.String(length=100), nullable=False),
        sa.Column('node_id', sa.String(length=100), nullable=False),
        sa.Column('event_type', sa.String(length=50), nullable=False),
        sa.Column('latitude', sa.Float(), nullable=False),
        sa.Column('longitude', sa.Float(), nullable=False),
        sa.Column('last_sequence_number', sa.Integer(), nullable=False),
        sa.Column('resolved', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('remarks', sa.Text(), nullable=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['node_id'], ['nodes.node_id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('emergency_id')
    )
    op.create_index('ix_emergency_events_emergency_id', 'emergency_events', ['emergency_id'], unique=True)
    op.create_index('ix_emergency_events_node_id', 'emergency_events', ['node_id'], unique=False)

    # 5. outbound_messages table (Requirement 4)
    op.create_table(
        'outbound_messages',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('message_id', sa.String(length=100), nullable=False),
        sa.Column('destination_node', sa.String(length=100), nullable=False),
        sa.Column('message_type', sa.String(length=50), nullable=False),
        sa.Column('payload', sa.JSON(), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='QUEUED'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('sent_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('ack_received', sa.Boolean(), nullable=False, server_default='false'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('message_id')
    )
    op.create_index('ix_outbound_messages_message_id', 'outbound_messages', ['message_id'], unique=True)
    op.create_index('ix_outbound_messages_destination_node', 'outbound_messages', ['destination_node'], unique=False)


def downgrade() -> None:
    op.drop_table('outbound_messages')
    op.drop_table('emergency_events')
    op.drop_table('packet_logs')
    op.drop_table('sensor_logs')
    op.drop_table('nodes')
