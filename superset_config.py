import os

REDIS_URL = os.getenv("REDIS_URL")

if not REDIS_URL:
    raise ValueError("REDIS_URL must be set")

base_config = {
    "CACHE_TYPE": "RedisCache",
    "CACHE_DEFAULT_TIMEOUT": 86400,
}

FILTER_STATE_CACHE_CONFIG = {
    **base_config,
    "CACHE_KEY_PREFIX": "superset_filter_cache",
    "CACHE_REDIS_URL": REDIS_URL + "/0",
}

EXPLORE_FORM_DATA_CACHE_CONFIG = {
    **base_config,
    "CACHE_KEY_PREFIX": "superset_explore_form_cache",  # fixed: was duplicate
    "CACHE_REDIS_URL": REDIS_URL + "/0",
}

CACHE_CONFIG = {
    **base_config,
    "CACHE_KEY_PREFIX": "superset_cache_config",
    "CACHE_REDIS_URL": REDIS_URL + "/0",
}

DATA_CACHE_CONFIG = {
    **base_config,
    "CACHE_KEY_PREFIX": "superset_data_cache",
    "CACHE_REDIS_URL": REDIS_URL + "/0",
}

FEATURE_FLAGS = {
    "DASHBOARD_RBAC": True,
    "ENABLE_TEMPLATE_PROCESSING": True,
    "GLOBAL_ASYNC_QUERIES": True,
    "GLOBAL_ASYNC_DASHBOARD_RENDER": True,
    "SQLLAB_BACKEND_PERSISTENCE": True,
}

# GAQ settings — transport can be "ws" (WebSocket) or "polling"
GLOBAL_ASYNC_QUERIES_TRANSPORT = "ws"  # or "polling" if not using the WS server
GLOBAL_ASYNC_QUERIES_WEBSOCKET_URL = "ws://localhost:8080/"  # adjust to your WS server

GLOBAL_ASYNC_QUERIES_JWT_SECRET = "e16ced3ff0ba27807fbeaaada998cbcb252ec54a167c45bb851d1dfba428fffe"

# Use CACHE_REDIS_URL to stay consistent with your REDIS_URL env var
GLOBAL_ASYNC_QUERIES_CACHE_BACKEND = {
    "CACHE_TYPE": "RedisCache",
    "CACHE_REDIS_URL": REDIS_URL + "/1",  # use a separate DB index from other caches
    "CACHE_DEFAULT_TIMEOUT": 300,
}

from flask_caching.backends.rediscache import RedisCache
RESULTS_BACKEND = RedisCache(
    host=REDIS_URL.split("//")[-1].split(":")[0],
    port=6379,
    key_prefix="superset_results",
)


class CeleryConfig(object):
    broker_url = REDIS_URL + "/0"
    imports = (
        "superset.sql_lab",
        "superset.tasks.scheduler",
        "superset.tasks.thumbnails",
        "superset.tasks.cache",
        "superset.tasks.async_queries",
    )
    result_backend = REDIS_URL + "/0"
    worker_prefetch_multiplier = 10
    task_acks_late = True
    task_annotations = {
        "sql_lab.get_sql_results": {
            "rate_limit": "100/s",
        },
    }


CELERY_CONFIG = CeleryConfig
