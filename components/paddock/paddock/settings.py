"""
Django settings for paddock project.

Generated by 'django-admin startproject' using Django 4.1.3.

For more information on this file, see
https://docs.djangoproject.com/en/4.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.1/ref/settings/

For configuration see
https://django-environ.readthedocs.io/en/latest/quickstart.html
https://djangostars.com/blog/configuring-django-settings-best-practices/
https://www.architect.io/blog/2022-08-04/deploy-python-django-kubernetes/
"""

import environ
import os
from pathlib import Path

env = environ.Env(
    # set casting, default value
    DEBUG=(bool, False),
    LOGGING_DB_LEVEL=(str, "INFO"),
)

# Set the project base directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Take environment variables from .env file
environ.Env.read_env(os.path.join(BASE_DIR, ".env"))

# False if not in os.environ because of casting above
DEBUG = env("DEBUG")

# Raises Django's ImproperlyConfigured
# exception if SECRET_KEY not in os.environ
SECRET_KEY = env("SECRET_KEY")

ALLOWED_HOSTS = [
    "127.0.0.1",
    "localhost",
    "paddock.b4mad.racing",
    os.environ.get("ALLOWED_HOST", ""),
]


# Application definition

INSTALLED_APPS = [
    "telemetry.apps.TelemetryConfig",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "explorer",
    "django_plotly_dash.apps.DjangoPlotlyDashConfig",
    "bootstrap4",
    "dpd_static_support",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django_plotly_dash.middleware.BaseMiddleware",
    "django_plotly_dash.middleware.ExternalRedirectionMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "paddock.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            os.path.join(BASE_DIR, "paddock", "templates"),
        ],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "paddock.wsgi.application"


# Database
# https://docs.djangoproject.com/en/4.1/ref/settings/#databases

# Parse database connection url strings
# like psql://user:pass@127.0.0.1:8458/db
DATABASES = {
    # read os.environ['DATABASE_URL'] and raises
    # ImproperlyConfigured exception if not found
    #
    "default": env.db_url("DATABASE_URL"),
    "readonly": env.db_url("READONLY_DATABASE_URL"),
}

# DATABASES = {
#     "sqlite3": {
#         "ENGINE": "django.db.backends.sqlite3",
#         "NAME": BASE_DIR / "db.sqlite3",
#     },
#     "default": {
#         "ENGINE": "django.db.backends.postgresql",
#         "NAME": os.getenv("DB_DATABASE"),
#         "USER": os.getenv("DB_USER"),
#         "PASSWORD": os.getenv("DB_PASSWORD"),
#         "HOST": os.getenv("DB_ADDR"),
#         "PORT": os.getenv("DB_PORT", 5432),
#     },
# }


# Password validation
# https://docs.djangoproject.com/en/4.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

CSRF_TRUSTED_ORIGINS = ["https://*.b4mad.racing"]

# Internationalization
# https://docs.djangoproject.com/en/4.1/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.1/howto/static-files/

STATIC_URL = "static/"
STATIC_ROOT = os.path.join(BASE_DIR, "static/")
STATICFILES_FINDERS = [
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
    "django_plotly_dash.finders.DashAssetFinder",
    "django_plotly_dash.finders.DashComponentFinder",
    "django_plotly_dash.finders.DashAppDirectoryFinder",
]
STATICFILES_DIRS = [
    BASE_DIR / "paddock/assets/",
]

# Default primary key field type
# https://docs.djangoproject.com/en/4.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LOGGING = {
    "disable_existing_loggers": False,
    "version": 1,
    "formatters": {
        "timestamp": {
            "format": "{asctime} {levelname} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            # logging handler that outputs log messages to terminal
            "class": "logging.StreamHandler",
            "level": "DEBUG",  # message level to be written to console
            "formatter": "timestamp",
        },
    },
    "loggers": {
        "": {
            # this sets root level logger to log debug and higher level
            # logs to console. All other loggers inherit settings from
            # root level logger.
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": False,  # this tells logger to send logging message
            # to its parent (will send if set to True)
        },
        "django.db": {
            # django also has database level logging
            "level": env("LOGGING_DB_LEVEL")
        },
    },
}

EXPLORER_CONNECTIONS = {"Default": "readonly"}
EXPLORER_DEFAULT_CONNECTION = "readonly"

# for plotly dash
X_FRAME_OPTIONS = "SAMEORIGIN"
PLOTLY_DASH = {
    # Route used for the message pipe websocket connection
    "ws_route": "dpd/ws/channel",
    # Route used for direct http insertion of pipe messages
    "http_route": "dpd/views",
    # Flag controlling existince of http poke endpoint
    "http_poke_enabled": True,
    # Insert data for the demo when migrating
    "insert_demo_migrations": False,
    # Timeout for caching of initial arguments in seconds
    "cache_timeout_initial_arguments": 60,
    # Name of view wrapping function
    "view_decorator": None,
    # Flag to control location of initial argument storage
    "cache_arguments": False,
    # Flag controlling local serving of assets
    "serve_locally": False,
}


# Plotly components containing static content that should
# be handled by the Django staticfiles infrastructure

PLOTLY_COMPONENTS = [
    # Common components (ie within dash itself) are automatically added
    # django-plotly-dash components
    "dpd_components",
    # static support if serving local assets
    "dpd_static_support",
    # Other components, as needed
    "dash_bootstrap_components",
]
