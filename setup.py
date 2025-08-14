#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Setuptools based setup script for the Django front end to Mathics.

For the easiest installation just type the following command (you'll probably
need root privileges):

    python setup.py install

This will install the library in the default location. For instructions on
how to customize the install procedure read the output of:

    python setup.py --help install

In addition, there are some other commands:

    python setup.py clean -> will clean all trash (*.pyc and stuff)

To get a full list of available commands, read the output of:

    python setup.py --help-commands

Or, if all else fails, feel free to write to the mathics users list at
mathics-users@googlegroups.com and ask for help.
"""

import os.path as osp
import platform
import re
import sys

from setuptools import Command, setup


def get_srcdir():
    filename = osp.normcase(osp.dirname(osp.abspath(__file__)))
    return osp.realpath(filename)


def read(*rnames):
    return open(osp.join(get_srcdir(), *rnames)).read()


# stores __version__ in the current namespace
exec(
    compile(
        open("mathics_django/version.py").read(), "mathics_django/version.py", "exec"
    )
)

# Get/set VERSION and long_description from files
long_description = read("README.rst") + "\n"


is_PyPy = platform.python_implementation() == "PyPy" or hasattr(
    sys, "pypy_version_info"
)

DEPENDENCY_LINKS = []
INSTALL_REQUIRES = []

if sys.platform == "darwin":
    INSTALL_REQUIRES += ["scikit-image"]

# General Requirements
INSTALL_REQUIRES += [
    "Mathics-Scanner >=1.4.1",
    # "Mathics3 @ http://github.com/Mathics3/mathics-core/archive/master.zip",
    "Mathics3 >=8.0.0",
    "django",
    "matplotlib",  # For networkx graphs
    "networkx >= 3.0",
    "pygments",  # For colorized Python tracebacks
    "requests",
]


def subdirs(root, file="*.*", depth=10):
    for k in range(depth):
        yield root + "*/" * k + file


class initialize(Command):
    """
    Manually create the Django database used by the web notebook
    """

    description = "manually create the Django database used by the web notebook"
    user_options = []  # distutils complains if this is not here.

    def __init__(self, *args):
        self.args = args[0]  # so we can pass it to other classes
        Command.__init__(self, *args)

    def initialize_options(self):  # distutils wants this
        pass

    def finalize_options(self):  # this too
        pass

    def run(self):
        import os
        import subprocess

        settings = {}
        exec(
            compile(
                open("mathics_django/settings.py").read(),
                "mathics-django/settings.py",
                "exec",
            ),
            settings,
        )

        database_file = settings["DATABASES"]["default"]["NAME"]
        print("Creating data directory %s" % settings["DATA_DIR"])
        if not osp.exists(settings["DATA_DIR"]):
            os.makedirs(settings["DATA_DIR"])
        print("Creating database %s" % database_file)
        try:
            subprocess.check_call(
                [sys.executable, "mathics_django/manage.py", "migrate", "--noinput"]
            )
            print("")
            print("Database created successfully.")
        except subprocess.CalledProcessError:
            print("Error: failed to create database")
            sys.exit(1)


mathjax_files = list(subdirs("media/js/mathjax/"))

extra_requires = []
for line in open("requirements-full.txt").read().split("\n"):
    if line and not line.startswith("#"):
        requires = re.sub(r"([^#]+)(\s*#.*$)?", r"\1", line)
        extra_requires.append(requires)

EXTRA_REQUIRES = {"full": extra_requires}

setup(
    name="Mathics-Django",
    version=__version__,
    packages=[
        "mathics_django",
        "mathics_django.doc",
        "mathics_django.web",
        "mathics_django.web.controllers",
        "mathics_django.web.templatetags",
        "mathics_django.web.migrations",
    ],
    install_requires=INSTALL_REQUIRES,
    extras_require=EXTRA_REQUIRES,
    dependency_links=DEPENDENCY_LINKS,
    package_data={
        "mathics_django": ["autoload/*.m"],
        "mathics_django.doc": ["*.pcl"],
        "mathics_django.web": [
            "media/css/*.css",
            "media/img/*.*",
            "media/fonts/*",
            "media/img/favicons/*",
            "media/js/innerdom/*.js",
            "media/js/mathics-threejs-backend/*",
            "media/js/prototype/*.js",
            "media/js/scriptaculous/*.js",
            "media/js/*.js",
            "templates/*.html",
            "templates/doc/*.html",
        ]
        + mathjax_files,
    },
    entry_points={
        "console_scripts": [
            "mathicsserver = mathics_django.server:main",
        ],
    },
    long_description=long_description,
    long_description_content_type="text/x-rst",
    # don't pack Mathics in egg because of media files, etc.
    zip_safe=False,
    # metadata for upload to PyPI
    maintainer="Mathics3 Group",
    maintainer_email="mathics-devel@googlegroups.com",
    description="A Django front end for Mathics3.",
    license="GPL",
    url="https://mathics.org/",
    keywords=["Mathematica", "Wolfram", "Interpreter", "Shell", "Math", "CAS"],
    classifiers=[
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Programming Language :: Python :: Implementation :: CPython",
        "Programming Language :: Python :: Implementation :: PyPy",
        "Topic :: Scientific/Engineering",
        "Topic :: Scientific/Engineering :: Mathematics",
        "Topic :: Scientific/Engineering :: Physics",
        "Topic :: Software Development :: Interpreters",
    ],
    # TODO: could also include long_description, download_url,
)
