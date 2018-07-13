# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.utils import translation

from exam import before

from .. import settings
from ..fields import TranslationField
from ..models import Translation

from .base import BaseTestCase

from .models import (
    Article,
    FooModel,
    DefaultLanguageFieldModel,
    DefaultLanguageFieldModelWithCallable,
    CustomTranslationModel,
    DeciderModel,
)


class ModelMixinTest(BaseTestCase):
    """
    Tests Linguist mixin.
    """

    @before
    def before(self):
        translation.activate("en")

    def test_linguist_identifier(self):
        self.assertTrue(hasattr(self.instance, "linguist_identifier"))
        self.assertEqual(self.instance.linguist_identifier, "foo")

    def test_activate_language(self):
        self.assertTrue(hasattr(self.instance, "activate_language"))
        self.instance.activate_language("en")
        self.assertEqual(self.instance._linguist.language, "en")
        self.instance.activate_language("fr")
        self.assertEqual(self.instance._linguist.language, "fr")

    def test_default_language(self):
        self.assertTrue(hasattr(self.instance, "default_language"))
        self.assertEqual(self.instance.default_language, "en")
        self.instance.default_language = "fr"
        self.assertEqual(self.instance.default_language, "fr")

    def test_available_languages(self):
        self.assertTrue(hasattr(self.instance, "available_languages"))
        self.assertEqual(len(self.instance.available_languages), 0)

    def test_translatable_fields(self):
        self.assertTrue(hasattr(self.instance, "translatable_fields"))
        self.assertEqual(
            self.instance.translatable_fields, ["title", "excerpt", "body"]
        )

    def test_cached_translations_count(self):
        self.instance.activate_language("en")
        self.instance.title = "Hello"
        self.instance.activate_language("fr")
        self.instance.title = "Bonjour"
        self.assertEqual(self.instance.cached_translations_count, 2)
        self.instance.activate_language("pt")
        self.instance.title = "Ola"
        self.assertEqual(self.instance.cached_translations_count, 3)

    def test_clear_translations_cache(self):
        self.instance.activate_language("en")
        self.instance.title = "Hello"
        self.instance.activate_language("fr")
        self.instance.title = "Bonjour"
        self.assertEqual(self.instance.cached_translations_count, 2)
        self.instance.clear_translations_cache()
        self.assertEqual(self.instance.cached_translations_count, 0)

    def test_model_fields(self):
        for code, name in settings.SUPPORTED_LANGUAGES:
            field_name = "title_%s" % code
            self.assertIn(field_name, dir(self.instance._meta.model))

    def test_new_instance_cache(self):
        self.instance.activate_language("en")
        self.instance.title = "Hello"
        self.assertTrue(self.instance._linguist.translations["title"]["en"])

        cached_obj = self.instance._linguist.translations["title"]["en"]
        self.assertEqual(cached_obj.language, "en")
        self.assertIsNone(cached_obj.object_id)
        self.assertEqual(cached_obj.field_value, "Hello")
        self.assertEqual(cached_obj.is_new, True)
        self.assertEqual(cached_obj.identifier, "foo")
        self.assertEqual(cached_obj.field_name, "title")

        self.instance.activate_language("fr")
        self.instance.title = "Bonjour"
        self.assertEqual(self.instance.cached_translations_count, 2)
        self.assertTrue(self.instance._linguist.translations["title"]["fr"])

        cached_obj = self.instance._linguist.translations["title"]["fr"]
        self.assertEqual(cached_obj.language, "fr")
        self.assertIsNone(cached_obj.object_id)
        self.assertEqual(cached_obj.field_value, "Bonjour")
        self.assertEqual(cached_obj.is_new, True)
        self.assertEqual(cached_obj.identifier, "foo")
        self.assertEqual(cached_obj.field_name, "title")

    def test_saved_instance_cache(self):
        self.instance.activate_language("en")
        self.instance.title = "Hello"
        self.instance.activate_language("fr")
        self.instance.title = "Bonjour"
        self.instance.save()

        self.assertEqual(Translation.objects.count(), 2)

        self.assertTrue(self.instance._linguist.translations["title"]["fr"])
        self.assertTrue(self.instance._linguist.translations["title"]["en"])

        title_fr = self.instance._linguist.translations["title"]["fr"]
        title_en = self.instance._linguist.translations["title"]["en"]

        self.assertEqual(title_en.language, "en")
        self.assertEqual(title_en.object_id, self.instance.pk)
        self.assertEqual(title_en.field_value, "Hello")
        self.assertEqual(title_en.is_new, False)
        self.assertEqual(title_en.identifier, "foo")
        self.assertEqual(title_en.field_name, "title")

        self.assertEqual(title_fr.language, "fr")
        self.assertEqual(title_fr.object_id, self.instance.pk)
        self.assertEqual(title_fr.field_value, "Bonjour")
        self.assertEqual(title_fr.is_new, False)
        self.assertEqual(title_fr.identifier, "foo")
        self.assertEqual(title_fr.field_name, "title")

    def test_instance_cache_has_changed(self):
        self.instance.activate_language("en")
        self.instance.title = "Hello"
        self.instance.activate_language("fr")
        self.instance.title = "Bonjour"
        self.instance.save()

        with self.assertNumQueries(1):
            self.instance.save()

        instance = FooModel.objects.get(pk=self.instance.pk)
        instance.activate_language("en")
        instance.title_en = "Hi"
        instance.title_fr = "Salut"

        with self.assertNumQueries(3):
            instance.save()

        self.assertEqual(instance.title, "Hi")
        self.assertEqual(instance.title_en, "Hi")
        self.assertEqual(instance.title_fr, "Salut")

        instance = FooModel.objects.get(pk=self.instance.pk)

        instance.activate_language("en")
        self.assertEqual(instance.title, "Hi")
        self.assertEqual(instance.title_en, "Hi")
        self.assertEqual(instance.title_fr, "Salut")

        instance = FooModel.objects.get(pk=self.instance.pk)
        instance.activate_language("en")
        instance.title = "Howdy"

        with self.assertNumQueries(2):
            instance.save()

        self.assertEqual(instance.title_en, "Howdy")
        self.assertEqual(instance.title_fr, "Salut")

        instance.activate_language("en")
        instance.title = "Plop"

        with self.assertNumQueries(2):
            instance.save()

        self.assertEqual(instance.title, "Plop")
        self.assertEqual(instance.title_en, "Plop")
        self.assertEqual(instance.title_fr, "Salut")

        instance = FooModel.objects.get(pk=self.instance.pk)
        instance.activate_language("en")
        self.assertEqual(instance.title, "Plop")
        self.assertEqual(instance.title_en, "Plop")
        self.assertEqual(instance.title_fr, "Salut")

    def test_instance_cache_empty_value(self):
        self.instance.activate_language("en")
        self.instance.title = "Hello"
        self.instance.activate_language("fr")
        self.instance.title = "Bonjour"
        self.instance.save()

        with self.assertNumQueries(1):
            self.instance.save()

        instance = FooModel.objects.get(pk=self.instance.pk)
        instance.activate_language("en")
        instance.title_en = "Hi"
        instance.activate_language("fr")
        instance.title_fr = "Bonjour"

        instance2 = FooModel()
        instance2.activate_language("en")
        instance2.title = "Nice day"
        instance2.activate_language("fr")
        instance2.title = "Belle journee"
        instance2.save()

        self.assertEqual(instance2.title_fr, "Belle journee")
        self.assertEqual(instance2.title_en, "Nice day")

        instance2 = FooModel.objects.get(pk=instance2.pk)
        instance2.activate_language("fr")
        instance2.title = ""

        with self.assertNumQueries(2):
            instance.save()

        with self.assertNumQueries(2):
            instance2.save()

        instance = FooModel.objects.get(pk=self.instance.pk)
        instance.activate_language("en")
        self.assertEqual(instance.title, "Hi")
        self.assertEqual(instance.title_en, "Hi")
        self.assertEqual(instance.title_fr, "Bonjour")

        instance2 = FooModel.objects.get(pk=instance2.pk)
        instance2.activate_language("en")
        self.assertEqual(instance2.title, "Nice day")
        self.assertEqual(instance2.title_en, "Nice day")
        self.assertEqual(instance2.title_fr, "")

    def test_instance_delete_value(self):
        self.instance.activate_language("en")
        self.instance.title = "Hello"
        self.instance.activate_language("fr")
        self.instance.title = "Bonjour"
        self.instance.save()

        with self.assertNumQueries(1):
            self.instance.save()

        instance = FooModel.objects.get(pk=self.instance.pk)
        instance.activate_language("en")
        instance.title_en = "Hi"

        instance2 = FooModel()
        instance2.activate_language("en")
        instance2.title = "Nice day"
        instance2.activate_language("fr")
        instance2.title = "Belle journee"
        instance2.save()

        self.assertEqual(instance2.title_fr, "Belle journee")
        self.assertEqual(instance2.title_en, "Nice day")

        instance2 = FooModel.objects.get(pk=instance2.pk)
        instance2.activate_language("fr")
        instance2.title = None

        with self.assertNumQueries(2):
            instance.save()

        with self.assertNumQueries(4):
            instance2.save()

        instance = FooModel.objects.get(pk=self.instance.pk)
        instance.activate_language("en")
        self.assertEqual(instance.title, "Hi")
        self.assertEqual(instance.title_en, "Hi")
        self.assertEqual(instance.title_fr, "Bonjour")

        instance2 = FooModel.objects.get(pk=instance2.pk)
        instance2.activate_language("en")
        self.assertEqual(instance2.title, "Nice day")
        self.assertEqual(instance2.title_en, "Nice day")
        self.assertEqual(instance2.title_fr, "")

        self.assertEqual(
            Translation.objects.filter(
                object_id=instance2.pk, language="fr", field_name="title"
            ).count(),
            0,
        )

    def test_override_language(self):
        self.assertTrue(hasattr(self.instance, "override_language"))
        self.instance.activate_language("fr")
        self.assertEqual(self.instance._linguist.language, "fr")
        with self.instance.override_language("de"):
            self.assertEqual(self.instance._linguist.language, "de")
        self.assertEqual(self.instance._linguist.language, "fr")

    def test_instance_cache_only(self):
        self.assertRaises(TypeError, FooModel._linguist)
        for i in range(10):
            o = FooModel()
            o.activate_language("en")
            o.title = "title %d" % i
            o.activate_language("fr")
            o.title = "title %d" % i
            o.save()
            self.assertEquals(o.cached_translations_count, 2)

    def test_default_language_descriptor(self):
        m = DefaultLanguageFieldModel()
        self.assertEqual(m.lang, "fr")
        self.assertEqual(m.default_language, "fr")

        m.title_fr = "Bonjour"
        m.title_en = "Hello"
        m.save()
        self.assertEqual(m.cached_translations_count, 2)

        translation.activate("it")
        self.assertEqual(m.title, "Bonjour")

    def test_default_language_descriptor_with_callable(self):
        m = DefaultLanguageFieldModelWithCallable()
        self.assertEqual(m.lang, "fr")
        self.assertEqual(m.default_language, "fr")

        m.title_fr = "Bonjour"
        m.title_en = "Hello"
        m.save()
        self.assertEqual(m.cached_translations_count, 2)

        translation.activate("it")
        self.assertEqual(m.title, "Bonjour")

    def test_default_language_descriptor_with_multiple_languages(self):
        m = DefaultLanguageFieldModel(
            title="hello", title_en="hello", title_fr="bonjour", lang="en"  # title_en
        )
        m.save()

        # As we explicitly set title_en and title_fr, we should have 2
        # translations saved
        self.assertEqual(Translation.objects.count(), 2)

        # Let's reset
        Translation.objects.all().delete()

        # If we don't set title field, it should work too.
        m = DefaultLanguageFieldModel(title_en="hello", title_fr="bonjour", lang="en")
        m.save()

        self.assertEqual(Translation.objects.count(), 2)

    def test_language_fields(self):
        # default language
        m = FooModel(title_en="hello", title_fr="bonjour")
        m.save()
        self.assertEqual(m.title_en, "hello")
        self.assertEqual(m.title_fr, "bonjour")

        # language field
        m = DefaultLanguageFieldModel(title_en="hello", title_fr="bonjour", lang="en")
        m.save()
        self.assertEqual(m.title_en, "hello")
        self.assertEqual(m.title_fr, "bonjour")

        # language field callable
        m = DefaultLanguageFieldModelWithCallable(title_en="hello", title_fr="bonjour")
        m.save()
        self.assertEqual(m.title_en, "hello")
        self.assertEqual(m.title_fr, "bonjour")

    def test_decider(self):
        m = DeciderModel()
        m.title = "bonjour"
        m.save()

        self.assertEqual(Translation.objects.count(), 0)
        self.assertEqual(CustomTranslationModel.objects.count(), 1)

    def test_no_translation_default_language(self):
        # This is the case of:
        # * "default_language" is not defined in linguist meta
        # * No translation is available for the current supported language
        # So we always try to display default language or empty value
        m = FooModel(title_en="hello", title_fr="bonjour")
        m.save()

        saved_lang = translation.get_language()
        translation.activate("it")

        self.assertEqual(m.title, "hello")

        translation.activate(saved_lang)

    def test_prefetch_translations(self):
        article = self.articles[0]

        # No related
        with self.assertNumQueries(1):
            article.prefetch_translations()
        with self.assertNumQueries(0):
            for language in ("fr", "en"):
                title = getattr(article, "title_%s" % language)

        # Clean
        article.clear_translations_cache()
        article.author.clear_translations_cache()

        # ForeignKey
        with self.assertNumQueries(2):
            article.prefetch_translations("author")
        with self.assertNumQueries(0):
            for language in ("fr", "en"):
                title = getattr(article, "title_%s" % language)
                author_bio = getattr(article.author, "bio_%s" % language)

    def test_prefetch_translations_with_no_translations(self):
        m = FooModel()
        m.save()
        m.prefetch_translations()
        self.assertEqual(m.cached_translations_count, 18)

    def test_prefetch_translations_parameters(self):
        article = self.articles[0]

        #
        # prefetch_translations(field_names=['title'])
        #

        article.clear_translations_cache()

        with self.assertNumQueries(1):
            article.prefetch_translations(field_names=["title"])

        with self.assertNumQueries(0):
            for language in ("fr", "en"):
                title = getattr(article, "title_%s" % language)

        with self.assertNumQueries(0):
            for language in ("fr", "en"):
                self.assertEqual(getattr(article, "content_%s" % language), "")

        #
        # prefetch_translations(populate_missing=True)
        #

        article.clear_translations_cache()

        with self.assertNumQueries(1):
            article.prefetch_translations(field_names=["title"], populate_missing=False)

        with self.assertNumQueries(0):
            for language in ("fr", "en"):
                title = getattr(article, "title_%s" % language)

        with self.assertNumQueries(2):
            for language in ("fr", "en"):
                self.assertNotEqual(getattr(article, "content_%s" % language), "")

        #
        # prefetch_translations(languages=['en'])
        #

        article.clear_translations_cache()

        with self.assertNumQueries(1):
            article.prefetch_translations(
                field_names=["title"], languages=["fr"], populate_missing=False
            )

        with self.assertNumQueries(1):
            for language in ("fr", "en"):
                title = getattr(article, "title_%s" % language)

        #
        # Be sure prefetch_translations(languages='en') is interpreted as
        # prefetch_translations(languages=['en'])
        article.clear_translations_cache()

        with self.assertNumQueries(1):
            article.prefetch_translations(
                field_names=["title"], languages="en", populate_missing=False
            )

        with self.assertNumQueries(1):
            for language in ("fr", "en"):
                title = getattr(article, "title_%s" % language)

    def test_get_field_object(self):
        field = self.translated_instance.get_field_object("title", "en")
        assert TranslationField in field.__class__.__mro__

        # If the method is called with a field that's unknown to linguist, it is a programming error and it should raise
        self.assertRaises(
            KeyError, self.translated_instance.get_field_object, "title", "lu"
        )
        self.assertRaises(
            KeyError, self.translated_instance.get_field_object, "description", "en"
        )
