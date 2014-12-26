# -*- coding: utf-8 -*-
from __future__ import unicode_literals


class LinguistRegistry(object):
    """
    Linguist Registry.
    """

    def __init__(self):
        """
        Initializes a new registry.
        """
        self._registry = {}

    @property
    def identifiers(self):
        """
        Returns registered identifiers (as list).
        """
        return self._registry.keys()

    @property
    def translations(self):
        """
        Returns registered translation classes (as list).
        """
        return self._registry.values()

    def register(self, translations):
        """
        Registers the given ``translations`` classes which must be a subclass of
        ``base.ModelTranslationBase``.
        """
        from .descriptors import contribute_to_model

        if not isinstance(translations, (list, tuple)):
            translations = [translations]

        for translation in translations:
            self.validate_translation(translation)
            contribute_to_model(translation)
            self._registry[translation.identifier] = translation

    def unregister(self, identifier):
        """
        Unregisters the translation class with the given ``identifier``.
        If ``identifier`` does not exist, raises ``exceptions.Unregistered``.
        """
        self.validate_identifier(identifier)
        del self._registry[identifier]

    def get_translation(self, identifier):
        """
        Returns the translation class with the given ``identifier``.
        If ``identifier`` does not exist, raises ``exceptions.Unregistered``.
        """
        self.validate_identifier(identifier)
        return self._registry[identifier]

    def validate_model(self, model):
        """
        Validates the given model.

        This model must be a ``django.db.models.Model`` class.
        If this model is a valid class, just returns ``True``.
        Otherwise, raises ``exceptions.InvalidModel``.
        """
        import types
        from django.db import models
        from .exceptions import InvalidModel

        err_msg = 'Class "%s" is not a subclass of django.db.models.Model'

        if not isinstance(model, (type, types.ClassType)):
            raise InvalidModel(err_msg % model)

        if not issubclass(model, models.Model):
            raise InvalidModel(err_msg % model.__class__.__name__)

        return True

    def validate_identifier(self, identifier, in_registered=False):
        """
        Checks if the given ``identifier`` is either ``in_registered`` or not.
        Otherwise, raises ``Unregistered`` or  ``AlreadyRegistered``
        """
        from django.utils.six import string_types
        from .exceptions import AlreadyRegistered, Unregistered

        if not isinstance(identifier, string_types):
            raise TypeError('Identifier must be a string')

        if len(identifier) > 100:
            raise TypeError('Identifier cannot have more than 100 characters')

        if in_registered:
            if identifier in self.identifiers:
                raise AlreadyRegistered(
                    'Model identifier "%s" is already registered' % identifier)
        else:
            if identifier not in self.identifiers:
                raise Unregistered(
                    'Model identifier "%s" has not been registered' % identifier)

        return True

    def validate_translation(self, translation):
        """
        Checks if the given ``translation`` class is a valid one.
        If it is valid one, returns ``True``.
        Otherwise, raises ``InvalidModelTranslation``
        """
        from .base import ModelTranslationBase
        from .exceptions import InvalidModelTranslation

        err_msg = ('The model translation is not a subclass of '
                  'linguist.base.ModelTranslationBase')

        if not issubclass(translation, ModelTranslationBase):
            raise InvalidModelTranslation(err_msg)

        self.validate_identifier(translation.identifier, in_registered=True)
        self.validate_model(translation.model)

        return True


def _autodiscover(registry):
    import copy
    from django.conf import settings
    from django.utils.importlib import import_module
    from django.utils.module_loading import module_has_submodule

    for app in settings.INSTALLED_APPS:
        mod = import_module(app)
        try:
            before_import_registry = copy.copy(registry)
            import_module('%s.linguist_registry' % app)
        except:
            registry = before_import_registry
            if module_has_submodule(mod, 'linguist_registry'):
                raise


registry = LinguistRegistry()


def autodiscover():
    _autodiscover(registry)


def register(*args, **kwargs):
    return registry.register(*args, **kwargs)
