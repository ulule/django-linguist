# -*- coding: utf-8 -*-
import collections
import copy
import itertools

from importlib import import_module

from django.db.models import QuerySet
from django.core import exceptions
from django.utils.encoding import force_text
from django.utils.functional import lazy
from django.utils.translation import get_language as _get_language

from . import settings


CLASS_PATH_ERROR = "django-linguist is unable to interpret settings value for %s. " "%s should be in the form of a tupple: " "('path.to.models.Class', 'app_label')."


def get_language_name(code):
    languages = dict(
        (lang_code, lang_name) for lang_code, lang_name in settings.SUPPORTED_LANGUAGES
    )
    return languages.get(code)


def get_language():
    """
    Returns an active language code that is guaranteed to be in
    settings.SUPPORTED_LANGUAGES.
    """
    lang = _get_language()

    if not lang:
        return get_fallback_language()

    langs = [l[0] for l in settings.SUPPORTED_LANGUAGES]
    if lang not in langs and "-" in lang:
        lang = lang.split("-")[0]

    if lang in langs:
        return lang

    return settings.DEFAULT_LANGUAGE


def get_fallback_language():
    """
    Returns the fallback language.
    """
    return settings.DEFAULT_LANGUAGE


def get_real_field_name(field, lang=None):
    if lang is None:
        lang = get_language()
    return str("%s_%s" % (field, lang.replace("-", "_")))


def get_fallback_field_name(field):
    return get_real_field_name(field, lang=get_fallback_language())


def get_supported_languages():
    """
    Returns supported languages list.
    """
    return [code.replace("-", "_") for code, name in settings.SUPPORTED_LANGUAGES]


def get_language_fields(fields):
    """
    Takes a list of fields and returns related language fields.
    """
    return [
        "%s_%s" % (field, lang)
        for field in fields
        for lang in get_supported_languages()
    ]


def activate_language(instances, language):
    """
    Activates the given language for the given instances.
    """
    language = (
        language if language in get_supported_languages() else get_fallback_language()
    )
    for instance in instances:
        instance.activate_language(language)


def build_localized_field_name(field_name, language=None):
    """
    Build localized field name from ``field_name`` and ``language``.
    """
    if language is None:
        language = get_language()

    return "%s_%s" % (field_name, language.replace("-", "_"))


def _build_localized_verbose_name(verbose_name, language):
    """
    Build localized verbose name from ``verbose_name`` and ``language``.
    """
    return force_text("%s (%s)") % (force_text(verbose_name), language)


build_localized_verbose_name = lazy(_build_localized_verbose_name, str)


def chunks(l, n):
    """
    Yields successive n-sized chunks from l.
    """
    for i in range(0, len(l), n):
        yield l[i: i + n]


def load_class(class_path, setting_name=None):
    """
    Loads a class given a class_path. The setting value may be a string or a
    tuple. The setting_name parameter is only there for pretty error output, and
    therefore is optional.
    """
    if not isinstance(class_path, str):
        try:
            class_path, app_label = class_path
        except Exception:
            if setting_name:
                raise exceptions.ImproperlyConfigured(
                    CLASS_PATH_ERROR % (setting_name, setting_name)
                )
            else:
                raise exceptions.ImproperlyConfigured(
                    CLASS_PATH_ERROR % ("this setting", "It")
                )

    try:
        class_module, class_name = class_path.rsplit(".", 1)
    except ValueError:
        if setting_name:
            txt = "%s isn't a valid module. Check your %s setting" % (
                class_path,
                setting_name,
            )
        else:
            txt = "%s isn't a valid module." % class_path
        raise exceptions.ImproperlyConfigured(txt)

    try:
        mod = import_module(class_module)
    except ImportError as e:
        if setting_name:
            txt = 'Error importing backend %s: "%s". Check your %s setting' % (
                class_module,
                e,
                setting_name,
            )
        else:
            txt = 'Error importing backend %s: "%s".' % (class_module, e)
        raise exceptions.ImproperlyConfigured(txt)

    try:
        clazz = getattr(mod, class_name)
    except AttributeError:
        if setting_name:
            txt = (
                'Backend module "%s" does not define a "%s" class. Check'
                " your %s setting" % (class_module, class_name, setting_name)
            )
        else:
            txt = 'Backend module "%s" does not define a "%s" class.' % (
                class_module,
                class_name,
            )
        raise exceptions.ImproperlyConfigured(txt)
    return clazz


