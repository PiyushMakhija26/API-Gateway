"""Initial schema: roles, users, api_keys, providers, routes

Revision ID: 0001
Revises:
Create Date: 2026-10-24
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _base_columns():
    return [
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    ]


def upgrade() -> None:
    op.create_table(
        "roles",
        *_base_columns(),
        sa.Column("name", sa.String(), nullable=False, unique=True),
        sa.Column("description", sa.String(), nullable=True),
    )
    op.create_table(
        "users",
        *_base_columns(),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("hashed_password", sa.String(), nullable=False),
        sa.Column("role_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("roles.id"), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_table(
        "api_keys",
        *_base_columns(),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("key_hash", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_api_keys_key_hash", "api_keys", ["key_hash"], unique=True)
    op.create_table(
        "providers",
        *_base_columns(),
        sa.Column("name", sa.String(), nullable=False, unique=True),
        sa.Column("base_url", sa.String(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("priority", sa.Integer(), nullable=False),
    )
    op.create_table(
        "routes",
        *_base_columns(),
        sa.Column("path_prefix", sa.String(), nullable=False),
        sa.Column("provider_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("providers.id"), nullable=False),
        sa.Column("require_auth", sa.Boolean(), nullable=False),
        sa.Column("rate_limit_rpm", sa.Integer(), nullable=False),
        sa.Column("timeout_seconds", sa.Integer(), nullable=False),
        sa.Column("retry_count", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
    )
    op.create_index("ix_routes_path_prefix", "routes", ["path_prefix"], unique=True)


def downgrade() -> None:
    op.drop_table("routes")
    op.drop_table("providers")
    op.drop_table("api_keys")
    op.drop_table("users")
    op.drop_table("roles")
