"""
Handles "about" section: information about the Mathics Django installation:
configuration information, software information, OS, and machine information.

"""

import json
import os.path as osp
import re
import sys
from builtins import open as builtin_open

from django import __version__ as django_version
from django.conf import settings
from django.shortcuts import render
from mathics import optional_software, version_info as mathics_version_info
from mathics.core.evaluation import Evaluation
from mathics.system_info import mathics_system_info

from mathics_django.settings import DOCTEST_USER_HTML_DATA_PATH, MATHICS_DJANGO_DB_PATH
from mathics_django.version import __version__
from mathics_django.web.models import get_session_evaluation

mathics_threejs_backend_data = {}


def about_page(request):
    """
    This view gives information about the version and software we have loaded.
    """
    evaluation = get_session_evaluation(request.session)
    definitions = evaluation.definitions
    system_info = mathics_system_info(definitions)

    return render(
        request,
        "about.html",
        {
            "BaseDirectory": system_info["$BaseDirectory"],
            "DB_PATH": MATHICS_DJANGO_DB_PATH,
            "DOCTEST_DATA_PATH": DOCTEST_USER_HTML_DATA_PATH,
            "HTTP_USER_AGENT": request.META.get("HTTP_USER_AGENT", ""),
            "HomeDirectory": system_info["$HomeDirectory"],
            "InstallationDirectory": system_info["$InstallationDirectory"],
            "Machine": system_info["$Machine"],
            "MachineName": system_info["$MachineName"],
            "MachinePrecision": system_info["MachinePrecision"],
            "MathJax_version": get_MathJax_version(),
            "MaximumDigitsInString": system_info["MaximumDigitsInString"]
            if system_info["MaximumDigitsInString"] != -1
            else "unlimited",
            "MemoryAvailable": system_info["MemoryAvailable[]"],
            "ProcessID": system_info["$ProcessID"],
            "ProcessorType": system_info["$ProcessorType"],
            "PythonImplementation": system_info["$PythonImplementation"],
            "PythonVersion": sys.version,
            "REMOTE_ADDR": request.META.get("REMOTE_ADDR", ""),
            "REMOTE_HOST": request.META.get("REMOTE_HOST", ""),
            "REMOTE_USER": request.META.get("REMOTE_USER", ""),
            "RootDirectory": system_info["$RootDirectory"],
            "SystemID": system_info["$SystemID"],
            "SystemCharacterEncoding": system_info["SystemCharacterEncoding"],
            "SystemMemory": system_info["$SystemMemory"],
            "SystemTimeZone": f'{system_info["$SystemTimeZone"]} hours from UTC',
            "TemporaryDirectory": system_info["$TemporaryDirectory"],
            "Time12Hour": system_info["Time12Hour"],
            "UserName": system_info["$UserName"],
            "django_version": django_version,
            "mathics_django_version": __version__,
            "mathics_threejs_backend_version": get_mathics_threejs_backend_version(),
            "mathics_version": mathics_version_info["mathics"],
            "mpmath_version": mathics_version_info["mpmath"],
            "numpy_version": mathics_version_info["numpy"],
            "mathics_version_info": mathics_version_info,
            "optional_software": optional_software,
            "python_version": mathics_version_info["python"],
            "settings": settings,
            "sympy_version": mathics_version_info["sympy"],
            "three_js_version": get_threejs_version(),
            "user_settings": get_user_settings(evaluation),
        },
    )


def get_MathJax_version():
    """
    Get the MathJax version the static and hacky way not involving javascript.
    """
    three_file = osp.join(
        osp.normcase(osp.dirname(osp.abspath(__file__))),
        "..",
        "media",
        "js",
        "mathjax",
        "MathJax.js",
    )
    pattern = r'MathJax.version="(\d\.\d\.\d)"'
    match = re.search(pattern, builtin_open(three_file).read())
    if match:
        return match.group(1)
    else:
        return "?.?.?"


def get_mathics_threejs_backend_data():
    """Load mathics-three-package.json. It contains version information."""
    global mathics_threejs_backend_data
    if not mathics_threejs_backend_data:
        try:
            with builtin_open(
                settings.MATHICS_BACKEND_THREEJS_JSON_PATH, "rb"
            ) as version_json_fp:
                mathics_threejs_backend_data = json.load(version_json_fp)
        except Exception:
            pass
    return mathics_threejs_backend_data


def get_mathics_threejs_backend_version():
    return get_mathics_threejs_backend_data().get("version", "??")


def get_threejs_version():
    """
    Get the three.js via information from mathics_threejs_backend's package/version.json.
    """
    return get_mathics_threejs_backend_data().get("threejs_revision", "??")


def get_user_settings(evaluation: Evaluation):
    definitions = evaluation.definitions
    setting_names = sorted(definitions.get_matching_names("Settings`*"))
    user_settings = {}

    evaluation.stopped = False

    for setting_name in setting_names:
        rule = evaluation.parse(setting_name)
        value = rule.evaluate(evaluation).to_python()

        setting_usage_expr = evaluation.parse(setting_name + "::usage")
        setting_usage = setting_usage_expr.evaluate(evaluation).to_python(
            string_quotes=False
        )

        user_settings[setting_name] = {
            "value": value,
            "usage": setting_usage,
            "is_boolean": type(value) is bool,
            "boolean_value": value,
        }

    return user_settings
