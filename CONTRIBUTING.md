<!-- shameless copy from graphene-django CONTRIBUTING file -->

# Contributing

Thanks for helping improve Django GraphQL Auth!

All kinds of contributions are welcome:

- Bug fixes
- Documentation improvements
- New features
- Refactoring
- Fix some typo
- Write more tests

## Getting started

If you have a specific contribution in mind, be sure to check the [issues](https://github.com/pritmeijer/django-rls/issues) and [projects](https://github.com/pritmeijer/django-rls/projects) in progress - someone could already be working on something similar and you can help out.

## Project setup

After cloning this repo, ensure dependencies are installed by running:

```bash
make dev-setup
```

and

```bash
pip install tox
```

## Running tests

All tests use PostgreSQL by default since RLS is a PostgreSQL-only feature. The project includes automated PostgreSQL testing via Docker Compose.

**Quick start:**

```bash
# Run all tests (automatically starts/stops PostgreSQL)
task test

# Or manually:
docker-compose up -d postgres
pytest
docker-compose down
```

**Available commands:**

```bash
# Run tests (starts PostgreSQL, runs tests, stops PostgreSQL)
task test

# Run tests but keep PostgreSQL container running
task test:keep-running

# Start PostgreSQL container manually
task postgresql:up

# Stop PostgreSQL container manually
task postgresql:down
```

**Environment variables:**

You can override PostgreSQL connection settings via environment variables:

```bash
POSTGRES_HOST=localhost POSTGRES_PORT=5432 \
POSTGRES_DB=testdb POSTGRES_USER=testuser POSTGRES_PASSWORD=testpass \
pytest
```

For live testing on a django project, you can use the testproject.
 Create a different virtualenv, install the dependencies again and run:

```bash
cd testproject
make install-local v=<CURRENT VERSION IN django_rls.__init__>
```

## Opening Pull Requests

Please fork the project and open a pull request against the main branch.

This will trigger a series of tests and lint checks.

We advise that you format and run lint locally before doing this to save time:

```bash
make format
make lint
```

## Documentation

The documentation is generated using the excellent [MkDocs](https://www.mkdocs.org/) with [material theme](https://squidfunk.github.io/mkdocs-material/).

The documentation dependencies are installed by running:

```bash
pip install -r docs/requirements.txt
```

Then to produce a HTML version of the documentation, for live editing:

```bash
make serve
```

It will run the `docs/pre_build.py` script before building the docs.