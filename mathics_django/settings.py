# -*- coding: utf-8 -*-

import os
import os.path as osp
from pathlib import Path

import pkg_resources
from mathics.settings import DATA_DIR

# The kinds of strings in an environment variable be interpreted as True.
ENV_VAR_YES_VALUE = ("true", "t", "1", "yes", "y")


def get_bool_from_environment(env_var: str, default_value: str):
    """
    Read environment variable ``env_var``, and turn that into a
    boolean which is returned.
    ``default_value`` is the value to use if ``env_var`` is not
    set as an environment variable
    """
    env_var_value = os.environ.get(env_var, default_value)
    return env_var_value in ENV_VAR_YES_VALUE


DEBUG = get_bool_from_environment("MATHICS_DJANGO_DEBUG", "true")

# The environment variable MATHICS_DJANGO_ALLOWED_HOSTS is used
# to set Django's ALLOWED_HOST, which specifies what kinds of
# host/domain names that Django can serve.
# See:
#   https://docs.djangoproject.com/en/4.1/ref/settings/#allowed-hosts
# for details
allowed_host_list = os.environ.get("MATHICS_DJANGO_ALLOWED_HOSTS", None)
if allowed_host_list is not None:
    ALLOWED_HOSTS = allowed_host_list.split(";")
else:
    # Use Django's default value for ALLOWED_HOSTS.
    ALLOWED_HOSTS = []

DISPLAY_EXCEPTIONS = get_bool_from_environment(
    "MATHICS_DJANGO_DISPLAY_EXCEPTIONS", DEBUG
)

# Setting this to True causes Django to freak out. Figure out why and fix.
LOG_QUERIES = False

# Show on Django console:
# * evaluation timeout
# * results
LOG_ON_CONSOLE = get_bool_from_environment("MATHICS_DJANGO_LOG_ON_CONSOLE", "false")

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

# Location of internal document data. Currently this is in Python
# Pickle form, but storing this in JSON if possible would be
# preferable and faster

# We need two versions, one in the user space which is updated with
# local packages installed and is user writable.
DOCTEST_USER_HTML_DATA_PATH = os.environ.get(
    "DOCTEST_USER_HTML_DATA_PATH", osp.join(DATA_DIR, "doc_html_data.pcl")
)

# We need another version as a fallback, and that is distributed with the
# package. It is note user writable and not in the user space.
DOC_SYSTEM_HTML_DATA_PATH = os.environ.get(
    "DOC_SYSTEM_HTML_DATA_PATH", osp.join(ROOT_DIR, "doc", "doc_html_data.pcl")
)


def get_doctest_html_data_path(should_be_readable=False, create_parent=False) -> str:
    """Returns a string path where we can find Python Pickle data for HTML
    processing.

    If `should_be_readable` is True, the we will check to see whether this file is
    readable (which also means it exists). If not, we'll return the `DOC_SYSTEM_DATA_PATH`.
    """
    doc_user_html_data_path = Path(DOCTEST_USER_HTML_DATA_PATH)
    base_config_dir = doc_user_html_data_path.parent
    if not base_config_dir.is_dir() and create_parent:
        Path("base_config_dir").mkdir(parents=True, exist_ok=True)

    if should_be_readable:
        return (
            DOCTEST_USER_HTML_DATA_PATH
            if doc_user_html_data_path.is_file()
            else DOC_SYSTEM_HTML_DATA_PATH
        )
    else:
        return DOCTEST_USER_HTML_DATA_PATH


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
    "mathics_django.web.controllers",
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
