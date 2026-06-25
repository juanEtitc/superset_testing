from __future__ import annotations

import importlib.util
import json
import logging
import os
import re
import sys
from collections import OrderedDict
from contextlib import contextmanager
from datetime import timedelta
from email.mime.multipart import MIMEMultipart
from importlib.resources import files
from typing import Any, Callable, Iterator, Literal, Optional, TYPE_CHECKING, TypedDict

import click
from celery.schedules import crontab
from flask import Blueprint
from flask_appbuilder.security.manager import AUTH_DB
from flask_caching.backends.base import BaseCache
from pandas import Series
from pandas._libs.parsers import STR_NA_VALUES
from sqlalchemy.engine.url import URL
from sqlalchemy.orm.query import Query

from superset.advanced_data_type.plugins.internet_address import internet_address
from superset.advanced_data_type.plugins.internet_port import internet_port
from superset.advanced_data_type.types import AdvancedDataType
from superset.constants import (
    CHANGE_ME_GLOBAL_ASYNC_QUERIES_JWT_SECRET,
    CHANGE_ME_GUEST_TOKEN_JWT_SECRET,
    CHANGE_ME_SECRET_KEY,
)
from superset.jinja_context import BaseTemplateProcessor
from superset.key_value.types import JsonKeyValueCodec
from superset.stats_logger import DummyStatsLogger
from superset.superset_typing import CacheConfig
from superset.tasks.types import ExecutorType
from superset.themes.types import Theme
from superset.utils import core as utils
from superset.utils.encrypt import SQLAlchemyUtilsAdapter
from superset.utils.log import DBEventLogger
from superset.utils.logging_configurator import DefaultLoggingConfigurator
from superset.utils.version import get_dev_env_label

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from flask_appbuilder.security.sqla import models
    from sqlglot import Dialect, Dialects

    from superset.connectors.sqla.models import SqlaTable
    from superset.models.core import Database
    from superset.models.dashboard import Dashboard
    from superset.models.slice import Slice

    DialectExtensions = dict[str, Dialects | type[Dialect]]

DEBUG = False

FILTER_STATE_CACHE_CONFIG = {
    "CACHE_TYPE": "RedisCache",
    "CACHE_DEFAULT_TIMEOUT": 86400,
    "CACHE_KEY_PREFIX": "superset_filter_cache",
    "CACHE_REDIS_URL": "redis://default:zGLxgQFNCJLqYACQHWRbdwGfaScmnHWA@redis.railway.internal:6379/0",
}

EXPLORE_FORM_DATA_CACHE_CONFIG = {
    "CACHE_TYPE": "RedisCache",
    "CACHE_DEFAULT_TIMEOUT": 86400,
    "CACHE_KEY_PREFIX": "superset_data_cache_config",
    "CACHE_REDIS_URL": "redis://default:zGLxgQFNCJLqYACQHWRbdwGfaScmnHWA@redis.railway.internal:6379/0",
}

DATA_CACHE_CONFIG = {
    "CACHE_TYPE": "RedisCache",
    "CACHE_DEFAULT_TIMEOUT": 86400,
    "CACHE_KEY_PREFIX": "superset_data_cache",
    "CACHE_REDIS_URL": "redis://default:zGLxgQFNCJLqYACQHWRbdwGfaScmnHWA@redis.railway.internal:6379/0",
}

STATS_LOGGER = DummyStatsLogger()
EVENT_LOGGER = DBEventLogger()
SUPERSET_LOG_VIEW = True
SUPERSET_SECURITY_VIEW_MENU = True
BASE_DIR = str(files("superset"))
if "SUPERSET_HOME" in os.environ:
    DATA_DIR = os.environ["SUPERSET_HOME"]
else:
    DATA_DIR = os.path.expanduser("~/.superset")


VERSION_INFO_FILE = str(files("superset") / "static/version_info.json")
PACKAGE_JSON_FILE = str(files("superset") / "static/assets/package.json")

FAVICONS = [{"href": "/static/assets/images/favicon.png"}]
PDF_COMPRESSION_LEVEL: Literal["NONE", "FAST", "MEDIUM", "SLOW"] = "MEDIUM"

