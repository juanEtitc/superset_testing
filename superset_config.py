import os

# 1. Definición básica de conexión
# Formato recomendado: redis://[password]@host:port/db
REDIS_URL = os.getenv("REDIS_URL")
if not REDIS_URL:
    raise ValueError("REDIS_URL must be set")

# 2. Configuración de Caches (usando diccionarios, no instancias)
base_config = {
    "CACHE_TYPE": "RedisCache",
    "CACHE_DEFAULT_TIMEOUT": 86400,
    "CACHE_REDIS_URL": REDIS_URL,
}

CACHE_CONFIG = {**base_config, "CACHE_KEY_PREFIX": "superset_cache"}
DATA_CACHE_CONFIG = {**base_config, "CACHE_KEY_PREFIX": "superset_data"}
FILTER_STATE_CACHE_CONFIG = {**base_config, "CACHE_KEY_PREFIX": "superset_filters"}
EXPLORE_FORM_DATA_CACHE_CONFIG = {**base_config, "CACHE_KEY_PREFIX": "superset_explore"}

# 3. Configuración de Resultados (Debe ser un diccionario para que Superset lo procese)
RESULTS_BACKEND = {
    "CACHE_TYPE": "RedisCache",
    "CACHE_REDIS_URL": f"{REDIS_URL}/2",  # Base de datos separada para resultados
    "CACHE_DEFAULT_TIMEOUT": 86400,
    "CACHE_KEY_PREFIX": "superset_results",
}

# 4. Configuración de Global Async Queries (GAQ)
FEATURE_FLAGS = {
    "DASHBOARD_RBAC": True,
    "ENABLE_TEMPLATE_PROCESSING": True,
    "GLOBAL_ASYNC_QUERIES": True,
    "GLOBAL_ASYNC_DASHBOARD_RENDER": True,
    "SQLLAB_BACKEND_PERSISTENCE": True,
}

# Transport puede ser "ws" (WebSocket) o "polling"
GLOBAL_ASYNC_QUERIES_TRANSPORT = "ws"
# Asegúrate de que este puerto sea el donde escucha el servidor de WebSocket
GLOBAL_ASYNC_QUERIES_WEBSOCKET_URL = "ws://localhost:8080/" 
GLOBAL_ASYNC_QUERIES_JWT_SECRET = "e16ced3ff0ba27807fbeaaada998cbcb252ec54a167c45bb851d1dfba428fffe"

# Configuración del backend para GAQ (Usa el índice 1)
GLOBAL_ASYNC_QUERIES_CACHE_BACKEND = {
    "CACHE_TYPE": "RedisCache",
    "CACHE_REDIS_URL": f"{REDIS_URL}/1",
    "CACHE_DEFAULT_TIMEOUT": 300,
}

# 5. Configuración de Celery
class CeleryConfig:
    broker_url = f"{REDIS_URL}/0"
    result_backend = f"{REDIS_URL}/0"
    imports = (
        "superset.sql_lab",
        "superset.tasks.scheduler",
        "superset.tasks.thumbnails",
        "superset.tasks.cache",
        "superset.tasks.async_queries",
    )
    worker_prefetch_multiplier = 10
    task_acks_late = True
    task_annotations = {
        "sql_lab.get_sql_results": {"rate_limit": "100/s"},
    }

CELERY_CONFIG = CeleryConfig
