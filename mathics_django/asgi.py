"""
Mathics3 Django for production use.

This is done using the Django ASGI and Daphne.
"""

import os

from django.core.asgi import get_asgi_application

# Set the default settings module for the 'mathics-django' project.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mathics_django.settings")

# This is the application object used by Daphne
application = get_asgi_application()