ALEMBIC_SKIP_LOG_CONFIG = False
HASH_ALGORITHM: Literal["md5", "sha256"] = "sha256"
HASH_ALGORITHM_FALLBACKS: list[Literal["md5", "sha256"]] = ["md5"]
SECRET_KEY = os.environ.get("SUPERSET_SECRET_KEY") or CHANGE_ME_SECRET_KEY
APP_NAME = "Informes MTS"
APP_ICON = "/static/assets/images/superset-logo-horiz.png"
LOGO_TARGET_PATH = None
LOGO_TOOLTIP = ""
LOGO_RIGHT_TEXT: Callable[[], str] | str = ""
FAB_API_SWAGGER_UI = True
AUTH_TYPE = AUTH_DB
PUBLIC_ROLE_LIKE: str | None = None
BABEL_DEFAULT_LOCALE = "en"
BABEL_DEFAULT_FOLDER = "superset/translations"
LANGUAGES = {
    "en": {"flag": "us", "name": "English"},
    "es": {"flag": "es", "name": "Spanish"},
    "it": {"flag": "it", "name": "Italian"},
}


class D3Format(TypedDict, total=False):
    decimal: str
    thousands: str
    grouping: list[int]
    currency: list[str]


D3_FORMAT: D3Format = {}
DECKGL_BASE_MAP: list[list[str, str]] = None
DEFAULT_MAP_RENDERER = os.environ.get("DEFAULT_MAP_RENDERER", "maplibre")


class D3TimeFormat(TypedDict, total=False):
    date: str
    dateTime: str
    time: str
    periods: list[str]
    days: list[str]
    shortDays: list[str]
    months: list[str]
    shortMonths: list[str]


D3_TIME_FORMAT: D3TimeFormat = {}
CURRENCIES = ["USD", "EUR", "GBP", "INR", "MXN", "JPY", "CNY"]
DEFAULT_FEATURE_FLAGS: dict[str, bool] = {
    "DASHBOARD_VIRTUALIZATION": True,
    "ALERTS_ATTACH_REPORTS": True,
    "CSS_TEMPLATES": True,
    "DASHBOARD_RBAC": True,
    "DRILL_TO_DETAIL": True,
    "ENABLE_JAVASCRIPT_CONTROLS": False,
}
FEATURE_FLAGS: dict[str, bool] = {}
EXTRA_CATEGORICAL_COLOR_SCHEMES: list[dict[str, Any]] = []
_THEME_DEFAULT_BASE: Theme = {
    "token": {
        "brandAppName": APP_NAME,
        "brandLogoAlt": "Apache Superset",
        "brandLogoUrl": APP_ICON,
        "brandLogoMargin": "18px 0",
        "brandLogoHref": LOGO_TARGET_PATH or "/",
        "brandLogoHeight": "24px",
        "brandSpinnerUrl": None,
        "brandSpinnerSvg": None,
        "colorPrimary": "#2893B3",
        "colorLink": "#2893B3",
        "colorError": "#e04355",
        "colorWarning": "#fcc700",
        "colorSuccess": "#5ac189",
        "colorInfo": "#66bcfe",
        "fontUrls": [],
        "fontFamily": "Inter, Helvetica, Arial, sans-serif",
        "fontFamilyCode": "'IBM Plex Mono', 'Courier New', monospace",
        "transitionTiming": 0.3,
        "brandIconMaxWidth": 37,
        "fontSizeXS": "8",
        "fontSizeXXL": "28",
        "fontWeightNormal": "400",
        "fontWeightLight": "300",
        "fontWeightStrong": "500",
        "fontWeightBold": "700",
        "colorEditorSelection": "#fff5cf",
    },
    "algorithm": "default",
}
THEME_DEFAULT: Theme = _THEME_DEFAULT_BASE
_THEME_DARK_BASE: Theme = {
    **_THEME_DEFAULT_BASE,
    "token": {
        **_THEME_DEFAULT_BASE["token"],
        "colorEditorSelection": "#5c4d1a",
    },
    "algorithm": "dark",
}
THEME_DARK: Optional[Theme] = _THEME_DARK_BASE


