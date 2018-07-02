#
# Copyright 2017, Martin Owens <doctormo@gmail.com>
#
# This file is part of the software inkscape-web, consisting of custom 
# code for the Inkscape project's django-based website.
#
# inkscape-web is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# inkscape-web is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with inkscape-web.  If not, see <http://www.gnu.org/licenses/>.
#
"""
Provide a template tag that allows for translated fields to be looked up.

Assumptions:
  * Target model has related_name 'translations'.
  * Target model and language have unique together set.
  * Target field and translated field have the same name.

{% load i18n_fields %}

{{ object|translate_field:"field_name" }}
"""

from django.utils.translation import get_language
from django.core.exceptions import FieldDoesNotExist
from django.template import TemplateSyntaxError
from django.template import Library
from django.conf import settings

from django.core.cache import caches
CACHE = caches['default']

register = Library()

DEFAULT_LANG = settings.LANGUAGE_CODE.split('-')[0]
OTHER_LANGS = list(i for i in settings.LANGUAGES if i[0].split('-')[0] != DEFAULT_LANG)

CONF_ERR = "Model '{}' is not configured for translations."
FIELD_ERR = "Field '{}.{}' doesn't exist, so it can't be translated."
STR_ERR = "Expected object but got string '{}'"

@register.filter("translate_field")
def translate_field(obj, name):
    if obj in ('', None, 0):
        return obj

    if isinstance(obj, (str, unicode)):
        raise TemplateSyntaxError(STR_ERR.format(obj))

    # Check that this is a translated model
    try:
        Translations = obj.translations.model
    except AttributeError:
        raise TemplateSyntaxError(CONF_ERR.format(type(obj).__name__))

    # Check both target and translation model have the requested field
    for cls in (type(obj), Translations):
        try:
            cls._meta.get_field(name)
        except FieldDoesNotExist:
            raise TemplateSyntaxError(FIELD_ERR.format(cls.__name__, name))

    lang = get_language()
    if lang or lang != DEFAULT_LANG:
        key = '{}.{}.{}'.format(type(obj).__name__, obj.pk, lang)
        tr_obj = CACHE.get(key)
        if tr_obj is None:
            try:
                # Return the translation OR if the translation exists, but the
                # field is blank, return the English version instead.
                tr_obj = obj.translations.get(language=lang)
            except Translations.DoesNotExist:
                tr_obj = False
            CACHE.set(key, tr_obj)
        if tr_obj is False:
            tr_obj = obj

        if hasattr(tr_obj, name):
            return getattr(tr_obj, name)

    # Passthrough, nothing to do here.
    return getattr(obj, name)

