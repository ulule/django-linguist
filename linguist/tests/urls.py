# -*- coding: utf-8 -*-
from django.conf.urls import include, url
from django.contrib import admin
from django.http import JsonResponse

from .models import FooModel


def home(request):
    obj = FooModel.objects.first()
    return JsonResponse({"title": obj.title})


urlpatterns = [
    url(r"^i18n/", include("django.conf.urls.i18n")),
    url(r"^admin/", admin.site.urls),
    url(r"^$", home, name="home"),
]