def sync_theme_logo_href(
    theme: Optional[Theme], logo_target_path: Optional[str]
) -> None:
    if theme and logo_target_path and isinstance(theme.get("token"), dict):
        theme["token"]["brandLogoHref"] = logo_target_path


ENABLE_UI_THEME_ADMINISTRATION = True
THEME_FONTS_MAX_URLS: int = 15
THEME_FONT_URL_ALLOWED_DOMAINS: list[str] = [
    "fonts.googleapis.com",
    "fonts.gstatic.com",
    "use.typekit.net",
    "use.typekit.com",
]

EXTRA_SEQUENTIAL_COLOR_SCHEMES: list[dict[str, Any]] = []
CACHE_WARMUP_EXECUTORS = [ExecutorType.OWNER]
THUMBNAIL_EXECUTORS = [ExecutorType.CURRENT_USER]
THUMBNAIL_DASHBOARD_DIGEST_FUNC: (
    Callable[[Dashboard, ExecutorType, str], str | None] | None
) = None
THUMBNAIL_CHART_DIGEST_FUNC: Callable[[Slice, ExecutorType, str], str | None] | None = (
    None
)

THUMBNAIL_CACHE_CONFIG: CacheConfig = {
    "CACHE_TYPE": "NullCache",
    "CACHE_DEFAULT_TIMEOUT": int(timedelta(days=7).total_seconds()),
    "CACHE_NO_NULL_WARNING": True,
}
THUMBNAIL_ERROR_CACHE_TTL = int(timedelta(days=1).total_seconds())
UPLOAD_FOLDER = BASE_DIR + "/static/uploads/"
UPLOAD_CHUNK_SIZE = 4096
UPLOAD_MAX_FILE_SIZE_BYTES: int | None = 100 * 1024 * 1024
CACHE_DEFAULT_TIMEOUT = int(timedelta(days=1).total_seconds())
CACHE_CONFIG: CacheConfig = {"CACHE_TYPE": "NullCache"}
DATA_CACHE_CONFIG: CacheConfig = {"CACHE_TYPE": "NullCache"}

FILTER_STATE_CACHE_CONFIG: CacheConfig = {
    "CACHE_TYPE": "SupersetMetastoreCache",
    "CACHE_DEFAULT_TIMEOUT": int(timedelta(days=90).total_seconds()),
    "REFRESH_TIMEOUT_ON_RETRIEVAL": True,
    "CODEC": JsonKeyValueCodec(),
}

EXPLORE_FORM_DATA_CACHE_CONFIG: CacheConfig = {
    "CACHE_TYPE": "SupersetMetastoreCache",
    "CACHE_DEFAULT_TIMEOUT": int(timedelta(days=7).total_seconds()),
    "REFRESH_TIMEOUT_ON_RETRIEVAL": True,
    "CODEC": JsonKeyValueCodec(),
}
STORE_CACHE_KEYS_IN_METADATA_DB = False
ENABLE_CORS = True
CORS_OPTIONS: dict[Any, Any] = {
    "origins": [
        "https://tile.openstreetmap.org",
        "https://tile.osm.ch",
    ]
}
HTML_SANITIZATION = True
HTML_SANITIZATION_SCHEMA_EXTENSIONS: dict[str, Any] = {}
SUPERSET_WEBSERVER_DOMAINS = None
EXCEL_EXTENSIONS = {"xlsx", "xls"}
CSV_EXTENSIONS = {"csv", "tsv", "txt"}
COLUMNAR_EXTENSIONS = {"parquet", "zip"}
ALLOWED_EXTENSIONS = {*EXCEL_EXTENSIONS, *CSV_EXTENSIONS, *COLUMNAR_EXTENSIONS}
CSV_EXPORT = {"encoding": "utf-8-sig"}
CSV_STREAMING_ROW_THRESHOLD = 100000
LOGGING_CONFIGURATOR = DefaultLoggingConfigurator()
LOG_FORMAT = "%(asctime)s:%(levelname)s:%(name)s:%(message)s"
LOG_LEVEL = logging.DEBUG if DEBUG else logging.INFO
ENABLE_TIME_ROTATE = False
TIME_ROTATE_LOG_LEVEL = logging.DEBUG if DEBUG else logging.INFO
FILENAME = os.path.join(DATA_DIR, "superset.log")
ROLLOVER = "midnight"
INTERVAL = 1
BACKUP_COUNT = 30
QUERY_LOGGER = None
MAPBOX_API_KEY = os.environ.get("MAPBOX_API_KEY", "")
SQL_MAX_ROW = 100000
MAX_PROPHET_PERIODS = 10000
TABLE_VIZ_MAX_ROW_SERVER = 500000
DISPLAY_MAX_ROW = 10000
DEFAULT_SQLLAB_LIMIT = 1000
DATASET_AUTO_DETECT_DATETIME_FORMATS = True
DATETIME_FORMAT_DETECTION_SAMPLE_SIZE = 1000
SUPERSET_META_DB_LIMIT: int | None = 1000

