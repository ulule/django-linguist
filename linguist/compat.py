# -*- coding: utf-8 -*-
import django
from django.conf import settings

__all__ = ['get_user_model']


if django.VERSION >= (1, 5):
    from django.contrib.auth import get_user_model
else:
    from django.contrib.auth.models import User

    def get_user_model():
        return User

AUTH_USER_MODEL = getattr(settings, 'AUTH_USER_MODEL', 'auth.User')