def get_model_string(model_name):
    """
    Returns the model string notation Django uses for lazily loaded ForeignKeys
    (eg 'auth.User') to prevent circular imports.
    This is needed to allow our crazy custom model usage.
    """
    setting_name = "LINGUIST_%s_MODEL" % model_name.upper().replace("_", "")
    class_path = getattr(settings, setting_name, None)
    if not class_path:
        return "linguist.%s" % model_name
    elif isinstance(class_path, str):
        parts = class_path.split(".")
        try:
            index = parts.index("models") - 1
        except ValueError:
            raise exceptions.ImproperlyConfigured(
                CLASS_PATH_ERROR % (setting_name, setting_name)
            )
        app_label, model_name = parts[index], parts[-1]
    else:
        try:
            class_path, app_label = class_path
            model_name = class_path.split(".")[-1]
        except Exception:
            raise exceptions.ImproperlyConfigured(
                CLASS_PATH_ERROR % (setting_name, setting_name)
            )
    return "%s.%s" % (app_label, model_name)


def get_translation_lookup(identifier, field, value):
    """
    Mapper that takes a language field, its value and returns the
    related lookup for Translation model.
    """
    # Split by transformers
    parts = field.split("__")

    # Store transformers
    transformers = parts[1:] if len(parts) > 1 else None

    # defaults to "title" and default language
    field_name = parts[0]
    language = get_fallback_language()

    name_parts = parts[0].split("_")
    if len(name_parts) > 1:
        supported_languages = get_supported_languages()
        last_part = name_parts[-1]
        if last_part in supported_languages:
            # title_with_underscore_fr?
            field_name = "_".join(name_parts[:-1])
            language = last_part
        else:
            # title_with_underscore?
            # Let's use default language
            field_name = "_".join(name_parts)

    value_lookup = (
        "field_value"
        if transformers is None
        else "field_value__%s" % "__".join(transformers)
    )

    lookup = {"field_name": field_name, "identifier": identifier, "language": language}

    lookup[value_lookup] = value

    return lookup


def get_field_name_from_lookup(lookup):
    """
    Returns field name from query lookup.
    """
    return lookup.split("__")[0]


def get_grouped_translations(instances, **kwargs):
    """
    Takes instances and returns grouped translations ready to
    be set in cache.
    """
    grouped_translations = collections.defaultdict(list)

    if not instances:
        return grouped_translations

    if not isinstance(instances, collections.Iterable):
        instances = [instances]

    if isinstance(instances, QuerySet):
        model = instances.model
    else:
        model = instances[0]._meta.model

    instances_ids = []

    for instance in instances:
        instances_ids.append(instance.pk)

        if instance._meta.model != model:
            raise Exception(
                "You cannot use different model instances, only one authorized."
            )

    from .models import Translation

    decider = model._meta.linguist.get("decider", Translation)
    identifier = model._meta.linguist.get("identifier", None)
    chunks_length = kwargs.get("chunks_length", None)

    if identifier is None:
        raise Exception('You must define Linguist "identifier" meta option')

    lookup = dict(identifier=identifier)
    for kwarg in ("field_names", "languages"):
        value = kwargs.get(kwarg, None)
        if value is not None:
            if not isinstance(value, (list, tuple)):
                value = [value]
            lookup["%s__in" % kwarg[:-1]] = value

    if chunks_length is not None:
        translations_qs = []
        for ids in chunks(instances_ids, chunks_length):
            ids_lookup = copy.copy(lookup)
            ids_lookup["object_id__in"] = ids
            translations_qs.append(decider.objects.filter(**ids_lookup))
        translations = itertools.chain.from_iterable(translations_qs)
    else:
        lookup["object_id__in"] = instances_ids
        translations = decider.objects.filter(**lookup)

    for translation in translations:
        grouped_translations[translation.object_id].append(translation)

    return grouped_translations


def set_object_translations_cache(obj, queryset):
    obj.clear_translations_cache()

    if obj.pk in queryset._prefetched_translations_cache:
        for translation in queryset._prefetched_translations_cache[obj.pk]:
            obj._linguist.set_cache(instance=obj, translation=translation)
            obj.populate_missing_translations()
