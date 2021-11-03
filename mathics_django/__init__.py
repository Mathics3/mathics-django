# -*- coding: utf-8 -*-

import sympy
import mpmath
import django

from mathics import version_info


version_info["django"] = django.__version__

version_string = """Mathics {mathics}
on {python}
using SymPy {sympy}, mpmath {mpmath}""".format(
    **version_info
)


server_version_string = version_string + ", django {django}".format(**version_info)

if "cython" in version_info:
    server_version_string += f", cython {version_info['cython']}"
    version_string += f", cython {version_info['cython']}"

license_string = """\
Copyright (C) 2011-2021 The Mathics Team.
This program comes with ABSOLUTELY NO WARRANTY.
This is free software, and you are welcome to redistribute it
under certain conditions.
See the documentation for the full license."""
