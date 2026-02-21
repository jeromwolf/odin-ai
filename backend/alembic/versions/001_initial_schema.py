"""Initial schema - baseline from existing SQL files

Revision ID: 001_initial
Revises:
Create Date: 2025-02-21
"""
from alembic import op

revision = '001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Initial schema baseline.

    This migration represents the existing database schema.
    All tables should already exist from sql/init.sql.
    This migration exists as a starting point for future changes.

    To bootstrap a new database:
      1. Run sql/init.sql first
      2. Then: alembic stamp 001_initial

    To apply to existing database:
      alembic stamp 001_initial
    """
    # Tables already exist from init.sql
    # This is a baseline migration - no operations needed
    # Future migrations will use op.add_column(), op.create_table(), etc.
    pass


def downgrade() -> None:
    """Cannot downgrade initial schema - would require dropping all tables."""
    raise RuntimeError("Cannot downgrade past initial schema. Restore from backup instead.")
