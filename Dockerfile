FROM apache/superset

USER root

RUN . /app/.venv/bin/activate && uv pip install psycopg2-binary pyathena[pandas]

USER superset

CMD ["/app/docker/entrypoints/run-server.sh"]
