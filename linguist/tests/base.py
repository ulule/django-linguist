# -*- coding: utf-8 -*-
from django.test import TestCase

from ..registry import LinguistRegistry as Registry
from ..models import Translation

from . import settings
from .translations import FooModel, FooTranslation


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

    def create_registry(self):
        self.registry = Registry()
        self.registry.register(FooTranslation)
        self.instance = FooModel()
        self.instance.save()
