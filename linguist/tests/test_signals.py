# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from ..models import Translation

from .base import BaseTestCase
from .models import BarModel


class SignalsTest(BaseTestCase):
    """
    Tests Linguist Signals.
    """

    def test_post_delete(self):
        self.instance.activate_language('en')
        self.instance.title = 'Hello'
        self.instance.save()

        self.instance.activate_language('fr')
        self.instance.title = 'Bonjour'
        self.instance.save()

        self.assertEqual(Translation.objects.count(), 2)

        bar_instance = BarModel()
        bar_instance.activate_language('fr')
        bar_instance.title = 'Bonjour'
        bar_instance.save()

        self.assertEqual(Translation.objects.count(), 3)

        self.instance.delete()
        self.assertEqual(Translation.objects.count(), 1)

        bar_instance.delete()
        self.assertEqual(Translation.objects.count(), 0)
