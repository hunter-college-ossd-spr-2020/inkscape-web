#
# Copyright 2016, Martin Owens <doctormo@gmail.com>
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
Some generic utilities for improving caching and other core features
"""
import urllib
from io import StringIO

from django.conf import settings
from django.core.exceptions import FieldDoesNotExist
from django.core.files.storage import FileSystemStorage, File

from django.db.models.lookups import Exact
from django.db.models.expressions import Col

from django.template.context import Context

def to(t=list):
    """Create an object from a generator function, default is list"""
    def _outer(f):
        def _inner(*args, **kwargs):
            return t(f(*args, **kwargs))
        return _inner
    return _outer


def context_items(context):
    """Unpack a django context, equiv of dict.items()"""
    if not isinstance(context, Context):
        context = [context]
    for d in context:
        for (key, value) in d.items():
            yield (key, value)

def language_alternator(lang_code, translations=None):
    """
    Generate a list of language alternatives for the given lang_code, for example es_MX
    will yield es-mx, es, en.

    translations - A dictionary containing alternatives, in the given example above if
                   the alternatives is set as {'es-mx': 'es-al', 'es': 'fr'} it will
                   yield es-al, fr, en instead.
                   Default: settings.LANGUAGE_ALTERNATIVES
    """
    if translations is None:
        translations = getattr(settings, 'LANGUAGE_ALTERNATIVES', {})
    lang_name = lang_code.replace('_', '-').lower()
    lang_prefix = lang_name.split('-', 1)[0].split('@')[0]
    for lang in dict.fromkeys([
            lang_name, translations.get(lang_name, lang_name),
            lang_prefix, translations.get(lang_prefix, lang_prefix), 'en']):
        yield lang

class MonkeyCache(object):
    """Cache the response from the function perminantly (once per thread)"""
    def __init__(self, func, keys=()):
        self.func = func
        self.keys = keys
        self.cache = {}

    @staticmethod
    def get_key(key, args, kwargs):
        """Convert args in a crude caching key"""
        if isinstance(key, int):
            if key < len(args):
                return str(args[key])
            return ''
        return str(kwargs[str(key)])

    def __call__(self, *args, **kwargs):
        key = "-".join([self.get_key(key, args, kwargs) for key in self.keys])
        if key not in self.cache:
            self.cache[key] = self.func(*args, **kwargs)
        return self.cache[key]

class QuerySetWrapper(object):
    """
    When wrappd around a django QuerySet object using the clone method
    this class will provide you a callback mechanism so every consumed
    iterator will call the method given as it's consumed.

    This is helpful because a queryset might contain thousands of possible
    objects but the template may only consume twenty on a page. We can now
    get a callback for each of those twenty consumed objects, no matter
    what page is being requested.

    Use:

    def func(obj, **kwargs):
        # perhaps action here

    qs._clone(klass=QuerySetWrapper, method=func, [kwargs={...}])

    """
    def iterator(self):
        for obj in super(QuerySetWrapper, self).iterator():
            if self.method is not None:
                self.method(obj, **getattr(self, 'kwargs', {}))
            yield obj

    def _clone(self, klass=None, setup=False, **kwargs):
        c = super(QuerySetWrapper, self)._clone(klass, **kwargs)
        c.method = self.method
        c.kwargs = getattr(self, 'kwargs', {})
        return c

    def __getstate__(self):
        odict = self.__dict__.copy()
        del odict['method']
        return odict

    def __setstate__(self, args):
        args['method'] = None
        self.__dict__.update(args)

    def get_basic_filter(self):
        """Generator of field/values for all exact matchs in this qs"""
        for child in self.query.where.children:
            if isinstance(child, Exact) and \
               isinstance(child.lhs, Col) and not isinstance(child.rhs, Col):
                ret = self._basic_filter(child.lhs.target, child.rhs, child.lhs.alias)
                if ret:
                    yield ret

    def _basic_filter(self, target, value, alias=None):
        name = None
        if self.model == target.model:
            name = target.name
        elif target.model._meta._forward_fields_map[target.name].unique:
            # For fields like slug, id and other unqiue fields
            name = alias.split('_', 1)[-1]
            try:
                field = self.model._meta.get_field_by_name(name)
            except FieldDoesNotExist:
                return

            qs = target.model.objects.filter(**{target.name: value})
            if qs.count() == 0:
                return

            value = qs.values_list('pk', flat=True)[0]

        if name:
            return (name, value)


class BaseMiddleware(object):
    """
    When used by a middleware class, provides a predictable get()
    function which will provide the first available variable from
    first the context_data, then the view, then the middleware.
    """
    def get(self, data, key, default=None, then=None):
        """Returns a data key from the context_data, the view, a get
        method on the view or a get method on the middleware in that order.
        
        Returns default (None) if all fail."""
        if key in data:
            return data[key]
        view = data.get('view', None)
        if hasattr(view, key):
            return getattr(view, key)
        if hasattr(view, 'get_'+key):
            return getattr(view, 'get_'+key)()
        if hasattr(then, 'get_'+key):
            return getattr(then, 'get_'+key)(data)
        return default

class ReplaceStore(FileSystemStorage):
    """Allow filenames to replace when saving"""
    def get_available_name(self, name, max_length=255):
        """Always return the exact name, never change it"""
        return name

    def _save(self, name, content):
        """Delete the existing file if it already exists"""
        if self.exists(name):
            self.delete(name)
        return super(ReplaceStore, self)._save(name, content)

class URLFile(File):
    """Takes a url and attempts to download it"""
    def __init__(self, url):
        self.response = urllib.request.urlopen(url)
        if 'content-length' in self.response.headers:
            self.size = self.response.headers['content-length']
        super(URLFile, self).__init__(self.response)

    def _get_size_from_underlying_file(self):
        """Called when content-length was not returned with response"""
        content = self.response.read()
        self.file = StringIO(content)
        self.size = len(content)
        return self.size
