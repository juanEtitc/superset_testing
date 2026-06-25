FROM apache/superset

USER root

RUN . /app/.venv/bin/activate && uv pip install psycopg2-binary pyathena[pandas] redis

USER superset

COPY config.py /app/superset/config.py

CMD ["/app/docker/entrypoints/run-server.sh"]