SQLLAB_SAVE_WARNING_MESSAGE = None
SQLLAB_SCHEDULE_WARNING_MESSAGE = None

SQLLAB_PAYLOAD_MAX_MB = None
DASHBOARD_AUTO_REFRESH_MODE: Literal["fetch", "force"] = "force"

DASHBOARD_AUTO_REFRESH_INTERVALS = [
    [0, "Don't refresh"],
    [10, "10 seconds"],
    [30, "30 seconds"],
    [60, "1 minute"],
    [300, "5 minutes"],
    [1800, "30 minutes"],
    [3600, "1 hour"],
    [21600, "6 hours"],
    [43200, "12 hours"],
    [86400, "24 hours"],
]

DASHBOARD_LIST_CUSTOM_TAGS_ONLY: bool = False

CELERY_BEAT_SCHEDULER_EXPIRES = timedelta(weeks=1)


class CeleryConfig:
    broker_url = "sqla+sqlite:///celerydb.sqlite"
    imports = (
        "superset.sql_lab",
        "superset.tasks.scheduler",
        "superset.tasks.thumbnails",
        "superset.tasks.cache",
        "superset.tasks.slack",
    )
    result_backend = "db+sqlite:///celery_results.sqlite"
    worker_prefetch_multiplier = 1
    task_acks_late = False
    task_annotations = {
        "sql_lab.get_sql_results": {
            "rate_limit": "100/s",
        },
    }
    beat_schedule = {
        "reports.scheduler": {
            "task": "reports.scheduler",
            "schedule": crontab(minute="*", hour="*"),
            "options": {"expires": int(CELERY_BEAT_SCHEDULER_EXPIRES.total_seconds())},
        },
        "reports.prune_log": {
            "task": "reports.prune_log",
            "schedule": crontab(minute=0, hour=0),
        },
    }


CELERY_CONFIG: type[CeleryConfig] | None = CeleryConfig

DEFAULT_HTTP_HEADERS: dict[str, Any] = {}
OVERRIDE_HTTP_HEADERS: dict[str, Any] = {}
HTTP_HEADERS: dict[str, Any] = {}


DEFAULT_DB_ID = None


SQLLAB_TIMEOUT = int(timedelta(seconds=30).total_seconds())


BQ_FETCH_MAX_MB = 200


SQLLAB_VALIDATION_TIMEOUT = int(timedelta(seconds=10).total_seconds())


SQLLAB_DEFAULT_DBID = None


SQLLAB_ASYNC_TIME_LIMIT_SEC = int(timedelta(hours=6).total_seconds())


SQLLAB_QUERY_COST_ESTIMATE_TIMEOUT = int(timedelta(seconds=10).total_seconds())


SQLLAB_QUERY_RESULT_TIMEOUT = 0

ODPS_PARTITION_DETECT_TIMEOUT = int(timedelta(seconds=30).total_seconds())

QUERY_COST_FORMATTERS_BY_ENGINE: dict[
    str, Callable[[list[dict[str, Any]]], list[dict[str, Any]]]
] = {}


SQLLAB_CTAS_NO_LIMIT = False
SQLLAB_CTAS_SCHEMA_NAME_FUNC: (
    None | (Callable[[Database, models.User, str, str], str])
) = None


