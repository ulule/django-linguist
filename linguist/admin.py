# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin
from django.contrib.admin.views.main import ChangeList
from django.utils.translation import ugettext_lazy as _

from .helpers import prefetch_translations

from .models import Translation as LinguistTranslationModel

__all__ = [
    "TranslatableModelChangeListMixin",
    "TranslatableModelChangeList",
    "TranslatableModelAdminMixin",
    "TranslatableModelAdmin",
]


class TranslatableModelChangeListMixin(object):
    def get_results(self, request):
        super(TranslatableModelChangeListMixin, self).get_results(request)
        prefetch_translations(self.result_list)


class TranslatableModelChangeList(TranslatableModelChangeListMixin, ChangeList):
    pass


class TranslatableModelAdminMixin(object):
    """
    Admin class mixin for translatable models.
    """

    def get_object(self, *args, **kwargs):
        obj = super(TranslatableModelAdminMixin, self).get_object(*args, **kwargs)
        if obj:
            obj.prefetch_translations()

        return obj

    def get_changelist(self, request, **kwargs):
        return TranslatableModelChangeList

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
        return '<span class="available-languages">{0}</span>'.format(
            " ".join(languages)
        )

    languages_column.allow_tags = True
    languages_column.short_description = _("Languages")


class TranslatableModelAdmin(TranslatableModelAdminMixin, admin.ModelAdmin):
    """
    Admin class for translatable models.
    """

    pass


class LinguistTranslationModelAdmin(admin.ModelAdmin):
    """
    Linguist Translation admin options.
    """

    list_display = ("identifier", "object_id", "language", "field_name", "field_value")
    list_filter = ("identifier", "language")


admin.site.register(LinguistTranslationModel, LinguistTranslationModelAdmin)
