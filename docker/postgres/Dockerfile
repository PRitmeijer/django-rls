FROM postgres:17-bookworm

# Install envsubst from gettext
RUN apt-get update && \
    apt-get install -y --no-install-recommends gettext && \
    rm -rf /var/lib/apt/lists/*

# Place both the template and our custom entrypoint script into /docker-entrypoint-initdb.d
COPY db_init/ /db_init/
RUN ls -la /db_init/

# Make the script executable
RUN chmod +x /db_init/entrypoint.sh

# Use our custom entrypoint script (it will call the original afterwards)
ENTRYPOINT ["/db_init/entrypoint.sh"]

CMD ["postgres"]