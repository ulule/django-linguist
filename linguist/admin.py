# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import django
from django.conf.urls import patterns, url
from django.contrib import admin
from django.contrib.admin.options import csrf_protect_m
from django.contrib.admin.util import unquote
from django.contrib.admin.templatetags.admin_urls import add_preserved_filters
from django.core.urlresolvers import reverse
from django.forms import Media
from django.http import HttpResponseRedirect, Http404
from django.shortcuts import render
from django.utils.encoding import iri_to_uri, force_text
from django.utils.functional import lazy
from django.utils.http import urlencode
from django.utils.translation import ugettext_lazy as _
from django.utils import six

from . import utils

from .models import Translation as LinguistTranslationModel

__all__ = [
    'ModelTranslationAdmin',
]


_lazy_select_template_name = lazy(utils.select_template_name, six.text_type)


class ModelTranslationAdmin(admin.ModelAdmin):

    @property
    def media(self):
        """
        Add Linguist media files.
        """
        return super(ModelTranslationAdmin, self).media + Media(js=['linguist/admin/linguist.js'])

    @property
    def change_form_template(self):
        """
        Overrides ``admin/change_form.html`` template.
        """
        return 'admin/linguist/change_form.html'

    def get_change_form_base_template(self):
        """
        Overrides base change form template.
        """
        opts = self.model._meta
        app_label = opts.app_label
        return _lazy_select_template_name((
            "admin/{0}/{1}/change_form.html".format(app_label, opts.object_name.lower()),
            "admin/{0}/change_form.html".format(app_label),
            "admin/change_form.html"))

    def get_available_languages(self, obj):
        """
        Returns available languages for current object.
        """
        return obj.available_languages if obj is not None else self.model.objects.none()

    def languages_column(self, obj):
        """
        Adds languages columns.
        """
        languages = self.get_available_languages(obj)
        return '<span class="available-languages">{0}</span>'.format(' '.join(languages))

    languages_column.allow_tags = True
    languages_column.short_description = _('Languages')

    def add_view(self, request, form_url='', extra_context=None):
        """
        Adds default language and translatable fields to template context.
        """
        extra_context = extra_context or {}
        extra_context['default_language'] = self.model._linguist.default_language
        extra_context['translatable_fields'] = self.model._linguist.fields
        return super(ModelTranslationAdmin, self).add_view(
            request=request,
            form_url=form_url,
            extra_context=extra_context)

    def change_view(self, request, object_id, form_url='', extra_context=None):
        """
        Adds default language and translatable fields to template context.
        """
        extra_context = extra_context or {}
        extra_context['default_language'] = self.model._linguist.default_language
        extra_context['translatable_fields'] = self.model._linguist.fields
        return super(ModelTranslationAdmin, self).change_view(
            request=request,
            object_id=object_id,
            form_url=form_url,
            extra_context=extra_context)


class LinguistTranslationModelAdmin(admin.ModelAdmin):
    """
    Linguist Translation admin options.
    """
    list_display = ('identifier', 'object_id', 'language', 'field_name', 'field_value')


admin.site.register(LinguistTranslationModel, LinguistTranslationModelAdmin)
