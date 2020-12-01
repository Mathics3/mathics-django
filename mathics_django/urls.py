#!/usr/bin/env python3
# -*- coding: utf-8 -*-


from django.conf.urls import url, include
from django.conf.urls.static import static
from django.conf import settings

handler404 = 'mathics_django.web.views.error_404_view'
handler500 = 'mathics_django.web.views.error_500_view'

urlpatterns = [
    # url(''),
    url(r'^', include('mathics_django.web.urls')),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
