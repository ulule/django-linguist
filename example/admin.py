# -*- coding: utf-8 -*-
from django.contrib import admin

from linguist.admin import ModelTranslationAdmin

from .models import (Post,
                     Category,
                     Bookmark,
                     BookmarkTranslation)


class PostAdmin(ModelTranslationAdmin):
    list_display = ('title', 'body', 'languages_column', 'created_at')


class CategoryAdmin(ModelTranslationAdmin):
    list_display = ('name', 'languages_column', 'created_at')


class BookmarkAdmin(ModelTranslationAdmin):
    list_display = ('title', 'url', 'description', 'languages_column', 'created_at')


class BookmarkTranslationAdmin(admin.ModelAdmin):
    list_display = ('identifier', 'object_id', 'language', 'field_name', 'field_value')


admin.site.register(Post, PostAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(Bookmark, BookmarkAdmin)
admin.site.register(BookmarkTranslation, BookmarkTranslationAdmin)
