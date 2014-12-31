# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db.models.signals import post_delete
from django.dispatch import receiver

from ..models import Translation

from .base import BaseTestCase
from .translations import FooModel


class SignalsTest(BaseTestCase):
    """
    Tests Linguist Signals.
    """

    def setUp(self):
        self.create_registry()
        self.deleted_count = 0
        post_delete.connect(self.post_delete_listener, sender=FooModel)

    def post_delete_listener(self, sender, instance, **kwargs):
        self.deleted_count += 1

    def test_post_delete(self):
        self.instance.language = 'en'
        self.instance.title = 'Hello'
        self.instance.save()

        self.instance.language = 'fr'
        self.instance.title = 'Bonjour'
        self.instance.save()

        self.assertEqual(Translation.objects.count(), 2)
        self.assertEqual(self.deleted_count, 0)

        self.instance.delete()
        self.assertEqual(self.deleted_count, 1)
        self.assertEqual(Translation.objects.count(), 0)