RESULTS_BACKEND: BaseCache | None = None

RESULTS_BACKEND_USE_MSGPACK = True

CSV_TO_HIVE_UPLOAD_S3_BUCKET = None

CSV_TO_HIVE_UPLOAD_DIRECTORY = "EXTERNAL_HIVE_TABLES/"


def CSV_TO_HIVE_UPLOAD_DIRECTORY_FUNC(
    database: Database,
    user: models.User,
    schema: str | None,
) -> str:

    return os.path.join(
        CSV_TO_HIVE_UPLOAD_DIRECTORY, str(database.id), schema or "", ""
    )


UPLOADED_CSV_HIVE_NAMESPACE: str | None = None


def allowed_schemas_for_csv_upload(
    database: Database,
    user: models.User,
) -> list[str]:
    return [UPLOADED_CSV_HIVE_NAMESPACE] if UPLOADED_CSV_HIVE_NAMESPACE else []


ALLOWED_USER_CSV_SCHEMA_FUNC = allowed_schemas_for_csv_upload


CSV_DEFAULT_NA_NAMES = list(STR_NA_VALUES)

REPORTS_CSV_NA_NAMES: list[str] | None = None

READ_CSV_CHUNK_SIZE = 1000

JINJA_CONTEXT_ADDONS: dict[str, Callable[..., Any]] = {}

CUSTOM_TEMPLATE_PROCESSORS: dict[str, type[BaseTemplateProcessor]] = {}


ROBOT_PERMISSION_ROLES = ["Public", "Gamma", "Alpha", "Admin", "sql_lab"]

CONFIG_PATH_ENV_VAR = "SUPERSET_CONFIG_PATH"


EXTENSION_STARTUP_LOCK_TIMEOUT = 30

FLASK_APP_MUTATOR = None


SMTP_HOST = "localhost"
SMTP_STARTTLS = True
SMTP_SSL = False
SMTP_USER = "superset"
SMTP_PORT = 25
SMTP_PASSWORD = "superset"
SMTP_MAIL_FROM = "superset@superset.com"

SMTP_SSL_SERVER_AUTH = False

SMTP_TIMEOUT = 30
ENABLE_CHUNK_ENCODING = False

SILENCE_FAB = True

FAB_ADD_SECURITY_VIEWS = True
FAB_ADD_SECURITY_API = True
FAB_ADD_SECURITY_PERMISSION_VIEW = False
FAB_ADD_SECURITY_VIEW_MENU_VIEW = False
FAB_ADD_SECURITY_PERMISSION_VIEWS_VIEW = False

FAB_API_KEY_ENABLED = False
FAB_API_KEY_PREFIXES = ["sst_"]
TROUBLESHOOTING_LINK = ""
WTF_CSRF_TIME_LIMIT = int(timedelta(weeks=1).total_seconds())
PERMISSION_INSTRUCTIONS_LINK = ""
BLUEPRINTS: list[Blueprint] = []
TRACKING_URL_TRANSFORMER = lambda url: url
DB_POLL_INTERVAL_SECONDS: dict[str, int] = {}
PRESTO_POLL_INTERVAL = int(timedelta(seconds=1).total_seconds())
ALLOWED_EXTRA_AUTHENTICATIONS: dict[str, dict[str, Callable[..., Any]]] = {}


DASHBOARD_TEMPLATE_ID = None


@contextmanager
def engine_context_manager(
    database: Database,
    catalog: str | None,
    schema: str | None,
) -> Iterator[None]:
    yield None


ENGINE_CONTEXT_MANAGER = engine_context_manager

DB_CONNECTION_MUTATOR = None
DB_SQLA_URI_VALIDATOR: Callable[[URL], None] | None = None


def SQL_QUERY_MUTATOR(sql: str, **kwargs: Any) -> str:
    return sql


MUTATE_AFTER_SPLIT = False
MUTATE_ALERT_QUERY = False


def EMAIL_HEADER_MUTATOR(msg: MIMEMultipart, **kwargs: Any) -> MIMEMultipart:
    return msg


