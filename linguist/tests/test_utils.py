# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json

from django.utils import translation

from .. import settings
from .. import utils

from .base import BaseTestCase


class UtilsTest(BaseTestCase):
    """
    Tests Linguist utils.
    """

    def test_get_language_name(self):
        expected = [("fr", "French"), ("en", "English")]

        for e in expected:
            self.assertEqual(utils.get_language_name(e[0]), e[1])

    def test_get_language(self):
        # Full? Returns first level
        translation.activate("en-us")
        self.assertEqual(utils.get_language(), "en")

        # Unsupported? Returns fallback one
        translation.activate("ru")
        self.assertEqual(utils.get_fallback_language(), "en")
        self.assertEqual(utils.get_language(), utils.get_fallback_language())

        # Deactivating all should returns fallback one
        translation.deactivate_all()
        self.assertEqual(utils.get_fallback_language(), "en")
        self.assertEqual(utils.get_language(), utils.get_fallback_language())

    def test_get_fallback_language(self):
        self.assertEqual(utils.get_fallback_language(), settings.DEFAULT_LANGUAGE)

    def test_get_supported_languages(self):
        languages = [("en-us", "English"), ("fr-ca", "Canadian French")]

        old = list(settings.SUPPORTED_LANGUAGES)
        settings.SUPPORTED_LANGUAGES = languages

        self.assertEqual(utils.get_supported_languages(), ["en_us", "fr_ca"])

        settings.SUPPORTED_LANGUAGES = old

    def test_get_language_fields(self):
        self.assertEqual(
            utils.get_language_fields(["title"]),
            ["title_en", "title_de", "title_fr", "title_es", "title_it", "title_pt"],
        )

    def test_build_localized_field_name(self):
        self.assertEqual(utils.build_localized_field_name("title", "fr"), "title_fr")
        self.assertEqual(
            utils.build_localized_field_name("title", "fr-ca"), "title_fr_ca"
        )

        translation.deactivate_all()
        self.assertEqual(utils.build_localized_field_name("title"), "title_en")

        translation.activate("it")
        self.assertEqual(utils.build_localized_field_name("title"), "title_it")

    def test_get_translation_lookup(self):
        expected = {
            # default language
            "title": {
                "field_name": "title",
                "field_value": "value",
                "identifier": "foo",
                "language": "en",
            },
            "title_fr": {
                "field_name": "title",
                "field_value": "value",
                "identifier": "foo",
                "language": "fr",
            },
            "title_fr__transformer": {
                "field_name": "title",
                "field_value__transformer": "value",
                "identifier": "foo",
                "language": "fr",
            },
            "title_fr__transformer1__transformer2": {
                "field_name": "title",
                "field_value__transformer1__transformer2": "value",
                "identifier": "foo",
                "language": "fr",
            },
        }

        for k, v in expected.items():
            lookup = utils.get_translation_lookup("foo", k, "value")
            lookup = json.loads(json.dumps(lookup, sort_keys=True))
            self.assertEqual(lookup, expected[k])
