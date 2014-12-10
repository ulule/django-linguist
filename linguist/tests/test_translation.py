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

    def test_fields(self):
        r = Registry()
        r.register(FooTranslation)
        for language in LANGUAGES:
            self.assertIn('title_%s' % language, dir(FooModel))

    def test_getter_setter(self):
        r = Registry()
        r.register(FooTranslation)
        m = FooModel()

        with self.assertNumQueries(3):
            # one query to save model object
            m.title = 'hello'
            m.save()
            # get + create of translation object
            m.title_fr = 'bonjour'

        m.title_fr = 'bonjour bonjour'

        o = FooModel.objects.all()[0]
        self.assertEqual(o.title, 'hello')
        self.assertEqual(o.title_fr, 'bonjour bonjour')



    def test_prefetch_translations(self):
        r = Registry()
        r.register(FooTranslation)
        m = FooModel()
        self.assertTrue(hasattr(m, 'prefetch_translations'))

        m.title = 'hello'
        m.save()
        m.title_fr = 'bonjour'
        m.title_en = 'Hello'

        # reset cache
        m._linguist = {}

        with self.assertNumQueries(2):
            string = '%s_%s' % (m.title_fr, m.title_en)  # noqa

        m.prefetch_translations()
        with self.assertNumQueries(0):
            string = '%s_%s' % (m.title_fr, m.title_en)  # noqa
