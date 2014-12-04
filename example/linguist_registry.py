# -*- coding: utf-8 -*-
import linguist

from .models import Post, Category


linguist.register('post', Post)
linguist.register('category', Category)
