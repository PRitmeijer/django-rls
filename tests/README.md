# Tests

## Structure

- `unit/` - Unit tests (settings, resolvers, middleware)
- `integration/` - Integration tests (RLS enforcement, e2e)
- `commands/` - Command tests (makemigrations, add_rls)
- `data/` - Manual interactive tests (run after migrations)

The test Django project is in `../testproject/` (separate from test code).

## Quick Start

```bash
# Run all tests
task test

# Manual testing (after migrations)
docker-compose exec web uv run python manage.py shell
>>> from tests.data.test_rls_data import *
>>> run_all_tests()
```
