# -*- coding: utf-8 -*-
from django.test import TestCase, TransactionTestCase

from exam.cases import Exam
from exam.decorators import fixture, before, after

from ..models import Translation

from . import settings
from .models import FooModel


class Fixtures(Exam):
    """
    Base test class mixin.
    """

    @fixture
    def translated_instance(self):
        m = FooModel()
        for language in self.languages:
            m.activate_language(language)
            m.title = language
            m.save()
        return m

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


class BaseTransactionTestCase(Fixtures, TransactionTestCase):
    pass


class BaseTestCase(Fixtures, TestCase):
    pass
