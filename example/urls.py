# -*- coding: utf-8 -*-
from django.conf import settings
from django.conf.urls import patterns, include, url
from django.contrib import admin
from  django.views.generic import TemplateView


urlpatterns = patterns('',
    url(r'^admin/', include(admin.site.urls)),
    url(r'^$', TemplateView.as_view(template_name='home.html'), name='home')
)
