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
Record each page publish change.

This is a log of what happened and is NOT an undo and redo functionality.

"""

from django.db.models import *

from django.utils.translation import ugettext_lazy as _, get_language
from django.contrib.auth import get_user_model
from django.dispatch import receiver
from django.conf import settings

from cms.models import Page, CMSPlugin

def get_deleted_user():
    """Replace user when needed"""
    return get_user_model().objects.get_or_create(username='deleted')[0]

REMOVABLE_USER = dict(on_delete=SET(get_deleted_user))
REMOVABLE_PAGE = dict(on_delete=SET_NULL, null=True)


class EditHistory(Model):
    user = ForeignKey(settings.AUTH_USER_MODEL, **REMOVABLE_USER)
    page = ForeignKey(Page, related_name='edit_history', **REMOVABLE_PAGE)
    date = DateTimeField(auto_now=True, db_index=True)

    # We're not linking the plugin with a foreign key, we don't
    # want history to disappear when plugins are deleted.
    plugin_id = IntegerField(db_index=True)
    comment = CharField(_("User Comment"), max_length=255, null=True)
    content = TextField(_("Current Plugin Content"))
    language = CharField(_("Plugin Language"), max_length=8,
        null=True, choices=settings.LANGUAGES)

    published_in = ForeignKey('PublishHistory',
        related_name='editings', null=True, blank=True)

    class Meta:
        ordering = ('-date',)
        get_latest_by = 'date'

    def __str__(self):
        return "%d/%d/%s/%s" % (self.pk, self.page_id, self.date.isoformat(), self.user_id)


class PublishHistory(Model):
    user = ForeignKey(settings.AUTH_USER_MODEL, **REMOVABLE_USER)
    page = ForeignKey(Page, related_name='publish_history', **REMOVABLE_PAGE)
    date = DateTimeField(auto_now=True, db_index=True)

    language = CharField(_("Page Language"), max_length=8,
        null=True, choices=settings.LANGUAGES)

    def __str__(self):
        return "Page %d published on %s by %s" % (
            self.page_id, str(self.date), self.user_id)

    class Meta:
        ordering = ('-date',)
        get_latest_by = 'date'


