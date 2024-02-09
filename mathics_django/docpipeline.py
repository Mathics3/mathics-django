#!/usr/bin/env python
# -*- coding: utf-8 -*-
# FIXME: combine with same thing in Mathics core
"""
Does 2 things which can either be done independently or
as a pipeline:

1. Extracts tests and runs them from static mdoc files and docstrings from
   Mathics built-in functions
2. Creates/updates internal documentation data
"""

import pickle
from argparse import ArgumentParser
from datetime import datetime

import mathics
import mathics.docpipeline as md
from mathics.core.definitions import Definitions
from mathics.core.load_builtin import import_and_load_builtins
from mathics.doc.utils import open_ensure_dir
from mathics.docpipeline import (
    MAX_TESTS,
    test_all,
    test_chapters,
    test_sections,
    write_doctest_data,
)
from mathics.eval.pymathics import PyMathicsLoadException, eval_LoadModule

from mathics_django.doc import DjangoDocumentation
from mathics_django.settings import get_doctest_html_data_path


def save_doctest_data(output_data):
    """
    Save doctest tests and test results to a Python PCL file.

    ``output_data`` is a dictionary of test results. The key is a tuple
    of:
    * Part name,
    * Chapter name,
    * [Guide Section name],
    * Section name,
    * Subsection name,
    * test number
    and the value is a dictionary of a Result.getdata() dictionary.
    """
    doctest_html_data_path = get_doctest_html_data_path(
        should_be_readable=False, create_parent=True
    )
    print(f"Writing internal document data to {doctest_html_data_path}")
    with open_ensure_dir(doctest_html_data_path, "wb") as output_file:
        pickle.dump(output_data, output_file, 4)


def main():
    import_and_load_builtins()
    md.DEFINITIONS = Definitions(add_builtin=True)

    parser = ArgumentParser(description="Mathics test suite.", add_help=False)
    parser.add_argument(
        "--help", "-h", help="show this help message and exit", action="help"
    )
    parser.add_argument(
        "--version", "-v", action="version", version="%(prog)s " + mathics.__version__
    )
    parser.add_argument(
        "--chapters",
        "-c",
        dest="chapters",
        metavar="CHAPTER",
        help="only test CHAPTER(s). "
        "You can list multiple chapters by adding a comma (and no space) in between chapter names.",
    )
    parser.add_argument(
        "--sections",
        "-s",
        dest="sections",
        metavar="SECTION",
        help="only test SECTION(s). "
        "You can list multiple sections by adding a comma (and no space) in between section names.",
    )
    parser.add_argument(
        "--exclude",
        "-X",
        default="",
        dest="exclude",
        metavar="SECTION",
        help="exclude SECTION(s). "
        "You can list multiple sections by adding a comma (and no space) in between section names.",
    )
    parser.add_argument(
        "--load-module",
        "-l",
        dest="pymathics",
        metavar="MATHIC3-MODULES",
        help="load Mathics3 module MATHICS3-MODULES. "
        "You can list multiple Mathics3 Modules by adding a comma (and no space) in between "
        "module names.",
    )
    parser.add_argument(
        "--logfile",
        "-f",
        dest="logfilename",
        metavar="LOGFILENAME",
        help="stores the output in [logfilename]. ",
    )
    parser.add_argument(
        "--time-each",
        "-d",
        dest="elapsed_times",
        action="store_true",
        help="check the time that take each test to parse, evaluate and compare.",
    )

    parser.add_argument(
        "--output",
        "-o",
        dest="output",
        action="store_true",
        help="generate pickled internal document data",
    )
    parser.add_argument(
        "--reload",
        "-r",
        dest="reload",
        action="store_true",
        help="reload pickled internal data, before possibly adding to it",
    )
    parser.add_argument(
        "--doc-only",
        dest="doc_only",
        action="store_true",
        help="reload pickled internal document data, before possibly adding to it",
    )
    parser.add_argument(
        "--quiet", "-q", dest="quiet", action="store_true", help="hide passed tests"
    )
    parser.add_argument(
        "--keep-going",
        "-k",
        dest="keep_going",
        action="store_true",
        help="create documentation even if there is a test failure",
    )
    parser.add_argument(
        "--stop-on-failure", "-x", action="store_true", help="stop on failure"
    )
    parser.add_argument(
        "--skip",
        metavar="N",
        dest="skip",
        type=int,
        default=0,
        help="skip the first N tests",
    )
    parser.add_argument(
        "--count",
        metavar="N",
        dest="count",
        type=int,
        default=MAX_TESTS,
        help="run only  N tests",
    )
    parser.add_argument(
        "--show-statistics",
        action="store_true",
        help="print cache statistics",
    )
    global LOGFILE

    args = parser.parse_args()

    if args.elapsed_times:
        md.CHECK_PARTIAL_ELAPSED_TIME = True
    # If a test for a specific section is called
    # just test it
    if args.logfilename:
        md.LOGFILE = open(args.logfilename, "wt")

    md.DOCUMENTATION = DjangoDocumentation()

    # LoadModule Mathics3 modules
    if args.pymathics:
        for module_name in args.pymathics.split(","):
            try:
                eval_LoadModule(module_name, md.DEFINITIONS)
            except PyMathicsLoadException:
                print(f"Python module {module_name} is not a Mathics3 module.")

            except ImportError:
                print(f"Python module {module_name} does not exist")
            else:
                print(f"Mathics3 Module {module_name} loaded")

    # md.DOCUMENTATION.load_documentation_sources()

    start_time = None
    total = 0

    if args.sections:
        sections = set(args.sections.split(","))

        start_time = datetime.now()
        test_sections(
            sections,
            stop_on_failure=args.stop_on_failure,
            generate_output=args.output,
            reload=args.reload,
        )
    elif args.chapters:
        start_time = datetime.now()
        chapters = set(args.chapters.split(","))

        total = test_chapters(
            chapters, stop_on_failure=args.stop_on_failure, reload=args.reload
        )
    else:
        if args.doc_only:
            write_doctest_data(
                quiet=args.quiet,
                reload=args.reload,
            )
        else:
            excludes = set(args.exclude.split(","))
            start_at = args.skip + 1
            start_time = datetime.now()
            total = test_all(
                quiet=args.quiet,
                generate_output=args.output,
                stop_on_failure=args.stop_on_failure,
                start_at=start_at,
                doc_even_if_error=args.keep_going,
                excludes=excludes,
            )
            end_time = datetime.now()
            print("Tests took ", end_time - start_time)

    if total > 0 and start_time is not None:
        end_time = datetime.now()
        print("Test evalation took ", end_time - start_time)

    if md.LOGFILE:
        md.LOGFILE.close()


if __name__ == "__main__":
    main()
