# -*- coding: utf-8 -*-
from django.contrib import admin

from linguist.admin import ModelTranslationAdmin

from .models import Post, Category


class PostAdmin(ModelTranslationAdmin):
    list_display = ('title', 'body', 'languages_column', 'created_at')


class CategoryAdmin(ModelTranslationAdmin):
    list_display = ('name', 'created_at')


admin.site.register(Post, PostAdmin)
admin.site.register(Category, CategoryAdmin)
