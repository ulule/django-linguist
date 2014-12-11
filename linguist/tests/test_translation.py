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
class TranslationTest(TestCase):
    """
    Tests the Linguist's Translation class.
    """

    def setUp(self):
        self.registry = Registry()
        self.registry.register(FooTranslation)
        self.instance = FooModel()

    def test_fields(self):
        for language in LANGUAGES:
            self.assertIn('title_%s' % language, dir(FooModel))

    def test_getter_setter(self):
        with self.assertNumQueries(3):
            # save = 1 query
            self.instance.save()
            # get / create "en" translation = 2 queries
            self.instance.title = 'Hello'

        self.assertEqual(self.instance.title_en, 'Hello')
        self.assertIsNone(self.instance.title_fr)

        self.instance.set_current_language('fr')
        self.instance.title = 'Bonjour'
        self.assertEqual(self.instance.title_en, 'Hello')
        self.assertEqual(self.instance.title_fr, 'Bonjour')
