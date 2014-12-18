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
        self.instance.language = 'en'
        self.instance.title = 'Hello'

    def test_identifier(self):
        self.assertTrue(hasattr(self.instance, 'identifier'))
        self.assertEqual(self.instance.identifier, 'foo')

    def test_language(self):
        self.assertTrue(hasattr(self.instance, 'language'))
        self.assertEqual(self.instance.language, 'en')
        self.instance.language = 'fr'
        self.assertEqual(self.instance.language, 'fr')

    def test_available_languages(self):
        self.assertTrue(hasattr(self.instance, 'available_languages'))
        self.instance.language = 'fr'
        self.instance.title = 'Bonjour'
        self.assertEqual(len(self.instance.available_languages), 2)
