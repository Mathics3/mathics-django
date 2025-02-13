# -*- coding: utf-8 -*-


from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, re_path

handler404 = "mathics_django.web.views.error_404_view"
handler500 = "mathics_django.web.views.error_500_view"

urlpatterns = [
    # url(''),
    re_path(r"^", include("mathics_django.web.urls")),
    re_path(r"^"+settings.BASE_URL, include("mathics_django.web.urls")),
    re_path(r"^"+settings.BASE_URL+"/", include("mathics_django.web.urls")),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
