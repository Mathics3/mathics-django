# -*- coding: utf-8 -*-
"""
Module for handling Mathics-style documentation inside Mathics Django.
"""

from mathics.core.load_builtin import import_and_load_builtins

import_and_load_builtins()

# FIXME: should we really do this here?
from mathics_django.doc.django_doc import MathicsDjangoDocumentation

documentation = MathicsDjangoDocumentation()
