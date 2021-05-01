#!/usr/bin/env python3
# -*- coding: utf-8 -*-


from django.conf.urls import url
from mathics_django.web.views import (
    about_view,
    delete,
    doc,
    doc_chapter,
    doc_part,
    doc_search,
    doc_section,
    get_worksheets,
    login,
    logout,
    main_view,
    open,
    query,
    save,
)

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
]
