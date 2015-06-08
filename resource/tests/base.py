#
# Copyright 2015, Maren Hachmann <removemarenhachmannthis@yahoo.com>
#                 Martin Owens <doctormo@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
"""
Base TestCase for Resource and Gallery Tests.
"""
import os

from datetime import date

from django.test import TestCase
from django.contrib.auth import authenticate
from django.core.urlresolvers import reverse

from user_sessions.backends.db import SessionStore
from user_sessions.utils.tests import Client

from django.http import HttpRequest
from django.conf import settings

class BaseCase(TestCase):
    fixtures = ['test-auth', 'licenses', 'categories', 'quota', 'resource-tests']

    def open(self, filename, *args):
        "Opens a file relative to this test script"
        return open(os.path.join(os.path.dirname(__file__), filename), *args)

    def _get(self, url_name, *arg, **kw):
        "Make a generic GET request with the best options"
        data = kw.pop('data', {})
        method = kw.pop('method', self.client.get)
        follow = kw.pop('follow', True)
        get_param = kw.pop('get_param', None)
        url = reverse(url_name, kwargs=kw, args=arg)
        if get_param:
            url += '?' + get_param 
        return method(url, data, follow=follow)
      
    def _post(self, *arg, **kw):
        "Make a generic POST request with the best options"
        kw['method'] = self.client.post
        return self._get(*arg, **kw)

    def set_session_cookies(self):
        """Set session data regardless of being authenticated"""

        # Save new session in database and add cookie referencing it
        request = HttpRequest()
        request.session = SessionStore('Python/2.7', '127.0.0.1')

        # Save the session values.
        request.session.save()

        # Set the cookie to represent the session.
        session_cookie = settings.SESSION_COOKIE_NAME
        self.client.cookies[session_cookie] = request.session.session_key
        cookie_data = {
            'max-age': None,
            'path': '/',
            'domain': settings.SESSION_COOKIE_DOMAIN,
            'secure': settings.SESSION_COOKIE_SECURE or None,
            'expires': None,
        }
        self.client.cookies[session_cookie].update(cookie_data)

    def setUp(self):
        "Creates a dictionary containing a default post request for resources"
        super(TestCase, self).setUp()
        self.client = Client()
        self.download = self.open('../fixtures/media/test/file5.svg')
        self.thumbnail = self.open('../fixtures/media/test/preview5.png')
        self.data = {
          'download': self.download, 
          'thumbnail': self.thumbnail,
          'name': 'Test Resource Title',
          'link': 'http://www.inkscape.org',
          'desc': 'My nice picture',
          'category': 2,
          'license': 4,
          'owner': 'True',
          'published': 'on',
        }
        #self.set_session_cookies() # activate to test AnonymousUser tests, but deactivated mirrors reality

    def tearDown(self):
        super(TestCase, self).tearDown()
        self.download.close()
        self.thumbnail.close()

class BaseUserCase(BaseCase):
    def setUp(self):
        super(BaseUserCase, self).setUp()
        self.user = authenticate(username='tester', password='123456')
        self.client.login(username='tester', password='123456')

