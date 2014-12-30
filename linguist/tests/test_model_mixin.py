# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from .base import BaseTestCase

from .. import settings
from .. import utils
from ..base import ModelTranslationBase
from ..models import Translation

from .translations import FooModel


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
        self.assertEqual(self.instance.translatable_fields, ('title', 'excerpt', 'body'))

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

    def test_model_fields(self):
        for code, name in settings.SUPPORTED_LANGUAGES:
            field_name = 'title_%s' % code
            self.assertIn(field_name, dir(self.instance._meta.model))

    def test_new_instance_cache(self):
        self.instance.language = 'en'
        self.instance.title = 'Hello'
        self.assertTrue(self.instance._linguist.translations['title']['en'])

        cached_obj = self.instance._linguist.translations['title']['en']
        self.assertEqual(cached_obj.language, 'en')
        self.assertIsNone(cached_obj.object_id)
        self.assertEqual(cached_obj.field_value, 'Hello')
        self.assertEqual(cached_obj.is_new, True)
        self.assertEqual(cached_obj.identifier, 'foo')
        self.assertEqual(cached_obj.field_name, 'title')

        self.instance.language = 'fr'
        self.instance.title = 'Bonjour'
        self.assertEqual(self.instance.cached_translations_count, 2)
        self.assertTrue(self.instance._linguist.translations['title']['fr'])

        cached_obj = self.instance._linguist.translations['title']['fr']
        self.assertEqual(cached_obj.language, 'fr')
        self.assertIsNone(cached_obj.object_id)
        self.assertEqual(cached_obj.field_value, 'Bonjour')
        self.assertEqual(cached_obj.is_new, True)
        self.assertEqual(cached_obj.identifier, 'foo')
        self.assertEqual(cached_obj.field_name, 'title')

    def test_saved_instance_cache(self):
        self.instance.language = 'en'
        self.instance.title = 'Hello'
        self.instance.language = 'fr'
        self.instance.title = 'Bonjour'
        self.instance.save()

        self.assertTrue(self.instance._linguist.translations['title']['fr'])
        self.assertTrue(self.instance._linguist.translations['title']['en'])

        title_fr = self.instance._linguist.translations['title']['fr']
        title_en = self.instance._linguist.translations['title']['en']

        self.assertEqual(title_en.language, 'en')
        self.assertEqual(title_en.object_id, self.instance.pk)
        self.assertEqual(title_en.field_value, 'Hello')
        self.assertEqual(title_en.is_new, False)
        self.assertEqual(title_en.identifier, 'foo')
        self.assertEqual(title_en.field_name, 'title')

        self.assertEqual(title_fr.language, 'fr')
        self.assertEqual(title_fr.object_id, self.instance.pk)
        self.assertEqual(title_fr.field_value, 'Bonjour')
        self.assertEqual(title_fr.is_new, False)
        self.assertEqual(title_fr.identifier, 'foo')
        self.assertEqual(title_fr.field_name, 'title')

    def test_default_language_scenario(self):
        #
        # Let's define a default language in translation class.
        #
        class FooTranslationDefaultLanguage(ModelTranslationBase):
            model = FooModel
            identifier = 'foo'
            fields = ('title', )
            default_language = 'fr'

        #
        # Re-register translation class and re-create new model instance.
        #
        self.registry.unregister('foo')
        self.registry.register(FooTranslationDefaultLanguage)
        self.instance = FooModel()

        #
        # The default language must be the one defined in translation class.
        #
        self.assertEqual(self.instance.default_language, 'fr')
        self.instance.title = 'Bonjour'
        self.instance.save()
        self.assertEqual(Translation.objects.first().language, 'fr')

        #
        # Now, switch to English and it should work.
        #
        self.instance.language = 'en'
        self.instance.title = 'Hello'
        self.instance.save()

        self.assertEqual(Translation.objects.count(), 1)
        self.assertEqual(list(Translation.objects.get_languages()), ['en', 'fr'])

        #
        # Let's change the default language for the instance.
        #
        self.instance.default_language = 'de'
        self.instance.title = 'Hello'
        self.instance.save()

        #
        # Instance language should have been changed too.
        #
        self.assertEqual(self.instance.language, 'de')
        self.assertEqual(Translation.objects.count(), 3)
        self.assertEqual(list(Translation.objects.get_languages()), ['de', 'en', 'fr'])

        #
        # Let's change instance language again.
        #
        self.instance.language = 'it'
        self.instance.title = 'Pronto'
        self.instance.save()
        self.assertEqual(Translation.objects.count(), 4)
        self.assertEqual(list(Translation.objects.get_languages()), ['de', 'en', 'fr', 'it'])
