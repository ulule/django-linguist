# -*- coding: utf-8 -*-
import os
import django

BASE_PATH = os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir)
)

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql_psycopg2",
        "NAME": "django_linguist",
        "USER": "postgres",
        "PASSWORD": "",
        "HOST": "",
    }
}

SITE_ID = 1
DEBUG = True

MIDDLEWARE_CLASSES = (
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
)

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.sites",
    "linguist",
    "linguist.tests",
]

SECRET_KEY = "blabla"

ROOT_URLCONF = "linguist.tests.urls"

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s"
        }
    },
    "handlers": {
        "stream": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        }
    },
    "loggers": {
        "django.request": {"handlers": ["stream"], "level": "DEBUG", "propagate": True},
        "linguist": {"handlers": ["stream"], "level": "DEBUG", "propagate": True},
    },
}

ugettext = lambda s: s

LANGUAGE_CODE = "en"

LANGUAGES = (
    ("en", ugettext(u"English")),
    ("de", ugettext(u"German")),
    ("fr", ugettext(u"French")),
    ("es", ugettext(u"Spanish")),
    ("it", ugettext(u"Italian")),
    ("pt", ugettext(u"Portuguese")),
)

if django.VERSION <= (1, 6):
    TEST_RUNNER = "discover_runner.DiscoverRunner"
