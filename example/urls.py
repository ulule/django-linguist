# -*- coding: utf-8 -*-
from django.conf import settings
from django.conf.urls import patterns, include, url
from django.contrib import admin
from django.http import JsonResponse

def home(request):
    return JsonResponse({"message": "hello"})


urlpatterns = patterns('',
    url(r'^admin/', include(admin.site.urls)),
    url(r'^$',  home, name='home')
)
