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
  'CACHE_REDIS_URL': REDIS_URL + '/1'
}

CACHE_CONFIG = {
**base_config,
    'CACHE_KEY_PREFIX': 'cache_config',
  'CACHE_REDIS_URL': REDIS_URL + '/2'
}

DATA_CACHE_CONFIG = {
**base_config,
    'CACHE_KEY_PREFIX': 'data_cache',
  'CACHE_REDIS_URL': REDIS_URL + '/3'
}


FEATURE_FLAGS = {
    "DASHBOARD_RBAC": True,
    "ENABLE_TEMPLATE_PROCESSING": True,
}
