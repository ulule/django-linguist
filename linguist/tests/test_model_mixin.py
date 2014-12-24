# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from .base import BaseTestCase

from .translations import FooModel, FooTranslation


class ModelMixinTest(BaseTestCase):
    """
    Tests Linguist mixin.
    """

    def setUp(self):
        self.create_registry()

    def test_linguist_identifier(self):
        self.assertTrue(hasattr(self.instance, 'linguist_identifier'))
        self.assertEqual(self.instance.linguist_identifier, 'foo')

    def test_language(self):
        self.assertTrue(hasattr(self.instance, 'language'))
        self.assertEqual(self.instance.language, 'en')
        self.instance.language = 'fr'
        self.assertEqual(self.instance.language, 'fr')

    def test_default_language(self):
        self.assertTrue(hasattr(self.instance, 'default_language'))
        self.assertEqual(self.instance.default_language, 'en')
        self.instance.default_language = 'fr'
        self.assertEqual(self.instance.default_language, 'fr')

    def test_available_languages(self):
        self.assertTrue(hasattr(self.instance, 'available_languages'))
        self.assertEqual(len(self.instance.available_languages), 0)

    def test_translatable_fields(self):
        self.assertTrue(hasattr(self.instance, 'translatable_fields'))
        self.assertEqual(self.instance.translatable_fields, ('title',))

    def test_cached_translations_count(self):
        self.instance.language = 'en'
        self.instance.title = 'Hello'
        self.instance.language = 'fr'
        self.instance.title = 'Bonjour'
        self.assertEqual(self.instance.cached_translations_count, 2)
        self.instance.language = 'pt'
        self.instance.title = "Ola"
        self.assertEqual(self.instance.cached_translations_count, 3)

    def test_clear_translations_cache(self):
        self.instance.language = 'en'
        self.instance.title = 'Hello'
        self.instance.language = 'fr'
        self.instance.title = 'Bonjour'
        self.assertEqual(self.instance.cached_translations_count, 2)
        self.instance.clear_translations_cache()
        self.assertEqual(self.instance.cached_translations_count, 0)

    def test_new_instance_cache(self):
        self.instance.language = 'en'
        self.instance.title = 'Hello'
        cache_key = 'translation_foo_new-%s_en_title' % id(self.instance)
        self.assertTrue(cache_key in self.instance._linguist)
        attrs = self.instance._linguist.get(cache_key)
        self.assertEqual(attrs['language'], 'en')
        self.assertEqual(attrs['object_id'], 'new-%s' % id(self.instance))
        self.assertEqual(attrs['field_value'], 'Hello')
        self.assertEqual(attrs['is_new'], True)
        self.assertEqual(attrs['identifier'], 'foo')
        self.assertEqual(attrs['field_name'], 'title')

        self.instance.language = 'fr'
        self.instance.title = 'Bonjour'
        cache_key = 'translation_foo_new-%s_fr_title' % id(self.instance)
        self.assertEqual(self.instance.cached_translations_count, 2)
        self.assertTrue(cache_key in self.instance._linguist)
        attrs = self.instance._linguist.get(cache_key)
        self.assertEqual(attrs['language'], 'fr')
        self.assertEqual(attrs['object_id'], 'new-%s' % id(self.instance))
        self.assertEqual(attrs['field_value'], 'Bonjour')
        self.assertEqual(attrs['is_new'], True)
        self.assertEqual(attrs['identifier'], 'foo')
        self.assertEqual(attrs['field_name'], 'title')

    def test_saved_instance_cache(self):
        self.instance.language = 'en'
        self.instance.title = 'Hello'
        self.instance.language = 'fr'
        self.instance.title = 'Bonjour'
        self.instance.save()

        cache_key_en = 'translation_foo_%s_en_title' % self.instance.pk
        cache_key_fr = 'translation_foo_%s_fr_title' % self.instance.pk

        cache_keys = [cache_key_en, cache_key_fr]

        for cache_key in cache_keys:
            self.assertTrue(cache_key in self.instance._linguist)

        attrs = self.instance._linguist.get(cache_key_en)
        self.assertEqual(attrs['language'], 'en')
        self.assertEqual(attrs['object_id'], '%s' % self.instance.pk)
        self.assertEqual(attrs['field_value'], 'Hello')
        self.assertEqual(attrs['is_new'], False)
        self.assertEqual(attrs['identifier'], 'foo')
        self.assertEqual(attrs['field_name'], 'title')

        attrs = self.instance._linguist.get(cache_key_fr)
        self.assertEqual(attrs['language'], 'fr')
        self.assertEqual(attrs['object_id'], '%s' % self.instance.pk)
        self.assertEqual(attrs['field_value'], 'Bonjour')
        self.assertEqual(attrs['is_new'], False)
        self.assertEqual(attrs['identifier'], 'foo')
        self.assertEqual(attrs['field_name'], 'title')
