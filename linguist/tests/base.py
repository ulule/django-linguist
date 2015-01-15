# -*- coding: utf-8 -*-
from django.test import TestCase

from ..models import Translation

from . import settings
from .models import FooModel


class BaseTestCase(TestCase):
    """
    Base test class mixin.
    """

    @property
    def languages(self):
        return [language[0] for language in settings.LANGUAGES]

    @property
    def translation_en(self):
        obj, created = Translation.objects.get_or_create(
            identifier='foo',
            object_id=self.instance.pk,
            language='en',
            field_name='title',
            field_value='Hello')
        return obj

    @property
    def translation_fr(self):
        obj, created = Translation.objects.get_or_create(
            identifier='foo',
            object_id=self.instance.pk,
            language='fr',
            field_name='title',
            field_value='bonjour')
        return obj

    def setup_models(self):
        self.instance = FooModel()
