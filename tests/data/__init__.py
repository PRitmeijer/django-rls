"""
Data tests for RLS enforcement.

These tests are designed to be run manually after migrations have been applied.
They test RLS behavior with actual data in the database.

Usage:
    # After running migrations
    docker-compose exec web uv run python manage.py shell
    >>> from tests.data.test_rls_data import *
    >>> test_tenant_isolation()
"""

