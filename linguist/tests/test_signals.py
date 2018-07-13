# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from exam import around, fixture

from django.db.models.signals import pre_save, post_save

from ..models import Translation

from .base import BaseTestCase
from .models import BarModel


class PostDeleteSignalTest(BaseTestCase):
    """
    Tests Linguist post_delete Signals.
    """

    def test_post_delete(self):
        self.instance.activate_language("en")
        self.instance.title = "Hello"
        self.instance.save()

        self.instance.activate_language("fr")
        self.instance.title = "Bonjour"
        self.instance.save()

        self.assertEqual(Translation.objects.count(), 2)

        bar_instance = BarModel()
        bar_instance.activate_language("fr")
        bar_instance.title = "Bonjour"
        bar_instance.save()

        self.assertEqual(Translation.objects.count(), 3)

        self.instance.delete()
        self.assertEqual(Translation.objects.count(), 1)

        bar_instance.delete()
        self.assertEqual(Translation.objects.count(), 0)


class PrePostSaveSignalsTest(BaseTestCase):
    """
    Tests Linguist with pre_save/post_save Signals.
    """

    @fixture
    def bar(self):
        bar_instance = BarModel()

        bar_instance.activate_language("en")
        bar_instance.title = "Hello"
        bar_instance.save()

        bar_instance.activate_language("fr")
        bar_instance.title = "Bonjour"
        bar_instance.save()

        return bar_instance

    @around
    def pre_post_save_wrapper(self):
        self.pre_save_called = False
        self.post_save_called = False

        self.bar

        def pre_save_handler(sender, instance, **kwargs):
            # Assert that a pre_save handler gets the proper information on which fields have changed
            # (hence the translations have not yet been saved to the db).

            self.pre_save_called = True

            field_fr = instance._linguist_translations["title"].get("fr", None)
            field_en = instance._linguist_translations["title"].get("en", None)

            assert field_fr.has_changed
            assert not field_en.has_changed

        pre_save.connect(pre_save_handler, sender=BarModel)

        def post_save_handler(sender, instance, **kwargs):
            # Assert that a post_save handler that refreshes the model gets the saved translations
            # (hence the translations have been saved to the db).

            self.post_save_called = True

            title_fr = instance.title_fr
            title_en = instance.title_en

            instance = BarModel.objects.get(pk=instance.pk)

            assert instance.title_fr == title_fr
            assert instance.title_en == title_en

        post_save.connect(post_save_handler, sender=BarModel)

        yield

        pre_save.disconnect(pre_save_handler, sender=BarModel)
        post_save.disconnect(post_save_handler, sender=BarModel)

    def test_pre_post_save(self):
        assert self.pre_save_called is False
        assert self.post_save_called is False

        self.bar.activate_language("fr")
        self.bar.title = "Bonjour signal"
        self.bar.save()

        assert self.pre_save_called is True
        assert self.post_save_called is True
