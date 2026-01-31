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
import sys
from datetime import datetime

from mathics.core.load_builtin import import_and_load_builtins
from mathics.doc.utils import open_ensure_dir
from mathics.docpipeline import (
    DocTestPipeline,
    build_arg_parser,
    test_all,
    test_chapters,
    test_sections,
    write_doctest_data,
)
from mathics.timing import show_lru_cache_statistics

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
    args = build_arg_parser()
    data_path = (
        get_doctest_html_data_path(should_be_readable=False, create_parent=True)
        if args.output
        else None
    )
    test_pipeline = DocTestPipeline(args, output_format="xml", data_path=data_path)
    test_status = test_pipeline.status

    if args.sections:
        include_sections = set(args.sections.split(","))
        exclude_subsections = set(args.exclude.split(","))
        start_time = datetime.now()
        test_sections(test_pipeline, include_sections, exclude_subsections)
    elif args.chapters:
        start_time = datetime.now()
        include_chapters = set(args.chapters.split(","))
        exclude_sections = set(args.exclude.split(","))
        test_chapters(test_pipeline, include_chapters, exclude_sections)
    else:
        if args.doc_only:
            write_doctest_data(test_pipeline)
        else:
            excludes = set(args.exclude.split(","))
            start_time = datetime.now()
            test_all(test_pipeline, excludes=excludes)

    if test_status.total > 0 and start_time is not None:
        print("Test evaluation took ", datetime.now() - start_time)

    if test_pipeline.logfile:
        test_pipeline.logfile.close()
    if args.show_statistics:
        show_lru_cache_statistics()

    if test_status.failed == 0:
        print("\nOK")
    else:
        print("\nFAILED")
        sys.exit(1)  # Travis-CI knows the tests have failed


if __name__ == "__main__":
    import_and_load_builtins()    
    main()
