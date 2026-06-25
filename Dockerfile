FROM apache/superset
COPY requirements-local.txt /app/docker/requirements-local.txt
USER root
RUN chmod 777 -R .venv
USER superset
ENTRYPOINT ["./docker/docker-init.sh"]
