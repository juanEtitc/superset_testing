import os

REDIS_URL = os.getenv("REDIS_URL")

if not REDIS_URL:
  raise ValueError("redis must be set")

base_config = {
    'CACHE_TYPE': 'RedisCache',
    'CACHE_DEFAULT_TIMEOUT': 86400,
}

FILTER_STATE_CACHE_CONFIG = {
  **base_config,
  'CACHE_KEY_PREFIX': 'superset_filter_cache',
  'CACHE_REDIS_URL': REDIS_URL + '/0'
}

EXPLORE_FORM_DATA_CACHE_CONFIG = {
  **base_config,
  'CACHE_KEY_PREFIX': 'superset_filter_cache_config',
  'CACHE_REDIS_URL': REDIS_URL + '/0'
}

CACHE_CONFIG = {
**base_config,
    'CACHE_KEY_PREFIX': 'cache_config',
  'CACHE_REDIS_URL': REDIS_URL + '/0'
}

DATA_CACHE_CONFIG = {
**base_config,
    'CACHE_KEY_PREFIX': 'data_cache',
  'CACHE_REDIS_URL': REDIS_URL + '/0'
}


FEATURE_FLAGS = {
    "DASHBOARD_RBAC": True,
    "ENABLE_TEMPLATE_PROCESSING": True,
  "GLOBAL_ASYNC_QUERIES": True,
}


class CeleryConfig(object):
    broker_url = REDIS_URL + '/0'
    imports = (
        "superset.sql_lab",
        "superset.tasks.scheduler",
    )
    result_backend = REDIS_URL + '/0'
    worker_prefetch_multiplier = 10
    task_acks_late = True
    task_annotations = {
        "sql_lab.get_sql_results": {
            "rate_limit": "100/s",
        },
    }

CELERY_CONFIG = CeleryConfig


