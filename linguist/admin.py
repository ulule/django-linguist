# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin
from django.utils.translation import ugettext_lazy as _

from .models import Translation as LinguistTranslationModel

__all__ = [
    'ModelTranslationAdminMixin',
    'ModelTranslationAdmin',
]


class ModelTranslationAdminMixin(object):
    """
    Admin class mixin for translatable models.
    """

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


class ModelTranslationAdmin(ModelTranslationAdminMixin, admin.ModelAdmin):
    """
    Admin class for translatable models.
    """
    pass


class LinguistTranslationModelAdmin(admin.ModelAdmin):
    """
    Linguist Translation admin options.
    """
    list_display = ('identifier', 'object_id', 'language', 'field_name', 'field_value')


admin.site.register(LinguistTranslationModel, LinguistTranslationModelAdmin)
