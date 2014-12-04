# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import six


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
    def models(self):
        """
        Returns registered models (as list).
        """
        return self._registry.values()

    @staticmethod
    def validate_model(model):
        """
        Validates the given model.

        This model must be a ``django.db.models.Model`` class.
        If this model is a valid class, just returns ``True``.
        Otherwise, raises ``exceptions.InvalidModel``.

        Example::

            registry.validate_model(FooModel) # True if django.db.models.Model
            registry.validate_model(StupidClass) # Raises InvalidModel

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

    def register(self, identifier, model):
        """
        Registers the given ``identifier`` associated to the given ``model``.

        * ``identifier`` must be a string (will be unique)
        * ``model`` must be a ``django.db.models.Model`` class

        Example::

            registry.register('foo', FooModel)

        """
        from django.db import models
        from .exceptions import AlreadyRegistered

        model_name = model.__class__.__name__

        if identifier in self.identifiers:
            raise AlreadyRegistered(
                'Model identifier "%s" is already registered' % identifier)

        self.validate_model(model)
        self._registry[identifier] = model

    def bulk_register(self, models):
        """
        Bulk registers the given list of (``identifier``, ``model``) in the
        registry. Same as ``register`` but performs on a list instead of having
        to register each one individually.

        Example::

            MODELS = [
                ('foo', FooModel),
                ('bar', BarModel),
                ('baz', BazModel),
            ]

            registry.bulk_register(MODELS)

        """
        err_msg = 'bulk_register takes a list or tuple of (identifier, model)'

        if not isinstance(models, (list, tuple)):
            raise TypeError(err_msg)

        for model in models:
            if len(model) != 2:
                raise TypeError(err_msg)
            self.register(model[0], model[1])

    def unregister(self, identifier):
        """
        Unregisters the model associated to the given ``identifier``.

        If ``identifier`` does not exist, raises ``exceptions.Unregistered``.

        Example::

            registry.register('foo', FooModel)
            len(registry.models) # Returns 1
            registry.unregister('foo')
            len(registry.models) # Returns 0

            registry.unregister('unknown') # Raises Unregistered

        """
        self.validate_identifier(identifier)
        del self._registry[identifier]

    def get_model(self, identifier):
        """
        Returns the model associated with the given ``identifier``.

        If ``identifier`` does not exist, raises ``exceptions.Unregistered``.

        Example::

            registry.register('foo', FooModel)
            registry.get_model('foo') # Returns FooModel
            registry.get_model('unknown') # Raises Unregistered

        """
        self.validate_identifier(identifier)
        return self._registry[identifier]

    def validate_identifier(self, identifier):
        """
        Checks if the given ``identifier`` is registered. If it exists, returns
        ``True``. Otherwise, raises ``exceptions.Unregistered``.

        Example::

            registry.register('foo', FooModel)
            registry.validate_identifier('foo') # Returns True
            registry.validate_identifier('unknown') # Raises Unregistered

        """
        from .exceptions import Unregistered

        if identifier not in self.identifiers:
            raise Unregistered(
                'Model identifier "%s" has not been registered' % identifier)

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
