# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.utils import translation

from ..models import Translation

from .base import BaseTestCase
from .models import FooModel


class ManagerMixinTest(BaseTestCase):
    """
    Tests the Linguist's manager mixin.
    """

    def test_with_translations(self):
        # Be sure we have the method
        self.assertTrue(hasattr(FooModel.objects, 'with_translations'))

        # Create English content
        self.instance.activate_language('en')
        self.instance.title = 'Hello'

        # Create French content
        self.instance.activate_language('fr')
        self.instance.title = 'Bonjour'

        # Persist!
        #
        # 1 - INSERT INTO foomodel
        # 2 - SAVEPOINT
        # 3 - INSERT INTO translation
        # 4 - RELEASE SAVEPOINT
        with self.assertNumQueries(4):
            self.instance.save()

        # Titles are now cached
        with self.assertNumQueries(0):
            self.instance.activate_language('en')
            en_title = '%s' % self.instance.title  # noqa
            self.instance.activate_language('fr')
            fr_title = '%s' % self.instance.title  # noqa

        # Preload translations without clearing the cache
        #
        # 1 - SELECT ALL foomodel
        # 2 - SELECT IN translation
        with self.assertNumQueries(2):
            FooModel.objects.with_translations()

        # Clear cache
        self.instance.clear_translations_cache()
        self.assertEqual(self.instance.cached_translations_count, 0)

        # Preload translations with cache cleared
        #
        # 1 - SELECT ALL foomodel
        # 2 - SELECT IN translation
        with self.assertNumQueries(2):
            instances = FooModel.objects.with_translations()

        instance = instances[0]

        # Database should be not hit
        with self.assertNumQueries(0):
            self.assertEqual(instance.cached_translations_count, 2)

    def test_with_translations_args(self):
        # Create English content
        self.instance.activate_language('en')
        self.instance.title = 'Hello'
        self.instance.excerpt = 'This is the excerpt.'
        self.instance.body = 'This is the body.'

        # Create French content
        self.instance.activate_language('fr')
        self.instance.title = 'Bonjour'
        self.instance.excerpt = 'Ceci est la description'
        self.instance.body = 'Corps'

        # Persist!
        #
        # 1 - INSERT INTO foomodel
        # 2 - SAVEPOINT
        # 3 - INSERT INTO translation
        # 4 - RELEASE SAVEPOINT
        with self.assertNumQueries(4):
            self.instance.save()

        # Preload translations without clearing the cache
        #
        # 1 - SELECT ALL foomodel
        # 2 - SELECT IN translation
        with self.assertNumQueries(2):
            FooModel.objects.with_translations()

        # Clear cache
        self.instance.clear_translations_cache()
        self.assertEqual(self.instance.cached_translations_count, 0)

        # If we just want the title field
        #
        # 1 - SELECT ALL foomodel
        # 2 - SELECT IN translation
        with self.assertNumQueries(2):
            instances = FooModel.objects.with_translations(field_names=('title',))

        self.instance = instances[0]

        # Cache has been cleared and we got now the two titles
        self.assertEqual(self.instance.cached_translations_count, 2)

        # Verify dict
        with self.assertNumQueries(0):
            self.assertTrue(self.instance._linguist.translations['title']['fr'])
            self.assertTrue(self.instance._linguist.translations['title']['en'])

        # Clear cache
        self.instance.clear_translations_cache()
        self.assertEqual(self.instance.cached_translations_count, 0)

        # If we just want the title and body (excluding excerpt)
        #
        # 1 - SELECT ALL foomodel
        # 2 - SELECT IN translation
        with self.assertNumQueries(2):
            instances = FooModel.objects.with_translations(field_names=('title', 'body'))

        self.instance = instances[0]

        # Cached has been cleared. We should have title/body for each language
        self.assertEqual(self.instance.cached_translations_count, 4)

        # Verify dict
        self.assertTrue(self.instance._linguist.translations['title']['fr'])
        self.assertTrue(self.instance._linguist.translations['body']['fr'])
        self.assertTrue(self.instance._linguist.translations['title']['en'])
        self.assertTrue(self.instance._linguist.translations['body']['en'])

        # Clear cache
        self.instance.clear_translations_cache()
        self.assertEqual(self.instance.cached_translations_count, 0)

        # If we just want title and excerpt and only english
        #
        # 1 - SELECT ALL foomodel
        # 2 - SELECT IN translation
        with self.assertNumQueries(2):
            instances = FooModel.objects.with_translations(field_names=('title', 'excerpt'), languages=('en',))

        self.instance = instances[0]

        # Cache has been cleared. We should have title/excerpt for English only.
        self.assertEqual(self.instance.cached_translations_count, 2)

        # Verify dict
        self.assertTrue(self.instance._linguist.translations['title']['en'])
        self.assertTrue(self.instance._linguist.translations['excerpt']['en'])

        # Clear cache
        self.instance.clear_translations_cache()
        self.assertEqual(self.instance.cached_translations_count, 0)

        # If we just want title, excerpt, body and only french
        #
        # 1 - SELECT ALL foomodel
        # 2 - SELECT IN translation
        with self.assertNumQueries(2):
            instances = FooModel.objects.with_translations(field_names=('title', 'excerpt', 'body'), languages=('fr',))

        self.instance = instances[0]

        # Cache has been cleared. We should have title/excerpt/body for French only
        self.assertEqual(self.instance.cached_translations_count, 3)

        # Verify dict
        self.assertTrue(self.instance._linguist.translations['title']['fr'])
        self.assertTrue(self.instance._linguist.translations['excerpt']['fr'])
        self.assertTrue(self.instance._linguist.translations['body']['fr'])

        # If we just want title in english and french
        #
        # 1 - SELECT ALL foomodel
        # 2 - SELECT IN translation
        with self.assertNumQueries(2):
            instances = FooModel.objects.with_translations(field_names=('title',), languages=('fr', 'en'))

        self.instance = instances[0]

        # Cache has been cleared. We should have titles for French and English
        self.assertEqual(self.instance.cached_translations_count, 2)

        # Verify dict
        self.assertTrue(self.instance._linguist.translations['title']['fr'])
        self.assertTrue(self.instance._linguist.translations['title']['en'])

    def test_without_prefetching(self):
        # Create English content
        self.instance.activate_language('en')
        self.instance.title = 'Hello'

        # Create French content
        self.instance.activate_language('fr')
        self.instance.title = 'Bonjour'

        # Persist!
        #
        # 1 - INSERT INTO foomodel
        # 2 - SAVEPOINT
        # 3 - INSERT INTO translation
        # 4 - RELEASE SAVEPOINT
        with self.assertNumQueries(4):
            self.instance.save()

        # Clear cache
        self.instance.clear_translations_cache()
        self.assertEqual(self.instance.cached_translations_count, 0)

        # Because we don't use with_translations() here, each __get__ should
        # hit the database:
        #
        # 1 - Fetch title en
        # 2 - Fetch title fr
        with self.assertNumQueries(2):
            self.instance.activate_language('en')
            en_title = '%s' % self.instance.title  # noqa
            self.instance.activate_language('fr')
            fr_title = '%s' % self.instance.title  # noqa

        # Be sure titles are now in cache
        self.assertEqual(self.instance.cached_translations_count, 2)

        # Let's try again. Database should not be hit
        with self.assertNumQueries(0):
            self.instance.activate_language('en')
            en_title = '%s' % self.instance.title  # noqa
            self.instance.activate_language('fr')
            fr_title = '%s' % self.instance.title  # noqa

    def test_instance_cache(self):
        self.instance.title = 'hello'
        self.instance.save()

        self.assertTrue(self.instance._linguist)
        self.assertRaises(TypeError, FooModel._linguist)

    def test_language_activation(self):
        # Default to "en" (settings.LANGUAGE_CODE)
        self.assertEqual(translation.get_language(), 'en')

        self.instance.activate_language('en')
        self.instance.title = 'hello'
        self.instance.activate_language('fr')
        self.instance.title = 'bonjour'
        self.instance.save()
        self.assertEqual(Translation.objects.count(), 2)
        self.assertEqual(FooModel.objects.with_translations().first().active_language, 'en')

        # Switch to "fr"
        translation.activate('fr')
        self.assertEqual(translation.get_language(), 'fr')
        instance = FooModel.objects.with_translations().first()
        self.assertEqual(instance.active_language, 'fr')
        self.assertEqual(instance.title, 'bonjour')

        # Switch to "en"
        translation.activate('en')
        self.assertEqual(translation.get_language(), 'en')
        instance = FooModel.objects.with_translations().first()
        self.assertEqual(instance.active_language, 'en')
        self.assertEqual(instance.title, 'hello')

    def test_with_translation_with_translation_activate(self):
        # Let's define available languages
        languages = ('en', 'fr', 'it', 'de', 'pt')

        # Let's create multiple instances
        for i in range(20):
            m = FooModel()
            for language in languages:
                m.activate_language(language)
                m.title = 'Title in %s' % language
            m.save()

        self.assertEqual(FooModel.objects.count(), 20)
        self.assertEqual(Translation.objects.count(), 100)  # 20 objects x 5 languages

        # Default to "en" (settings.LANGUAGE_CODE)
        self.assertEqual(translation.get_language(), 'en')

        # Without prefetch
        qs = FooModel.objects.all()
        with self.assertNumQueries(101):
            for language in languages:
                translation.activate(language)
                for obj in qs:
                    string = '%s' % obj.title  # noqa

        # With prefetch
        qs = FooModel.objects.with_translations()
        with self.assertNumQueries(0):
            for language in languages:
                translation.activate(language)
                for obj in qs:
                    string = '%s' % obj.title  # noqa
