# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from .base import BaseTestCase

from .translations import FooModel


class ManagerMixinTest(BaseTestCase):
    """
    Tests the Linguist's manager mixin.
    """

    def setUp(self):
        self.create_registry()

    def test_with_translations(self):
        self.assertTrue(hasattr(FooModel.objects, 'with_translations'))
        FooModel.objects.with_translations()
        for obj in FooModel.objects.all():
            self.assertTrue(obj.cached_translation_count > 0)
