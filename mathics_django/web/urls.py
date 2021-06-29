#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""This module handles the mapping of URI's to
the functions that get called.

All of the callback functions are located in mathics_django.web.views.
"""

from django.conf.urls import url

# These ae the callback functions.
from mathics_django.web.views import (
    about_view,
    delete,
    doc,
    doc_chapter,
    doc_guide_section,
    doc_part,
    doc_search,
    doc_section,
    doc_subsection,
    get_worksheets,
    login,
    logout,
    main_view,
    open,
    query,
    save,
)

# These patterns map URI's a function to call to generate HTML output.
# Note that although what we have here are URIs not URLs.
urlpatterns = [
    # 'mathics.web.views',
    url("^$", main_view),
    url("^about(?:\.htm(?:l)?)?$", about_view),
    url("^ajax/query/$", query),
    url("^ajax/login/$", login),
    url("^ajax/logout/$", logout),
    url("^ajax/save/$", save),
    url("^ajax/open/$", open),
    url("^ajax/delete/$", delete),
    url("^ajax/getworksheets/$", get_worksheets),
    url("^(?P<ajax>(?:ajax/)?)doc/$", doc),
    url("^ajax/doc/search/$", doc_search),
    url("^(?P<ajax>(?:ajax/)?)doc/(?P<part>[\w-]+)/$", doc_part),
    url("^(?P<ajax>(?:ajax/)?)doc/(?P<part>[\w-]+)/(?P<chapter>[\w-]+)/$", doc_chapter),
    url(
        "^(?P<ajax>(?:ajax/)?)doc/(?P<part>[\w-]+)/(?P<chapter>[\w-]+)/"
        "(?P<section>[$\w-]+)/$",
        doc_section,
    ),
    url(
        "^(?P<ajax>(?:ajax/)?)doc/(?P<part>[\w-]+)/(?P<chapter>[\w-]+)/"
        "(?P<section>[$\w-]+)/(?P<subsection>[$\w-]+)/$",
        doc_subsection,
    ),
]
