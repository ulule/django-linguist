# -*- coding: utf-8 -*-
import json

from django.conf import settings
from django.conf.urls import patterns, include, url
from django.contrib import admin
from django.core import serializers
from django.forms.models import model_to_dict
from django.http import HttpResponse

from .models import FooModel


def home(request):
    obj = FooModel.objects.first()
    return HttpResponse(json.dumps({'title': obj.title}), content_type="application/json")


urlpatterns = patterns('',
    url(r'^i18n/', include('django.conf.urls.i18n')),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^$',  home, name='home')
)
