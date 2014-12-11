# -*- coding: utf-8 -*-
from django.test import TestCase
from django.test.utils import override_settings

from ..registry import LinguistRegistry as Registry

from . import settings

from .translations import (
    FooModel,
    FooTranslation
)


LANGUAGES = [l[0] for l in settings.LANGUAGES]

@override_settings(DEBUG=True)
class MethodsTest(TestCase):
    """
    Tests Linguist custom model instance methods.
    """

    def setUp(self):
        self.registry = Registry()
        self.registry.register(FooTranslation)
        self.instance = FooModel()

    def test_get_current_language(self):
        self.assertTrue(hasattr(self.instance, 'get_current_language'))
        self.assertEqual(self.instance.get_current_language(), 'en')

    def test_set_current_language(self):
        self.assertTrue(hasattr(self.instance, 'set_current_language'))
        self.instance.set_current_language('fr')
        self.assertEqual(self.instance.get_current_language(), 'fr')

    def test_linguist_clear_cache(self):
        self.assertTrue(hasattr(self.instance, 'linguist_clear_cache'))
        self.instance.set_current_language('fr')
        self.assertEqual(self.instance.get_current_language(), 'fr')
        self.instance.linguist_clear_cache()
        self.assertEqual(self.instance._linguist, {})
        self.assertEqual(self.instance.get_current_language(), 'en')

    def test_prefetch_translations(self):
        self.assertTrue(hasattr(self.instance, 'prefetch_translations'))

        with self.assertNumQueries(5):
            self.instance.save()
            self.instance.title_en = 'Hello'
            self.instance.title_fr = 'Bonjour'

        with self.assertNumQueries(0):
            string = '%s %s' % (self.instance.title_fr, self.instance.title_en)

        self.instance.linguist_clear_cache()
        with self.assertNumQueries(2):
             string = '%s %s' % (self.instance.title_fr, self.instance.title_en)

        self.instance.linguist_clear_cache()
        self.instance.prefetch_translations()
        with self.assertNumQueries(0):
             string = '%s %s' % (self.instance.title_fr, self.instance.title_en)
