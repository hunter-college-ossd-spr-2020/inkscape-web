#
# Copyright 2016, Maren Hachmann <marenhachmann@yahoo.com>
#                 Martin Owens <doctormo@gmail.com>
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
Some useful base test tools to help django testing.
"""

# FLAG: do not report failures from here in tracebacks
# pylint: disable=invalid-name
__unittest = True

import os
import sys
import types
import shutil
import inspect

from urllib import urlencode

from os.path import basename, dirname, join, abspath, isfile
from datetime import date
from importlib import import_module

from unittest.case import SkipTest

from django.test import TestCase
from django.test.utils import override_settings

from django.db.models import Model
from django.core.urlresolvers import reverse
from django.core.management import call_command
from django.core.files.base import File
from django.conf import settings
from django.http import HttpRequest

from django.contrib.auth import get_user_model

try:
    import haystack
except ImportError:
    haystack = None


class ExtraTestCase(TestCase):
    """
    Sets the MEDIA_ROOT location to a test location, copies in media files
    used in fixtures and provides an easy way to load files, objects and test
    GET and POST requests and their responses.
    """
    override_settings = {}

    @classmethod
    def setUpClass(cls, *args, **kwargs):
        tdir = dirname(inspect.getfile(cls))
        cls.app_dir = dirname(tdir) if basename(tdir) == 'tests' else tdir
        cls.fixture_dir = os.path.join(cls.app_dir, 'fixtures')
        cls.source_dir = os.path.join(cls.fixture_dir, 'media')

        super(ExtraTestCase, cls).setUpClass(*args, **kwargs)
        cls.media_root = settings.MEDIA_ROOT.rstrip('/')
        if not cls.media_root.endswith('_test'):
            cls.media_root += '_test'
        if not os.path.isdir(cls.media_root):
            os.makedirs(cls.media_root)

        cls._et_overridden = override_settings(
            MEDIA_ROOT=cls.media_root,
            HAYSTACK_CONNECTIONS={
              'default': {
                'ENGINE': 'haystack.backends.whoosh_backend.WhooshEngine',
                'STORAGE': 'ram'
              },
            },
            **cls.override_settings
        )
        cls._et_overridden.enable()

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls._et_overridden, 'wrapper'):
            cls._et_overridden.disable()
        super(ExtraTestCase, cls).tearDownClass()

    @classmethod
    def get_app_dir(cls):
        """Returns the root directory of an app based on the test case location"""
        return cls.app_dir

    def setUp(self):
        "Creates a dictionary containing a default post request for resources"
        super(ExtraTestCase, self).setUp()
        if os.path.isdir(self.source_dir):
            for fname in os.listdir(self.source_dir):
                source = os.path.join(self.source_dir, fname)
                target = os.path.join(self.media_root, fname)
                if not isfile(target) and isfile(source):
                    shutil.copy(source, target)

        client = import_module(getattr(
            settings, 'SESSION_CLIENT', 'django.test.client'))
        self.client = client.Client()
        self.user = None

        if hasattr(self, 'credentials'):
            self.assertTrue(self.client.login(**self.credentials),
                    "User not logged in as expected")
            self.request = self.client.request
            self.session = self.client.session
            self.user = get_user_model().objects.get(
                    username=self.credentials['username'])

    def open(self, filename, *args, **kw):
        """Opens a file relative to this test script.

        *args go to open(), **kwargs go to File() e.g:
        
        self.open('foo.xml', 'rb', name='bar.xml')

        """
        fn = filename
        if not '/' in filename:
            filename = join(self.source_dir, fn)
            if not isfile(filename):
                filename = join(self.source_dir, 'test', fn)
        if not isfile(filename):
            raise IOError("Can't open file: %s (%s)" % (filename, fn))
        return File(open(filename, *args), **kw)

    def getObj(self, qs, **kw):
        """
        Get an object from django, assert it exists, return it.

        qs      - a QuerySet or Model class
        count   - number of objects to get (default: 1)
        **kw    - filter to run (default: None)

        Filters are combination of positive fields=value in kwargs
        and not_field=value for exclusion in the same dictionary.
        """
        count = kw.pop('count', 1)

        # Is the queryset a class? It's probably a model class
        if isinstance(qs, (types.TypeType, types.ClassType)):
            qs = qs.objects.all()

        for (field, value) in kw.items(): 
            if field[:4] != 'not_':
                qs = qs.filter(**{field: value})
            else:
                qs = qs.exclude(**{field[4:]: value})

        # Assert we have enough objects to return
        self.assertGreater(qs.count(), count - 1,
            "%d object(s) matching %s not found." % (count, unicode(kw)))

        # Return either one object or a list of objects limited to count
        return qs[0] if count == 1 else qs[:count]

    def contextData(self, response, field, default=None):
        """Returns a context data field from a response, returns default if provided."""
        for i, context in enumerate(list(response.context or [])):
            if field not in context:
                continue
            return context[field]
        return default

    def assertGet(self, url_name, *arg, **kw):
        """Make a generic GET request with the best options
        
        url_name - Direct /path/, url name or object of the request.
        *args - Argument list to pass to the url reverse method.
        **kw - Keyword Arguments to pass to the url reverse method.

        query - Query string to append to the url (dictionary or url encoded string)
        follow - Should redirects be followed (default True)
        status - The Http status to expect (default: no-check)

        Returns response.
        """
        data = kw.pop('data', {})
        method = kw.pop('method', self.client.get)
        follow = kw.pop('follow', True)
        status = kw.pop('status', None)
        query = kw.pop('query', None)

        if isinstance(url_name, Model):
            url = url_name.get_absolute_url()
        elif url_name[0] == '/' or '://' in url_name:
            url = url_name
        else:
            url = reverse(url_name, kwargs=kw, args=arg)

        if isinstance(query, dict):
            query = urlencode(query)
        if query:
            url += '?' + query

        response = method(url, data, follow=follow)
        if status:
            self.assertEqual(response.status_code, status,
                "URL '%s' returned %s, but we expected %s" % \
                        (url, response.status_code, status))
        return response

    def assertPost(self, *arg, **kw):
        """Make a generic POST request with the best options

        url_name - Either /path/ or url name of the request.
        *args - Argument list to pass to the url reverse method.
        **kw - Keyword Arguments to pass to the url reverse method.
        q - Query string to append to the url (dictionary or string)

        follow - Should redirects be followed (default True)

        status - The Http status to expect (default: no-check)
        form_errors - A dictionary of expected errors (if any)
        data - Post data to submit in the request
        form - Form to use as the basis for the data
        get - Previous get request to find a form in for data.

        Returns response.
        """
        errs = kw.pop('form_errors', {})

        # Get a possible form from a previous get request
        if 'get' in kw:
            form = self.contextData(kw.pop('get'), 'form')
            if form is not None:
                kw['form'] = form

        # Use a previous form as a basis for the data
        if 'form' in kw:
            data = kw.pop('form').initial
            data = dict([(a,b) for (a,b) in data.items() if b])
            data.update(kw.pop('data', {}))
            kw['data'] = data

        kw['method'] = self.client.post
        response = self.assertGet(*arg, **kw)

        form = self.contextData(response, 'form')
        if form is not None:
            err_only = errs.pop('_default', 'No error specified.')
            # Look for form errors and confirm them
            for field in form.errors:
                msg = errs.pop(field, err_only)
                if msg is not None:
                    self.assertFormError(response, 'form', field, msg)
            for field, msg in errs.items():
                self.assertFormError(response, 'form', field, msg)

        return response

    def assertBoth(self, *args, **kw):
        """
        Make a GET and POST request and expect the same status.

        Feeds forum data from the GET into the POST, you can update this
        dictionary as needed using the kwargs 'data' and look for
        form_errors as in assertPost.
        
        Returns (get, post) response tuple
        
        (see assertGet and assertPost for details)
        """
        post_kw = kw.copy()
        for key in ('form_errors', 'data'):
            kw.pop(key, None)
        get = self.assertGet(*args, **kw)
        post_kw['get'] = get
        return (get, self.assertPost(*args, **post_kw))

    def assertThenSkip(self, result, reason=None):
        if not reason:
            reason = "skipping test"
        if result:
            raise SkipTest(reason)


class MultipleFailureTestCase(ExtraTestCase):
    """Each test function is treated as an iterator, returning multiple failures

    You can raise a failure or error as usual for a single error.

    Or you can yield errors as needed
    """
    def __call__(self, result=None):
        """Wrapper for TestCase run to inject test call"""
        self._innerMethodName = self._testMethodName
        self._testMethodName = 'catch_test_call'
        self._currentResult = result if result is not None else self.defaultTestResult()
        super(MultipleFailureTestCase, self).__call__(result=result)
        self._testMethodName = self._innerMethodName

    def catch_test_call(self):
        """
        Called instead of test method and watches for a generator or iterator
        """
        innerMethod = getattr(self, self._innerMethodName)
        ret = innerMethod()

        if isinstance(ret, types.GeneratorType):
            ok = True
            for name, failure in ret:
                self._testMethodName = name
                try:
                    if failure is not None:
                        ok = False
                        raise failure
                    self._currentResult.addSuccess(self)
                except self.failureException:
                    self._currentResult.addFailure(self, sys.exc_info())
                except SkipTest as e:
                    self._addSkip(self._currentResult, unicode(e))
                except Exception:
                    self._currentResult.addError(self, sys.exc_info())

            self.assertTrue(ok, "One or more sub-tests generated a failure.")


class HaystackTestCase(ExtraTestCase):
    """Access haystack as if it were indexed and ready for your test"""
    def setUp(self):
        super(HaystackTestCase, self).setUp()
        haystack.connections.reload('default')
        call_command('update_index', interactive=False, verbosity=0)

    def tearDown(self):
        super(HaystackTestCase, self).tearDown()
        call_command('clear_index', interactive=False, verbosity=0)

