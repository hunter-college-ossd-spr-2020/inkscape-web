#
# Copyright 2015, Martin Owens <doctormo@gmail.com>
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
Test team functions
"""
from autotest.base import ExtraTestCase

from django.contrib.auth.models import Permission

from ..models import User
from django.contrib.sessions.models import Session

class UserTests(ExtraTestCase):
    fixtures = ('test-auth',)
    credentials = dict(username='admin', password='123456')

    def test_13_user_sessions_removed(self):
        """Sessions are removed when user is deactivated"""
        admin = User.objects.get(username='admin')
        self.assertEqual(Session.objects.all().count(), 1)
        response = self.assertGet('admin:index', status=200, follow=False)

        admin.first_name = 'Nothing'
        admin.save()

        self.assertEqual(Session.objects.all().count(), 1)
        response = self.assertGet('admin:index', status=200, follow=False)

        admin.is_active = False
        admin.save()

        self.assertEqual(Session.objects.all().count(), 0)
        response = self.assertGet('admin:index', status=302, follow=False)

    def test_23_staff_permission(self):
        """Having the staff permission grants staff access"""
        user = User.objects.get(username='staff')
        self.assertFalse(user.has_perm('person.is_staff'))
        self.assertTrue(user.is_admin)
        self.assertTrue(user.is_staff)

        user = User.objects.get(username='tester')
        user.user_permissions.add(Permission.objects.get(codename='is_staff'))

        self.assertTrue(user.has_perm('person.is_staff'))
        self.assertFalse(user.is_admin)
        self.assertTrue(user.is_staff)

