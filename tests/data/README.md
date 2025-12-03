# Data Tests for RLS Enforcement

This directory contains manual data tests that can be run interactively after migrations have been applied.

## Purpose

These tests are designed to:
- Test RLS behavior with actual data in the database
- Allow manual verification of RLS policies
- Provide examples of how to test RLS in your own code
- Support interactive debugging and exploration

## Usage

### 1. Start the containers

```bash
task test:dev
```

### 2. Apply migrations

```bash
docker-compose exec web uv run python manage.py migrate
```

### 3. Run tests interactively

Get a Django shell:

```bash
docker-compose exec web uv run python manage.py shell
```

Then import and run tests:

```python
# Import all test functions
from tests.data.test_rls_data import *

# Run individual tests
test_tenant_isolation()
test_uuid_tenant_isolation()
test_mixed_fields()
test_uuid_mixed_fields()
test_wildcard_all()

# Or run all tests at once
run_all_tests()

# Clean up when done
cleanup_test_data()
```

## Available Tests

### `manual_test_tenant_isolation()`
Tests RLS isolation with integer `tenant_id` fields. Creates records with different tenant IDs and verifies filtering works.

### `manual_test_uuid_tenant_isolation()`
Tests RLS isolation with UUID `tenant_id` fields. Verifies UUID-based RLS policies work correctly.

### `manual_test_mixed_fields()`
Tests RLS with multiple integer fields (`tenant_id` AND `user_id`). Verifies that records must match both conditions.

### `manual_test_uuid_mixed_fields()`
Tests RLS with multiple UUID fields. Verifies UUID-based multi-field RLS policies.

### `manual_test_wildcard_all()`
Tests that `RlsWildcard.ALL` bypasses RLS filtering, allowing access to all records.

### `cleanup_test_data()`
Removes all test data from the database.

### `run_all_tests()`
Runs all tests in sequence with proper error handling.

## Test Structure

Each test:
1. Sets up RLS settings and middleware
2. Creates test data with different RLS field values
3. Sets session variables via middleware
4. Queries the database and verifies results
5. Provides clear output about what's being tested

## Example Session

```python
>>> from tests.data.test_rls_data import *
>>> test_tenant_isolation()

=== Testing Tenant Isolation (Integer) ===
Created 4 records
With tenant_id=123: Found 2 records
✓ Tenant isolation works correctly
With tenant_id=456: Found 1 records
✓ Tenant filtering works correctly

>>> test_uuid_tenant_isolation()

=== Testing Tenant Isolation (UUID) ===
Created 3 UUID records
Tenant UUID 1: 550e8400-e29b-41d4-a716-446655440000
Tenant UUID 2: 6ba7b810-9dad-11d1-80b4-00c04fd430c8
With tenant_id=550e8400-e29b-41d4-a716-446655440000: Found 2 records
✓ UUID tenant isolation works correctly
```

