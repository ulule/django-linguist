# -*- coding: utf-8 -*-
import linguist

from .models import Post, Category


class CategoryTranslation(linguist.ModelTranslationBase):
    model = Category
    identifier = 'category'
    fields = ('name', )


class PostTranslation(linguist.ModelTranslationBase):
    model = Post
    identifier = 'post'
    fields = ('title', 'body', )


linguist.register(CategoryTranslation)
linguist.register(PostTranslation)
