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

    def test_add_fields_to_model(self):
        r = Registry()
        r.register(FooTranslation)
        for language in LANGUAGES:
            self.assertIn('title_%s' % language, dir(FooModel))

    def test_field_values(self):
        r = Registry()
        r.register(FooTranslation)
        m = FooModel()
        m.title = 'hello'
        m.save()
        m.title_fr = 'bonjour'
        m.save()
        o = FooModel.objects.all()[0]
        self.assertEqual(o.title, 'hello')
        self.assertEqual(o.title_fr, 'bonjour')
