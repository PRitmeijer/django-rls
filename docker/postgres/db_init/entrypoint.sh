#!/bin/bash
set -e

echo "Running envsubst on init_roles.sql.template..."
if [ -f /db_init/init_roles.sql.template ]; then
    # Explicitly list all variables to substitute
    envsubst '$POSTGRES_MIGRATION_USER $POSTGRES_MIGRATION_PASSWORD $POSTGRES_RUNTIME_USER $POSTGRES_RUNTIME_PASSWORD $POSTGRES_USER $POSTGRES_PASSWORD' \
        < /db_init/init_roles.sql.template > /docker-entrypoint-initdb.d/init_roles.sql
    echo "Generated init_roles.sql"
    echo "Substituted variables:"
    echo "  POSTGRES_MIGRATION_USER=${POSTGRES_MIGRATION_USER:-not set}"
    echo "  POSTGRES_RUNTIME_USER=${POSTGRES_RUNTIME_USER:-not set}"
    echo "  POSTGRES_USER=${POSTGRES_USER:-not set}"
fi

# Now execute the official entrypoint script
exec /usr/local/bin/docker-entrypoint.sh "$@"