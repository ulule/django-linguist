# -*- coding: utf-8 -*-
from django.test import TestCase

from ..exceptions import AlreadyRegistered, Unregistered, InvalidModel, InvalidModelTranslation
from ..registry import LinguistRegistry as Registry

from .translations import (
    FooModel,
    BadModel,
    FooTranslation,
    BarTranslation,
    BadTranslation,
)


class RegistryTest(TestCase):
    """
    Tests the Linguist's Registry.
    """

    def test_register(self):
        registry = Registry()
        registry.register(FooTranslation)
        registry.register(BarTranslation)
        self.assertEqual(len(registry.identifiers), 2)
        self.assertEqual(len(registry.translations), 2)
        self.assertRaises(AlreadyRegistered, registry.register, FooTranslation)
        self.assertRaises(InvalidModelTranslation, registry.register, BadTranslation)

    def test_unregister(self):
        registry = Registry()
        registry.register(FooTranslation)
        registry.register(BarTranslation)
        self.assertEqual(len(registry.identifiers), 2)
        self.assertEqual(len(registry.translations), 2)
        registry.unregister('foo')
        self.assertEqual(len(registry.identifiers), 1)
        self.assertEqual(len(registry.translations), 1)
        registry.unregister('bar')
        self.assertEqual(len(registry.identifiers), 0)
        self.assertEqual(len(registry.translations), 0)
        self.assertRaises(Unregistered, registry.unregister, 'badaboom')

    def test_get_translation(self):
        registry = Registry()
        registry.register(FooTranslation)
        self.assertEqual(registry.get_translation('foo'), FooTranslation)
        self.assertRaises(Unregistered, registry.get_translation, BarTranslation)

    def test_validate_model(self):
        registry = Registry()
        self.assertRaises(InvalidModel, registry.validate_model, 'string')
        self.assertRaises(InvalidModel, registry.validate_model, 10)
        self.assertRaises(InvalidModel, registry.validate_model, BadModel)
        self.assertTrue(registry.validate_model(FooModel))

    def test_validate_identifier(self):
        registry = Registry()
        registry.register(FooTranslation)
        self.assertTrue(registry.validate_identifier('foo', in_registered=False))
        self.assertTrue(registry.validate_identifier('bar', in_registered=True))
        self.assertRaises(AlreadyRegistered, registry.validate_identifier, 'foo', True)
        self.assertRaises(Unregistered, registry.validate_identifier, 'bar', False)
