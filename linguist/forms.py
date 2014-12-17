# -*- coding: utf-8 -*_
from django import forms

from .utils.i18n import get_language

__all__ = [
    'ModelTranslationFormMixin',
    'ModelTranslationForm',
]


class ModelTranslationFormMixin(object):

    language = None

    def __init__(self, *args, **kwargs):
        current_language = kwargs.pop('_current_language', None)
        super(ModelTranslationFormMixin, self).__init__(*args, **kwargs)
        instance = kwargs.get('instance', None)
        if self.language is None:
            if instance:
                self.language = instance.language
                return
            self.language = current_language or get_language()

    def _post_clean(self):
        self.instance.language = self.language
        super(ModelTranslationFormMixin, self)._post_clean()


class ModelTranslationForm(ModelTranslationFormMixin, forms.ModelForm):
    pass
