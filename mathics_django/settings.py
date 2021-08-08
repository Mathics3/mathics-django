# -*- coding: utf-8 -*-

import pkg_resources
import os
import os.path as osp
from mathics.settings import DATA_DIR
from pathlib import Path

DEBUG = True

# set only to True in DEBUG mode
DISPLAY_EXCEPTIONS = True

LOG_QUERIES = False

MATHICS_DJANGO_DB = os.environ.get("MATHICS_DJANGO_DB", "mathics.sqlite")
MATHICS_DJANGO_DB_PATH = os.environ.get(
    "MATHICS_DJANGO_DB_PATH", DATA_DIR + MATHICS_DJANGO_DB
)

ROOT_DIR = pkg_resources.resource_filename("mathics_django", "")

# Location of internal document data.
MATHICS_BACKEND_THREEJS_JSON_PATH = os.path.join(
    ROOT_DIR, "web", "media", "js", "mathics-threejs-backend", "version.json"
)

REQUIRE_LOGIN = False

# Rocky: this is probably a hack. LoadModule[] needs to handle
# whatever it is that setting this thing did.
default_pymathics_modules = []

# Location of internal document data. Currently this is in Python
# Pickle form, but storing this in JSON if possible would be preferable and faster

# We need two versions, one in the user space which is updated with
# local packages installed and is user writable.
DOC_USER_HTML_DATA_PATH = os.environ.get(
    "DOC_USER_HTML_DATA_PATH", osp.join(DATA_DIR, "doc_html_data.pcl")
)

# We need another version as a fallback, and that is distributed with the
# package. It is note user writable and not in the user space.
DOC_SYSTEM_HTML_DATA_PATH = os.environ.get(
    "DOC_SYSTEM_HTML_DATA_PATH", osp.join(ROOT_DIR, "doc", "doc_html_data.pcl")
)


def get_doc_html_data_path(should_be_readable=False, create_parent=False) -> str:
    """Returns a string path where we can find Python Pickle data for HTML
    processing.

    If `should_be_readable` is True, the we will check to see whether this file is
    readable (which also means it exists). If not, we'll return the `DOC_SYSTEM_DATA_PATH`.
    """
    doc_user_html_data_path = Path(DOC_USER_HTML_DATA_PATH)
    base_config_dir = doc_user_html_data_path.parent
    if not base_config_dir.is_dir() and create_parent:
        Path("base_config_dir").mkdir(parents=True, exist_ok=True)

    if should_be_readable:
        return (
            DOC_USER_HTML_DATA_PATH
            if doc_user_html_data_path.is_file()
            else DOC_SYSTEM_HTML_DATA_PATH
        )
    else:
        return DOC_USER_HTML_DATA_PATH


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

# Make this unique, and don't share it with anybody.
SECRET_KEY = "uvbhuiasaeaph6Duh)r@3ex1i@et=0j4h(!p4@!r6s-=a_ev*e"

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
