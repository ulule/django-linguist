# -*- coding: utf-8 -*-
from django.contrib import admin

from .models import Translation


class ModelTranslationAdminMixin(object):
    """
    Mixin for model admin classes.
    """
    pass



class TranslationAdmin(admin.ModelAdmin):
    """
    Translation model admin options.
    """
    pass


admin.site.register(Translation, TranslationAdmin)
