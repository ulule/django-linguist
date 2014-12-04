# -*- coding: utf-8 -*-
from django.contrib import admin

from .models import Translation


class TranslationAdmin(admin.ModelAdmin):
    pass


admin.site.register(Translation, TranslationAdmin)
