# -*- coding: utf-8 -*-
"""This module handles the mapping of URI's to
the functions that get called.

All of the callback functions are located in mathics_django.web.views.
"""

from django.conf.urls import url

# These are the callback functions.
from mathics_django.web.views import (
    about_view,
    delete,
    doc,
    doc_chapter,
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
    url(r"^$", main_view),
    url(r"^about(?:\.htm(?:l)?)?$", about_view),
    url(r"^ajax/query/$", query),
    url(r"^ajax/login/$", login),
    url(r"^ajax/logout/$", logout),
    url(r"^ajax/save/$", save),
    url(r"^ajax/open/$", open),
    url(r"^ajax/delete/$", delete),
    url(r"^ajax/getworksheets/$", get_worksheets),
    url(r"^(?P<ajax>(?:ajax/)?)doc/$", doc),
    url(r"^ajax/doc/search/$", doc_search),
    url(r"^(?P<ajax>(?:ajax/)?)doc/(?P<part>[\w-]+)/$", doc_part),
    url(
        r"^(?P<ajax>(?:ajax/)?)doc/(?P<part>[\w-]+)/(?P<chapter>[\w-]+)/$", doc_chapter
    ),
    url(
        r"^(?P<ajax>(?:ajax/)?)doc/(?P<part>[\w-]+)/(?P<chapter>[\w-]+)/"
        r"(?P<section>[$\w-]+)/$",
        doc_section,
    ),
    url(
        r"^(?P<ajax>(?:ajax/)?)doc/(?P<part>[\w-]+)/(?P<chapter>[\w-]+)/"
        r"(?P<section>[$\w-]+)/(?P<subsection>[$\w-]+)/$",
        doc_subsection,
    ),
]
