FROM apache/superset

USER root

RUN . /app/.venv/bin/activate && uv pip install psycopg2-binary pyathena[pandas] redis

USER superset

COPY superset_config.py /app/pythonpath/

CMD ["/app/docker/entrypoints/run-server.sh"]
