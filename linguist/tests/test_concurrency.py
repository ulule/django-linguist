# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import threading

from ..models import Translation

from .base import BaseTransactionTestCase
from .models import SlugModel


def test_concurrently(times):
    def test_concurrently_decorator(test_func):
        def wrapper(*args, **kwargs):
            exceptions = []

            def call_test_func():
                try:
                    test_func(*args, **kwargs)
                except Exception as e:
                    exceptions.append(e)
                    raise

            threads = []
            for i in range(times):
                threads.append(threading.Thread(target=call_test_func))
            for t in threads:
                t.start()
            for t in threads:
                t.join()
            if exceptions:
                raise Exception(
                    "test_concurrently intercepted %s exceptions: %s"
                    % (len(exceptions), exceptions)
                )

        return wrapper

    return test_concurrently_decorator


class ConcurrentTest(BaseTransactionTestCase):
    """
    Tests the Linguist's manager mixin.
    """

    def test_concurrent_save(self):
        @test_concurrently(10)
        def create_translations(instance):
            languages = ("en", "fr", "it", "de", "pt")
            for language in languages:
                instance.activate_language(language)
                instance.title = "Title in %s" % language
                instance.save()

        instance = SlugModel()
        instance.slug = "foobarslug"
        instance.save()

        instance = SlugModel.objects.get(slug="foobarslug")
        create_translations(instance)

        self.assertTrue(Translation.objects.count() <= 5)
