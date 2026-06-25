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


FEATURE_FLAGS: dict[str, bool] = {
    # =================================================================
    # IN DEVELOPMENT
    # =================================================================
    # These features are considered unfinished and should only be used
    # on development environments.
    # -----------------------------------------------------------------
    # Enables Table V2 (AG Grid) viz plugin
    # @lifecycle: development
    "AG_GRID_TABLE_ENABLED": False,
    # Enables experimental tabs UI for Alerts and Reports
    # @lifecycle: development
    "ALERT_REPORT_TABS": False,
    # Enables experimental chart plugins
    # @lifecycle: development
    "CHART_PLUGINS_EXPERIMENTAL": False,
    # Experimental PyArrow engine for CSV parsing (may have issues with dates/nulls)
    # @lifecycle: development
    "CSV_UPLOAD_PYARROW_ENGINE": False,
    # Allow metrics and columns to be grouped into folders in the chart builder
    # @lifecycle: development
    "DATASET_FOLDERS": False,
    # Enable support for date range timeshifts (e.g., "2015-01-03 : 2015-01-04")
    # in addition to relative timeshifts (e.g., "1 day ago")
    # @lifecycle: development
    "DATE_RANGE_TIMESHIFTS_ENABLED": False,
    # Enable API key authentication via FAB SecurityManager
    # When enabled, users can create/manage API keys in the User Info page
    # @lifecycle: development
    "FAB_API_KEY_ENABLED": False,
    # Enable granular export controls (can_export_data, can_export_image,
    # can_copy_clipboard) instead of the single can_csv permission
    # @lifecycle: development
    "GRANULAR_EXPORT_CONTROLS": False,
    # Enable semantic layers and show semantic views alongside datasets
    # @lifecycle: development
    "SEMANTIC_LAYERS": False,
    # Enables advanced data type support
    # @lifecycle: development
    "ENABLE_ADVANCED_DATA_TYPES": False,
    # Enable Superset extensions for custom functionality without modifying core
    # @lifecycle: development
    "ENABLE_EXTENSIONS": False,
    # Enable Matrixify feature for matrix-style chart layouts
    # @lifecycle: development
    "MATRIXIFY": False,
    # Try to optimize SQL queries — for now only predicate pushdown is supported
    # @lifecycle: development
    "OPTIMIZE_SQL": False,
    # Expand nested types in Presto into extra columns/arrays. Experimental,
    # doesn't work with all nested types.
    # @lifecycle: development
    "PRESTO_EXPAND_DATA": False,
    # Enable Table V2 time comparison feature
    # @lifecycle: development
    "TABLE_V2_TIME_COMPARISON_ENABLED": False,
    # Enables the tagging system for organizing assets
    # @lifecycle: development
    "TAGGING_SYSTEM": False,
    # =================================================================
    # IN TESTING
    # =================================================================
    # These features are finished but currently being tested.
    # They are usable, but may still contain some bugs.
    # -----------------------------------------------------------------
    # Enables filter functionality in Alerts and Reports
    # @lifecycle: testing
    "ALERT_REPORTS_FILTER": False,
    # Enables Alerts and Reports functionality
    # @lifecycle: testing
    # @docs: https://superset.apache.org/docs/configuration/alerts-reports
    "ALERT_REPORTS": False,
    # Enables Slack V2 integration for Alerts and Reports
    # @lifecycle: testing
    "ALERT_REPORT_SLACK_V2": False,
    # Enables webhook integration for Alerts and Reports
    # @lifecycle: testing
    "ALERT_REPORT_WEBHOOK": False,
    # Allow users to export full CSV of table viz type.
    # Warning: Could cause server memory/compute issues with large datasets.
    # @lifecycle: testing
    "ALLOW_FULL_CSV_EXPORT": False,
    # Enable caching per impersonation key in datasources with user impersonation
    # @lifecycle: testing
    "CACHE_IMPERSONATION": False,
    # Allow users to optionally specify date formats in email subjects
    # @lifecycle: testing
    # @docs: https://superset.apache.org/docs/configuration/alerts-reports
    "DATE_FORMAT_IN_EMAIL_SUBJECT": False,
    # Enable dynamic plugin loading
    # @lifecycle: testing
    "DYNAMIC_PLUGINS": False,
    # Enables endpoints to cache and retrieve dashboard screenshots via webdriver.
    # Requires Celery and THUMBNAIL_CACHE_CONFIG.
    # @lifecycle: testing
    "ENABLE_DASHBOARD_SCREENSHOT_ENDPOINTS": False,
    # Generate screenshots (PDF/JPG) of dashboards using web driver.
    # Depends on ENABLE_DASHBOARD_SCREENSHOT_ENDPOINTS.
    # @lifecycle: testing
    "ENABLE_DASHBOARD_DOWNLOAD_WEBDRIVER_SCREENSHOT": False,
    # Allows users to add a superset:// DB that can query across databases.
    # Experimental with potential security/performance risks.
    # See SUPERSET_META_DB_LIMIT.
    # @lifecycle: testing
    # @docs: https://superset.apache.org/user-docs/databases/supported/superset-meta-database
    "ENABLE_SUPERSET_META_DB": False,
    # Enable query cost estimation. Supported in Presto, Postgres, and BigQuery.
    # Requires `cost_estimate_enabled: true` in database `extra` attribute.
    # @lifecycle: testing
    "ESTIMATE_QUERY_COST": False,
    # Enable async queries for dashboards and Explore via WebSocket.
    # Requires Redis 5.0+ and Celery workers.
    # @lifecycle: testing
    # @docs: https://superset.apache.org/docs/contributing/misc#async-chart-queries
    "GLOBAL_ASYNC_QUERIES": False,
    # When impersonating a user, use the email prefix instead of username
    # @lifecycle: testing
    "IMPERSONATE_WITH_EMAIL_PREFIX": False,
    # Replace Selenium with Playwright for reports and thumbnails.
    # Supports deck.gl visualizations. Requires playwright pip package.
    # @lifecycle: testing
    "PLAYWRIGHT_REPORTS_AND_THUMBNAILS": False,
    # Apply RLS rules to SQL Lab queries. Requires query parsing/manipulation.
    # May break queries or allow RLS bypass. Use with care!
    # @lifecycle: testing
    "RLS_IN_SQLLAB": False,
    # Allow users to enable SSH tunneling when creating a DB connection.
    # DB engine must support SSH Tunnels.
    # @lifecycle: testing
    # @docs: https://superset.apache.org/docs/configuration/setup-ssh-tunneling
    "SSH_TUNNELING": False,
    # Enable AWS IAM authentication for database connections (Aurora, Redshift).
    # Allows cross-account role assumption via STS AssumeRole.
    # Security note: When enabled, ensure Superset's IAM role has restricted
    # sts:AssumeRole permissions to prevent unauthorized access.
    # @lifecycle: testing
    "AWS_DATABASE_IAM_AUTH": False,
    # Global Task Framework - unified task management with progress tracking,
    # cancellation, and deduplication.
    "GLOBAL_TASK_FRAMEWORK": False,
    # Use analogous colors in charts
    # @lifecycle: testing
    "USE_ANALOGOUS_COLORS": False,
    # =================================================================
    # STABLE - PATH TO DEPRECATION
    # =================================================================
    # These flags are stable and on path to becoming default behavior,
    # after which the flag will be deprecated.
    # -----------------------------------------------------------------
    # Enables dashboard virtualization for improved performance
    # @lifecycle: stable
    # @category: path_to_deprecation
    "DASHBOARD_VIRTUALIZATION": True,
    # =================================================================
    # STABLE - RUNTIME CONFIGURATION
    # =================================================================
    # These flags act as runtime configuration options. They are stable
    # but will be retained as configuration options rather than deprecated.
    # -----------------------------------------------------------------
    # When enabled, alerts send email/slack with screenshot AND link.
    # When disabled, alerts send only link; reports still send screenshot.
    # @lifecycle: stable
    # @category: runtime_config
    "ALERTS_ATTACH_REPORTS": True,
    # Allow ad-hoc subqueries in SQL Lab
    # @lifecycle: stable
    # @category: runtime_config
    "ALLOW_ADHOC_SUBQUERY": False,
    # Enable caching per user key for Superset cache
    # @lifecycle: stable
    # @category: runtime_config
    "CACHE_QUERY_BY_USER": False,
    # Enables CSS Templates in Settings menu and dashboard forms
    # @lifecycle: stable
    # @category: runtime_config
    "CSS_TEMPLATES": True,
    # Role-based access control for dashboards
    # @lifecycle: stable
    # @category: runtime_config
    # @docs: https://superset.apache.org/docs/using-superset/creating-your-first-dashboard
    "DASHBOARD_RBAC": True,
    # Supports simultaneous data and dashboard virtualization for backend performance
    # @lifecycle: stable
    # @category: runtime_config
    "DASHBOARD_VIRTUALIZATION_DEFER_DATA": False,
    # Data panel closed by default in chart builder
    # @lifecycle: stable
    # @category: runtime_config
    "DATAPANEL_CLOSED_BY_DEFAULT": False,
    # Hide the logout button in embedded contexts (e.g., when using SSO in iframes)
    # @lifecycle: stable
    # @category: runtime_config
    # @docs: https://superset.apache.org/docs/configuration/networking-settings#hiding-the-logout-button-in-embedded-contexts
    "DISABLE_EMBEDDED_SUPERSET_LOGOUT": False,
    # Enable drill-by functionality in charts
    # @lifecycle: stable
    # @category: runtime_config
    "DRILL_BY": True,
    # Enable Druid JOINs (requires Druid version with JOIN support)
    # @lifecycle: stable
    # @category: runtime_config
    "DRUID_JOINS": False,
    # Enable sharing charts with embedding
    # @lifecycle: stable
    # @category: runtime_config
    "EMBEDDABLE_CHARTS": True,
    # Enable embedded Superset functionality
    # @lifecycle: stable
    # @category: runtime_config
    "EMBEDDED_SUPERSET": False,
    # Enable Jinja templating in SQL queries
    # @lifecycle: stable
    # @category: runtime_config
    "ENABLE_TEMPLATE_PROCESSING": True,
    # Escape HTML in Markdown components (rather than rendering it)
    # @lifecycle: stable
    # @category: runtime_config
    "ESCAPE_MARKDOWN_HTML": False,
    # Filter bar closed by default when opening dashboard
    # @lifecycle: stable
    # @category: runtime_config
    "FILTERBAR_CLOSED_BY_DEFAULT": False,
    # Force garbage collection after every request
    # @lifecycle: stable
    # @category: runtime_config
    "FORCE_GARBAGE_COLLECTION_AFTER_EVERY_REQUEST": False,
    # Use card view as default in list views
    # @lifecycle: stable
    # @category: runtime_config
    "LISTVIEWS_DEFAULT_CARD_VIEW": False,
    # Hide user info in the navigation menu
    # @lifecycle: stable
    # @category: runtime_config
    "MENU_HIDE_USER_INFO": False,
    # Use Slack avatars for users. Requires adding slack-edge.com to TALISMAN_CONFIG.
    # @lifecycle: stable
    # @category: runtime_config
    "SLACK_ENABLE_AVATARS": False,
    # Enable SQL Lab backend persistence for query state
    # @lifecycle: stable
    # @category: runtime_config
    "SQLLAB_BACKEND_PERSISTENCE": True,
    # Force SQL Lab to run async via Celery regardless of database settings
    # @lifecycle: stable
    # @category: runtime_config
    "SQLLAB_FORCE_RUN_ASYNC": False,
    # Exposes API endpoint to compute thumbnails
    # @lifecycle: stable
    # @category: runtime_config
    # @docs: https://superset.apache.org/docs/configuration/cache
    "THUMBNAILS": False,
    # =================================================================
    # STABLE - INTERNAL/ADMIN
    # =================================================================
    # These flags are for internal use or administrative purposes.
    # -----------------------------------------------------------------
    # Enable factory reset CLI command
    # @lifecycle: stable
    # @category: internal
    "ENABLE_FACTORY_RESET_COMMAND": False,
    # =================================================================
    # DEPRECATED
    # =================================================================
    # These flags default to True and will be removed in a future major
    # release. Set to True in your config to avoid unexpected changes.
    # -----------------------------------------------------------------
    # Avoid color collisions in charts by using distinct colors
    # @lifecycle: deprecated
    "AVOID_COLORS_COLLISION": True,
    # Enable drill-to-detail functionality in charts
    # @lifecycle: deprecated
    "DRILL_TO_DETAIL": True,
    # Allow JavaScript in chart controls. WARNING: XSS security vulnerability!
    # @lifecycle: deprecated
    "ENABLE_JAVASCRIPT_CONTROLS": False,
}
