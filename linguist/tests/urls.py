# -*- coding: utf-8 -*-
from django.conf.urls import re_path, include
from django.contrib import admin
from django.http import JsonResponse

from .models import FooModel


def home(request):
    obj = FooModel.objects.first()
    return JsonResponse({"title": obj.title})


urlpatterns = [
    re_path(r"^i18n/", include("django.conf.urls.i18n")),
    re_path(r"^admin/", admin.site.urls),
    re_path(r"^$", home, name="home"),
]
