# -*- coding: utf-8 -*-
from django.db import models
from django.test import TestCase

from ..exceptions import AlreadyRegistered, Unregistered, InvalidModel
from ..registry import LinguistRegistry as Registry


class FooModel(models.Model):
    title = models.CharField(max_length=255)


class BarModel(models.Model):
    title = models.CharField(max_length=255)


class BazModel(models.Model):
    title = models.CharField(max_length=255)


class BadModel(object):
    pass


class RegistryTest(TestCase):
    """
    Tests the Linguist's Registry.
    """

    def test_register(self):
        registry = Registry()
        registry.register('foo', FooModel)
        registry.register('bar', BarModel)
        self.assertEqual(len(registry.identifiers), 2)
        self.assertEqual(len(registry.models), 2)
        self.assertRaises(AlreadyRegistered, registry.register, 'foo', BazModel)
        self.assertRaises(InvalidModel, registry.register, 'cookie', BadModel)

    def test_bulk_register(self):
        registry = Registry()
        registry.bulk_register([('foo', FooModel), ('bar', BarModel)])
        self.assertEqual(len(registry.identifiers), 2)
        self.assertEqual(len(registry.models), 2)
        self.assertRaises(TypeError, registry.bulk_register, 'foo')
        self.assertRaises(TypeError, registry.bulk_register, ('foo', 'bar'))
        self.assertRaises(InvalidModel, registry.bulk_register, [(FooModel, 'foo'), ('bar', BarModel)])
        self.assertRaises(InvalidModel, registry.bulk_register, [('duck', BadModel)])

    def test_unregister(self):
        registry = Registry()
        registry.register('foo', FooModel)
        registry.register('bar', BarModel)
        self.assertEqual(len(registry.identifiers), 2)
        self.assertEqual(len(registry.models), 2)
        registry.unregister('foo')
        self.assertEqual(len(registry.identifiers), 1)
        self.assertEqual(len(registry.models), 1)
        registry.unregister('bar')
        self.assertEqual(len(registry.identifiers), 0)
        self.assertEqual(len(registry.models), 0)
        self.assertRaises(Unregistered, registry.unregister, 'badaboom')

    def test_get_model(self):
        registry = Registry()
        registry.register('foo', FooModel)
        self.assertEqual(registry.get_model('foo'), FooModel)
        self.assertRaises(Unregistered, registry.get_model, BazModel)

    def test_validate_model(self):
        self.assertRaises(InvalidModel, Registry.validate_model, 'string')
        self.assertRaises(InvalidModel, Registry.validate_model, 10)
        self.assertRaises(InvalidModel, Registry.validate_model, BadModel)
        self.assertTrue(Registry.validate_model(FooModel))

    def test_validate_identifier(self):
        registry = Registry()
        registry.register('foo', FooModel)
        self.assertTrue(registry.validate_identifier('foo'))
        self.assertRaises(Unregistered, registry.validate_identifier, 'bar')
