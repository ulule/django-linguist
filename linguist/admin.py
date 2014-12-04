# -*- coding: utf-8 -*-
from django.contrib import admin
from django.core.urlresolvers import reverse
from django.utils.html import format_html
from django.utils.translation import ugettext_lazy as _

from .models import Translation


class TranslationAdmin(admin.ModelAdmin):
    pass


admin.site.register(Translation, TranslationAdmin)
