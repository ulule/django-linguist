# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from .base import BaseTestCase

from .translations import FooModel


class ManagerMixinTest(BaseTestCase):
    """
    Tests the Linguist's manager mixin.
    """

    def setUp(self):
        self.create_registry()

    def test_with_translations(self):
        self.assertTrue(hasattr(FooModel.objects, 'with_translations'))
        self.instance.language = 'en'
        self.instance.title = 'Hello'
        self.instance.language = 'fr'
        self.instance.title = 'Bonjour'
        self.instance.save()

        self.instance.clear_translations_cache()
        self.assertEqual(self.instance.cached_translations_count, 0)

        FooModel.objects.with_translations()

        self.assertEqual(self.instance.cached_translations_count, 2)

    def test_with_translations_fields(self):
        # Let's create an English post
        self.instance.language = 'en'
        self.instance.title = 'Hello'
        self.instance.excerpt = 'This is the excerpt.'
        self.instance.body = 'This is the body.'

        # Let's create a French post
        self.instance.language = 'fr'
        self.instance.title = 'Bonjour'
        self.instance.excerpt = 'Ceci est la description'
        self.instance.body = 'Corps'

        # Persist!
        self.instance.save()

        # Clear cache (remove all translations previously cached)
        self.instance.clear_translations_cache()
        self.assertEqual(self.instance.cached_translations_count, 0)

        # If we just want the title field
        FooModel.objects.with_translations(field_names=('title',))
        self.assertEqual(self.instance.cached_translations_count, 2)
        self.assertTrue('foo_1_fr_title' in self.instance._linguist.translations)
        self.assertTrue('foo_1_en_title' in self.instance._linguist.translations)

        # Clear cache (remove all translations previously cached)
        self.instance.clear_translations_cache()
        self.assertEqual(self.instance.cached_translations_count, 0)

        # If we just want the title and body (excluding excerpt)
        FooModel.objects.with_translations(field_names=('title', 'body'))

        self.assertEqual(self.instance.cached_translations_count, 4)
        self.assertTrue('foo_1_fr_title' in self.instance._linguist.translations)
        self.assertTrue('foo_1_en_title' in self.instance._linguist.translations)
        self.assertTrue('foo_1_fr_body' in self.instance._linguist.translations)
        self.assertTrue('foo_1_en_body' in self.instance._linguist.translations)
