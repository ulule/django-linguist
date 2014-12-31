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

    def test_with_translations_args(self):
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

        self.assertTrue(self.instance._linguist.translations['title']['fr'])
        self.assertTrue(self.instance._linguist.translations['title']['en'])

        # Clear cache (remove all translations previously cached)
        self.instance.clear_translations_cache()
        self.assertEqual(self.instance.cached_translations_count, 0)

        # If we just want the title and body (excluding excerpt)
        FooModel.objects.with_translations(field_names=('title', 'body'))

        self.assertEqual(self.instance.cached_translations_count, 4)
        self.assertTrue(self.instance._linguist.translations['title']['fr'])
        self.assertTrue(self.instance._linguist.translations['body']['fr'])
        self.assertTrue(self.instance._linguist.translations['title']['en'])
        self.assertTrue(self.instance._linguist.translations['body']['en'])

        # Clear cache (remove all translations previously cached)
        self.instance.clear_translations_cache()
        self.assertEqual(self.instance.cached_translations_count, 0)

        # If we just want title and excerpt and only english
        FooModel.objects.with_translations(field_names=('title', 'excerpt'), languages=('en',))
        self.assertEqual(self.instance.cached_translations_count, 2)
        self.assertTrue(self.instance._linguist.translations['title']['en'])
        self.assertTrue(self.instance._linguist.translations['excerpt']['en'])

        # Clear cache (remove all translations previously cached)
        self.instance.clear_translations_cache()
        self.assertEqual(self.instance.cached_translations_count, 0)

        # If we just want title, excerpt, body and only french
        FooModel.objects.with_translations(field_names=('title', 'excerpt', 'body'), languages=('fr',))
        self.assertEqual(self.instance.cached_translations_count, 3)

        self.assertTrue(self.instance._linguist.translations['title']['fr'])
        self.assertTrue(self.instance._linguist.translations['excerpt']['fr'])
        self.assertTrue(self.instance._linguist.translations['body']['fr'])

        # If we just want title in english and french
        FooModel.objects.with_translations(field_names=('title',), languages=('fr', 'en'))
        self.assertEqual(self.instance.cached_translations_count, 2)
        self.assertTrue(self.instance._linguist.translations['title']['fr'])
        self.assertTrue(self.instance._linguist.translations['title']['en'])
