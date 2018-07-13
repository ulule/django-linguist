# -*- coding: utf-8 -*-
from mock import Mock

from linguist.tests.base import BaseTestCase


class PreSaveTest(BaseTestCase):
    def setUp(self):
        self.old_pre_save = self.instance.get_field_object("title", "fr").pre_save
        self.mock_pre_save = Mock()
        self.instance.get_field_object("title", "fr").pre_save = self.mock_pre_save

    def tearDown(self):
        self.instance.get_field_object("title", "fr").pre_save = self.old_pre_save

    def test_pre_save_called(self):
        self.instance.activate_language("fr")

        # create
        self.instance.title = "Hello"
        self.mock_pre_save.return_value = "Hello"
        self.instance.save()
        assert self.mock_pre_save.call_count == 1

        # update
        self.instance.title = "Goodbye"
        self.mock_pre_save.return_value = "Goodbye"
        self.instance.save()
        assert self.mock_pre_save.call_count == 2

        # delete
        self.instance.title = None
        self.mock_pre_save.return_value = None
        self.instance.save()
        assert self.mock_pre_save.call_count == 3
