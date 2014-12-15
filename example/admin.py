# -*- coding: utf-8 -*-
from django.contrib import admin

from linguist.admin import ModelTranslationAdminMixin

from .models import Post, Category


class PostAdmin(admin.ModelAdmin, ModelTranslationAdminMixin):
    list_display = ('title', 'body', 'created_at')


class CategoryAdmin(admin.ModelAdmin, ModelTranslationAdminMixin):
    list_display = ('name', 'created_at')


admin.site.register(Post, PostAdmin)
admin.site.register(Category, CategoryAdmin)
