# -*- coding: utf-8 -*-
from django.test import TestCase

from exam.cases import Exam
from exam.decorators import fixture, before, after

from ..models import Translation

from . import settings
from .models import FooModel


class BaseTestCase(Exam, TestCase):
    """
    Base test class mixin.
    """

    @property
    def languages(self):
        return [language[0] for language in settings.LANGUAGES]

    @fixture
    def translation_en(self):
        return Translation.objects.create(identifier='foo',
                                          object_id=self.instance.pk,
                                          language='en',
                                          field_name='title',
                                          field_value='Hello')

    @fixture
    def translation_fr(self):
        return Translation.objects.create(identifier='foo',
                                          object_id=self.instance.pk,
                                          language='fr',
                                          field_name='title',
                                          field_value='bonjour')

    @before
    def setup_models(self):
        self.instance = FooModel()

        self.instance.clear_translations_cache()

    @after
    def clear_cache(self):
        self.instance.clear_translations_cache()
