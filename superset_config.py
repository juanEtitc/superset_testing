import os

REDIS_URL = os.getenv("REDIS_URL")
if not REDIS_URL:
    raise ValueError("REDIS_URL must be set")

base_config = {
    "CACHE_TYPE": "RedisCache",
    "CACHE_DEFAULT_TIMEOUT": 86400,
    "CACHE_REDIS_URL": REDIS_URL,
}

CACHE_CONFIG = {**base_config, "CACHE_KEY_PREFIX": "superset_cache"}
DATA_CACHE_CONFIG = {**base_config, "CACHE_KEY_PREFIX": "superset_data"}
FILTER_STATE_CACHE_CONFIG = {**base_config, "CACHE_KEY_PREFIX": "superset_filters"}
EXPLORE_FORM_DATA_CACHE_CONFIG = {**base_config, "CACHE_KEY_PREFIX": "superset_explore"}

RESULTS_BACKEND = {
    "CACHE_TYPE": "RedisCache",
    "CACHE_REDIS_URL": f"{REDIS_URL}/2",
    "CACHE_DEFAULT_TIMEOUT": 86400,
    "CACHE_KEY_PREFIX": "superset_results",
}

FEATURE_FLAGS = {
    "DASHBOARD_RBAC": True,
    "ENABLE_TEMPLATE_PROCESSING": True,
    "DASHBOARD_VIRTUALIZATION": True,
    "FILTERBAR_CLOSED_BY_DEFAULT": True,
    "LISTVIEWS_DEFAULT_CARD_VIEW": True,
    "DASHBOARD_VIRTUALIZATION_DEFER_DATA": True,
}

# Transport puede ser "ws" (WebSocket) o "polling"
GLOBAL_ASYNC_QUERIES_TRANSPORT = "ws"
# Asegúrate de que este puerto sea el donde escucha el servidor de WebSocket
GLOBAL_ASYNC_QUERIES_WEBSOCKET_URL = "ws://localhost:8080/"
GLOBAL_ASYNC_QUERIES_JWT_SECRET = (
    "e16ced3ff0ba27807fbeaaada998cbcb252ec54a167c45bb851d1dfba428fffe"
)


GLOBAL_ASYNC_QUERIES_CACHE_BACKEND = {
    "CACHE_TYPE": "RedisCache",
    "CACHE_REDIS_URL": f"{REDIS_URL}/1",
    "CACHE_DEFAULT_TIMEOUT": 300,
}


class CeleryConfig(object):
    broker_url = f"{REDIS_URL}/0"
    imports = (
        "superset.sql_lab",
        "superset.tasks.scheduler",
    )
    result_backend = "redis://localhost:6379/0"
    worker_prefetch_multiplier = 10
    task_acks_late = True
    task_annotations = {
        "sql_lab.get_sql_results": {
            "rate_limit": "100/s",
        },
    }


CELERY_CONFIG = CeleryConfig