EXCLUDE_USERS_FROM_LISTS: list[str] | None = None
DBS_AVAILABLE_DENYLIST: dict[str, set[str]] = {}
MACHINE_AUTH_PROVIDER_CLASS = "superset.utils.machine_auth.MachineAuthProvider"
IMPALA_CANCEL_QUERY_ALLOW_INTERNAL_HOSTS: bool = False
EMAIL_REPORTS_SUBJECT_PREFIX = "[Report] "
EMAIL_REPORTS_CTA = "Explore in Superset"
SLACK_API_TOKEN: Callable[[], str] | str | None = None
SLACK_PROXY = None
SLACK_CACHE_TIMEOUT = int(timedelta(days=1).total_seconds())
SLACK_API_RATE_LIMIT_RETRY_COUNT = 2
SLACK_API_TIMEOUT = 30
EMAIL_PAGE_RENDER_WAIT = int(timedelta(seconds=30).total_seconds())
BUG_REPORT_URL = None
BUG_REPORT_TEXT = "Report a bug"
BUG_REPORT_ICON = None
DOCUMENTATION_URL = None
DOCUMENTATION_TEXT = "Documentation"
DOCUMENTATION_ICON = None

DEFAULT_RELATIVE_START_TIME = "today"
DEFAULT_RELATIVE_END_TIME = "today"


SQL_VALIDATORS_BY_ENGINE = {
    "presto": "PrestoDBSQLValidator",
    "postgresql": "PostgreSQLValidator",
}

PREFERRED_DATABASES: list[str] = [
    "PostgreSQL",
    "Presto",
    "MySQL",
    "SQLite",
]
TEST_DATABASE_CONNECTION_TIMEOUT = timedelta(seconds=30)
CONTENT_SECURITY_POLICY_WARNING = True
TALISMAN_ENABLED = utils.cast_to_boolean(os.environ.get("TALISMAN_ENABLED", True))
TALISMAN_CONFIG = {
    "content_security_policy": {
        "base-uri": ["'self'"],
        "default-src": ["'self'"],
        "img-src": [
            "'self'",
            "blob:",
            "data:",
            "https://apachesuperset.gateway.scarf.sh",
            "https://static.scarf.sh/",
            "ows.terrestris.de",
            "https://cdn.document360.io",
        ],
        "worker-src": ["'self'", "blob:"],
        "connect-src": [
            "'self'",
            "https://api.mapbox.com",
            "https://events.mapbox.com",
            "https://tile.openstreetmap.org",
            "https://tile.osm.ch",
            "https://basemaps.cartocdn.com",
            "https://*.basemaps.cartocdn.com",
            "https://tiles.openfreemap.org",
            "https://*.maptiler.com",
            "https://tiles.stadiamaps.com",
            "https://tiles.versatiles.org",
            "https://*.protomaps.com",
            "https://*.maplibre.org",
        ],
        "object-src": "'none'",
        "style-src": [
            "'self'",
            "'unsafe-inline'",
            *[f"https://{d}" for d in THEME_FONT_URL_ALLOWED_DOMAINS],
        ],
        "font-src": [
            "'self'",
            *[f"https://{d}" for d in THEME_FONT_URL_ALLOWED_DOMAINS],
        ],
        "script-src": ["'self'", "'strict-dynamic'"],
    },
    "content_security_policy_nonce_in": ["script-src"],
    "force_https": False,
    "session_cookie_secure": False,
}

TALISMAN_DEV_CONFIG = {
    "content_security_policy": {
        "base-uri": ["'self'"],
        "default-src": ["'self'"],
        "img-src": [
            "'self'",
            "blob:",
            "data:",
            "https://apachesuperset.gateway.scarf.sh",
            "https://static.scarf.sh/",
            "https://cdn.brandfolder.io",
            "ows.terrestris.de",
            "https://cdn.document360.io",
        ],
        "worker-src": ["'self'", "blob:"],
        "connect-src": [
            "'self'",
            "https://api.mapbox.com",
            "https://events.mapbox.com",
            "https://tile.openstreetmap.org",
            "https://tile.osm.ch",
            "https://basemaps.cartocdn.com",
            "https://*.basemaps.cartocdn.com",
            "https://tiles.openfreemap.org",
            "https://*.maptiler.com",
            "https://tiles.stadiamaps.com",
            "https://tiles.versatiles.org",
            "https://*.protomaps.com",
            "https://*.maplibre.org",
        ],
        "object-src": "'none'",
        "style-src": [
            "'self'",
            "'unsafe-inline'",
            *[f"https://{d}" for d in THEME_FONT_URL_ALLOWED_DOMAINS],
        ],
        "font-src": [
            "'self'",
            *[f"https://{d}" for d in THEME_FONT_URL_ALLOWED_DOMAINS],
        ],
        "script-src": ["'self'", "'unsafe-inline'", "'unsafe-eval'"],
    },
    "content_security_policy_nonce_in": ["script-src"],
    "force_https": False,
    "session_cookie_secure": False,
}


SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SECURE = False
SESSION_COOKIE_SAMESITE: Literal["None", "Lax", "Strict"] | None = "Lax"
SESSION_SERVER_SIDE = False
SEND_FILE_MAX_AGE_DEFAULT = int(timedelta(days=365).total_seconds())
SQLALCHEMY_EXAMPLES_URI = (
    "sqlite:///" + os.path.join(DATA_DIR, "examples.db") + "?check_same_thread=false"
)
STATIC_ASSETS_PREFIX = ""
PREVENT_UNSAFE_DB_CONNECTIONS = True
PREVENT_UNSAFE_DEFAULT_URLS_ON_DATASET = True
DATASET_IMPORT_ALLOWED_DATA_URLS = [r".*"]
DATASET_IMPORT_ALLOW_INTERNAL_DATA_URLS: bool = False
SSL_CERT_PATH: str | None = None
SQLA_TABLE_MUTATOR = lambda table: table
GLOBAL_ASYNC_QUERY_MANAGER_CLASS = (
    "superset.async_events.async_query_manager.AsyncQueryManager"
)
GLOBAL_ASYNC_QUERIES_REDIS_STREAM_PREFIX = "async-events-"
GLOBAL_ASYNC_QUERIES_REDIS_STREAM_LIMIT = 1000
GLOBAL_ASYNC_QUERIES_REDIS_STREAM_LIMIT_FIREHOSE = 1000000
GLOBAL_ASYNC_QUERIES_REGISTER_REQUEST_HANDLERS = True
GLOBAL_ASYNC_QUERIES_JWT_COOKIE_NAME = "async-token"
GLOBAL_ASYNC_QUERIES_JWT_COOKIE_SECURE = False
GLOBAL_ASYNC_QUERIES_JWT_COOKIE_SAMESITE: None | (Literal["None", "Lax", "Strict"]) = (
    None
)
GLOBAL_ASYNC_QUERIES_JWT_COOKIE_DOMAIN = None
GLOBAL_ASYNC_QUERIES_JWT_SECRET = CHANGE_ME_GLOBAL_ASYNC_QUERIES_JWT_SECRET
GLOBAL_ASYNC_QUERIES_JWT_EXPIRATION_SECONDS = int(timedelta(hours=1).total_seconds())
GLOBAL_ASYNC_QUERIES_TRANSPORT: Literal["polling", "ws"] = "polling"
GLOBAL_ASYNC_QUERIES_POLLING_DELAY = int(
    timedelta(milliseconds=500).total_seconds() * 1000
)
GLOBAL_ASYNC_QUERIES_WEBSOCKET_URL = "ws://127.0.0.1:8080/"
GLOBAL_ASYNC_QUERIES_CACHE_BACKEND = {
    "CACHE_TYPE": "RedisCache",
    "CACHE_REDIS_HOST": "localhost",
    "CACHE_REDIS_PORT": 6379,
    "CACHE_REDIS_USER": "",
    "CACHE_REDIS_PASSWORD": "",
    "CACHE_REDIS_DB": 0,
    "CACHE_DEFAULT_TIMEOUT": 300,
    "CACHE_REDIS_SENTINELS": [("localhost", 26379)],
    "CACHE_REDIS_SENTINEL_MASTER": "mymaster",
    "CACHE_REDIS_SENTINEL_PASSWORD": None,
    "CACHE_REDIS_SSL": False,
    "CACHE_REDIS_SSL_CERTFILE": None,
    "CACHE_REDIS_SSL_KEYFILE": None,
    "CACHE_REDIS_SSL_CERT_REQS": "required",
    "CACHE_REDIS_SSL_CA_CERTS": None,
}
GUEST_ROLE_NAME = "Public"
GUEST_TOKEN_JWT_SECRET = CHANGE_ME_GUEST_TOKEN_JWT_SECRET
GUEST_TOKEN_JWT_ALGO = "HS256"
GUEST_TOKEN_HEADER_NAME = "X-GuestToken"
GUEST_TOKEN_JWT_EXP_SECONDS = 300
GUEST_TOKEN_VALIDATOR_HOOK = None
GUEST_TOKEN_REVOCATION_ENABLED = False
DATASET_HEALTH_CHECK: Callable[[SqlaTable], str] | None = None
ADVANCED_DATA_TYPES: dict[str, AdvancedDataType] = {
    "internet_address": internet_address,
    "port": internet_port,
}
WELCOME_PAGE_LAST_TAB: Literal["examples", "all"] | tuple[str, list[dict[str, Any]]] = (
    "all"
)
ZIPPED_FILE_MAX_SIZE = 100 * 1024 * 1024
ZIP_FILE_MAX_COMPRESS_RATIO = 200.0
ZIP_FILE_MAX_TOTAL_SIZE = 1024 * 1024 * 1024
ENVIRONMENT_TAG_CONFIG = {
    "variable": "SUPERSET_ENV",
    "values": {
        "debug": {
            "color": "error",
            "text": "flask-debug",
        },
        "development": {
            "color": "processing",
            "text": get_dev_env_label(),
        },
        "production": {
            "color": "",
            "text": "",
        },
    },
}


