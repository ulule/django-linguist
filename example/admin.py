# -*- coding: utf-8 -*-
from django.contrib import admin

from linguist.admin import ModelTranslationAdminMixin

from .models import Post, Category


class PostAdmin(admin.ModelAdmin, ModelTranslationAdminMixin):
    pass


class CategoryAdmin(admin.ModelAdmin, ModelTranslationAdminMixin):
    pass


admin.site.register(Post, PostAdmin)
admin.site.register(Category, CategoryAdmin)
