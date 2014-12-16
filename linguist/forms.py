# -*- coding: utf-8 -*_
from django import forms
from django.forms.models import BaseInlineFormSet

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


class ModelTranslationInlineFormSet(BaseInlineFormSet):

    language = None

    def _construct_form(self, i, **kwargs):
        form = super(ModelTranslationInlineFormSet, self)._construct_form(i, **kwargs)
        form.language = self.language
        return form

    def save_new(self, form, commit=True):
        obj = super(ModelTranslationInlineFormSet, self).save_new(form, commit)
        return obj
