# -*- coding: utf-8 -*-
from django.test import TestCase
from django.test.utils import override_settings

from ..registry import LinguistRegistry as Registry
from . import settings
from .translations import FooModel, FooTranslation


LANGUAGES = [l[0] for l in settings.LANGUAGES]

@override_settings(DEBUG=True)
class LinguistMixinTest(TestCase):
    """
    Tests Linguist mixin.
    """

    def setUp(self):
        self.registry = Registry()
        self.registry.register(FooTranslation)
        self.instance = FooModel()

    def test_identifier(self):
        self.assertTrue(hasattr(self.instance, 'identifier'))
        self.assertEqual(self.instance.identifier, 'foo')

    def test_language(self):
        self.assertTrue(hasattr(self.instance, 'language'))
        self.assertEqual(self.instance.language, 'en')
        self.instance.language = 'fr'
        self.assertEqual(self.instance.language, 'fr')

    def test_get_translations(self):
        self.assertTrue(hasattr(self.instance, 'get_translations'))
        self.assertEqual(len(self.instance.get_translations()), 1)
        self.instance.language = 'fr'
        self.instance.title = 'Bonjour'
        self.assertEqual(len(self.instance.get_translations()), 2)

    def test_clear_translations_cache(self):
        self.assertTrue(hasattr(self.instance, 'clear_translations_cache'))
        self.instance.language = 'fr'
        self.assertEqual(self.instance.language, 'fr')
        self.instance.clear_translations_cache()
        self.assertEqual(self.instance._linguist, {})
        self.assertEqual(self.instance.language, 'en')

    def test_prefetch_translations(self):
        self.assertTrue(hasattr(self.instance, 'prefetch_translations'))

        with self.assertNumQueries(5):
            self.instance.save()
            self.instance.title_en = 'Hello'
            self.instance.title_fr = 'Bonjour'

        with self.assertNumQueries(0):
            string = '%s %s' % (self.instance.title_fr, self.instance.title_en)

        self.instance.clear_translations_cache()
        with self.assertNumQueries(2):
             string = '%s %s' % (self.instance.title_fr, self.instance.title_en)

        self.instance.clear_translations_cache()
        self.instance.prefetch_translations()
        with self.assertNumQueries(0):
             string = '%s %s' % (self.instance.title_fr, self.instance.title_en)
