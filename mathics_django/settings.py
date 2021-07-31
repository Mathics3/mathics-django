# -*- coding: utf-8 -*-

import pkg_resources
import os
from mathics.settings import DATA_DIR, ROOT_DIR

DEBUG = True

# set only to True in DEBUG mode
DISPLAY_EXCEPTIONS = True

# Location of internal document data.
DOC_DATA_PATH = os.path.join(DATA_DIR, "doc_html_data.pcl")

LOG_QUERIES = False

# Location of internal document data.
MATHICS_BACKEND_THREEJS_JSON_PATH = os.path.join(
    ROOT_DIR, "web", "media", "js", "mathics-threejs-backend", "version.json"
)

MATHICS_DJANGO_DB = os.environ.get("MATHICS_DJANGO_DB", "mathics.sqlite")
MATHICS_DJANGO_DB_PATH = os.environ.get(
    "MATHICS_DJANGO_DB_PATH", DATA_DIR + MATHICS_DJANGO_DB
)

REQUIRE_LOGIN = False

ROOT_DIR = pkg_resources.resource_filename("mathics_django", "")

# Rocky: this is probably a hack. LoadModule[] needs to handle
# whatever it is that setting this thing did.
default_pymathics_modules = []

#########################################################
# Django-specific settings
# See https://docs.djangoproject.com/en/3.2/ref/settings/
##########################################################

AUTHENTICATION_BACKENDS = ("mathics.web.authentication.EmailModelBackend",)

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": MATHICS_DJANGO_DB_PATH,
    }
}


DEBUG_PROPAGATE_EXCEPTIONS = True

# if REQUIRE_LOGIN is True be sure to set up an email sender:
EMAIL_HOST = "smtp.sendgrid.net"
EMAIL_HOST_USER = "mathics"
EMAIL_HOST_PASSWORD = ""
EMAIL_PORT = 587
EMAIL_USE_TLS = True

INSTALLED_APPS = (
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.sites",
    "mathics_django.web",
)

LANGUAGE_CODE = "en-us"

# List of callables that know how to import templates from various sources.
# TEMPLATE_LOADERS = (
#    'django.template.loaders.filesystem.load_template_source',
#    'django.template.loaders.app_directories.load_template_source',
# )

MIDDLEWARE = [
    "django.middleware.common.CommonMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
]

ROOT_URLCONF = "mathics_django.urls"

SITE_ID = 1

# Absolute path to the directory that holds static files.
STATIC_ROOT = os.path.join(ROOT_DIR, "web/media/")

# URL that handles the media served from STATIC_ROOT.
STATIC_URL = "/media/"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(ROOT_DIR, "web/templates/")],
        "OPTIONS": {
            "debug": DEBUG,
        },
    }
]

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True
