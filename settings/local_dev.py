"""Local development settings for wger"""

# ruff: noqa: F405
# ruff: noqa: F403

# wger
from .settings_global import *
import environ

# Load environment variables from .env if present
env_file = BASE_DIR.parent / '.env'
if env_file.exists():
    environ.Env.read_env(env_file)

DEBUG = True

# List of administrators
ADMINS = ['"Your name" <your_email@example.com>']
MANAGERS = ADMINS

# Don't use this key in production!
SECRET_KEY = 'wger-local-development-supersecret-key-1234567890!'

# Allow all hosts to access the application.
ALLOWED_HOSTS = [
    '*',
]

ENABLE_EMAIL = os.environ.get('ENABLE_EMAIL', '').lower() in ('true', '1', 'yes')
if ENABLE_EMAIL:
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.resend.com')
    EMAIL_PORT = int(os.environ.get('EMAIL_PORT', 587))
    EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', 'resend')
    EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
    EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', 'True').lower() in ('true', '1', 'yes')
    EMAIL_USE_SSL = os.environ.get('EMAIL_USE_SSL', 'False').lower() in ('true', '1', 'yes')
    EMAIL_TIMEOUT = 60
else:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

DEFAULT_FROM_EMAIL = os.environ.get('FROM_EMAIL', 'Fit Me <hello@fitmefitness.lk>')
WGER_SETTINGS['EMAIL_FROM'] = DEFAULT_FROM_EMAIL
SERVER_EMAIL = DEFAULT_FROM_EMAIL
EMAIL_FROM_ADDRESS = DEFAULT_FROM_EMAIL


# CELERY_BROKER_URL = "redis://localhost:6379/2"
# CELERY_RESULT_BACKEND = "redis://localhost:6379/2"

CSRF_TRUSTED_ORIGINS = ['http://localhost:8000', 'http://127.0.0.1:8000']

EXPOSE_PROMETHEUS_METRICS = True

COMPRESS_ENABLED = False
AXES_ENABLED = False


# Does not really cache anything
CACHES_DUMMY = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
        'TIMEOUT': 100,
    }
}

# In-memory cache, resets when the server restarts
CACHE_LOCMEM = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'wger-cache',
        'TIMEOUT': 100,
    }
}

# Redis cache
CACHE_REDIS = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://localhost:6379/1',
        'TIMEOUT': 5000,
        'OPTIONS': {'CLIENT_CLASS': 'django_redis.client.DefaultClient'},
    }
}


# CACHES = CACHE_REDIS
CACHES = CACHE_LOCMEM
# CACHES = CACHES_DUMMY


# Django Debug Toolbar
# INSTALLED_APPS += ['django_extensions', 'debug_toolbar']
# MIDDLEWARE += ["debug_toolbar.middleware.DebugToolbarMiddleware", ]
# INTERNAL_IPS = ["127.0.0.1", ]

# AUTH_PROXY_HEADER = 'HTTP_X_REMOTE_USER'
# AUTH_PROXY_USER_EMAIL_HEADER = 'HTTP_X_REMOTE_USER_EMAIL'
# AUTH_PROXY_USER_NAME_HEADER = 'HTTP_X_REMOTE_USER_NAME'
# AUTH_PROXY_TRUSTED_IPS = ['127.0.0.1', ]
# AUTH_PROXY_CREATE_UNKNOWN_USER = True


DBCONFIG_PG = {
    'ENGINE': 'django_prometheus.db.backends.postgresql',
    'NAME': 'wger',
    'USER': 'wger',
    'PASSWORD': 'wger',
    'HOST': 'localhost',
    'PORT': '5432',
}


DBCONFIG_SQLITE = {
    'ENGINE': 'django_prometheus.db.backends.sqlite3',
    'NAME': BASE_DIR.parent / 'db.sqlite3',
}

DATABASES = {
    # 'default': DBCONFIG_PG,
    'default': DBCONFIG_SQLITE,
}


# Import other local settings that are not in version control
try:
    from .local_dev_extra import *
except ImportError:
    pass

# Fit Me — LiveU Cloud-Managed Access Control & Hardware Bridge API Key
LIVEU_API_URL = os.environ.get('LIVEU_API_URL', 'https://attapi.liveucloud.com/api/v1')
LIVEU_BRANCH_API_KEY = os.environ.get('LIVEU_BRANCH_API_KEY', '')
ZKBIO_BRIDGE_TOKEN = LIVEU_BRANCH_API_KEY