try:
    from superset.custom_database_errors import CUSTOM_DATABASE_ERRORS
except ImportError:
    CUSTOM_DATABASE_ERRORS = {}
LOCAL_EXTENSIONS: list[str] = []
EXTENSIONS_PATH: str | None = None
EXTENSION_DENYLIST: list[str] = []
EXTENSION_VERSION_POLICY: dict[str, str] = {}
TASK_ABORT_POLLING_DEFAULT_INTERVAL = 10
TASK_PROGRESS_UPDATE_THROTTLE_INTERVAL = 2
DISTRIBUTED_COORDINATION_CONFIG: CacheConfig | None = None
DISTRIBUTED_LOCK_DEFAULT_TTL = 30
TASKS_ABORT_CHANNEL_PREFIX = "gtf:abort:"

if CONFIG_PATH_ENV_VAR in os.environ:
    cfg_path = os.environ[CONFIG_PATH_ENV_VAR]
    try:
        module = sys.modules[__name__]
        spec = importlib.util.spec_from_file_location("superset_config", cfg_path)
        override_conf = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(override_conf)
        for key in dir(override_conf):
            if key.isupper():
                setattr(module, key, getattr(override_conf, key))

        click.secho(f"Loaded your LOCAL configuration at [{cfg_path}]", fg="cyan")
    except Exception:
        logger.exception(
            "Failed to import config for %s=%s", CONFIG_PATH_ENV_VAR, cfg_path
        )
        raise
elif importlib.util.find_spec("superset_config"):
    try:
        import superset_config
        from superset_config import *

        click.secho(
            f"Loaded your LOCAL configuration at [{superset_config.__file__}]",
            fg="cyan",
        )
    except Exception:
        logger.exception("Found but failed to import local superset_config")
        raise
ENV_VAR_KEYS = {
    "SUPERSET__SQLALCHEMY_DATABASE_URI",
    "SUPERSET__SQLALCHEMY_EXAMPLES_URI",
}
for env_var in ENV_VAR_KEYS:
    if env_var in os.environ:
        config_var = env_var.replace("SUPERSET__", "")
        globals()[config_var] = os.environ[env_var]
sync_theme_logo_href(THEME_DEFAULT, LOGO_TARGET_PATH)
sync_theme_logo_href(THEME_DARK, LOGO_TARGET_PATH)
