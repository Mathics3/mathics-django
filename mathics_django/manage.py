#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sys

from django.core.management import execute_from_command_line


def main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mathics_django.settings")
    if len(sys.argv) == 1:
        sys.argv.append("runserver")
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
