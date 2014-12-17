# -*- coding: utf-8 -*_
from django import forms

from .utils.i18n import get_language

__all__ = [
    'ModelTranslationFormMixin',
    'ModelTranslationForm',
]


class ModelTranslationFormMixin(object):

    def __init__(self, *args, **kwargs):
        super(ModelTranslationFormMixin, self).__init__(*args, **kwargs)
        self.language = None
        instance = kwargs.get('instance', None)
        if self.language is None:
            self.language = instance.language if instance else get_language()


class ModelTranslationForm(ModelTranslationFormMixin, forms.ModelForm):
    pass
