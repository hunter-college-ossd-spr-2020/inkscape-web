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
Utility models which store data for the whole website's use.
"""
import json

from django.conf import settings
from django.core.urlresolvers import reverse
from django.db.models import (
    Model, CharField, IntegerField, DateTimeField, TextField, URLField, PositiveIntegerField
)

class Error(Model):
    """Record a unique traceback id for each error"""
    traceback_id = CharField(max_length=255, db_index=True, unique=True)
    traceback = TextField(help_text="Full traceback (json)")
    urls = TextField(help_text="List of URLs implicated (json)")

    name = CharField(max_length=255, help_text="Exception text thrown (first line)")
    description = TextField(help_text="Full exception text.")

    started = DateTimeField(help_text="First time we started to see this error in the logs.")
    ended = DateTimeField(help_text="Last time we saw this error in the logs.")
    count = PositiveIntegerField(default=1, help_text="Number of times seem in logs.")

    issue = URLField(help_text="Location of the error in a bug tracker.", null=True, blank=True)
    fixed = DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ('-count',)

    def __str__(self):
        if self.fixed:
            return "%s (FIXED)" % self.name
        return self.name

    def get_traceback(self):
        """Return the traceback as a structured object"""
        def pkg(item, cls, filename):
            if '/' in filename:
                item['pkg'], item['file'] = filename.split('/', 1)
            else:
                # This happens with xapian haystack backend, no directory
                item['file'] = filename
                item['pkg'] = filename.rsplit('.', 1)[0]
            item['class'] = cls

        for tbk in json.loads(self.traceback):
            if 'site-packages' in tbk['fn']:
                fnm = tbk['fn'].split('site-packages/')[-1]
                cls = 'env' if 'pythonenv' in tbk['fn'] else 'sys'
                pkg(tbk, cls, fnm)
            elif 'python3.6' in tbk['fn']:
                pkg(tbk, 'sys', tbk['fn'].split('python3.6/')[-1])
            elif settings.PROJECT_PATH in tbk['fn']:
                fnm = tbk['fn'].replace(settings.PROJECT_PATH, '')
                pkg(tbk, 'web', fnm)
            elif tbk['fn'].startswith('./'):
                pkg(tbk, 'web', tbk['fn'][2:])
            else:
                tbk['pkg'] = 'unknown'
                tbk['class'] = 'unknown'
                tbk['file'] = tbk['fn']
            yield tbk

    def get_urls(self):
        """Return the urls as a structured object"""
        try:
            return json.loads(self.urls)
        except json.JSONDecodeError:
            return []

    def get_absolute_url(self):
        """Return a link to the error"""
        return reverse('cog:error', kwargs={'slug': self.traceback_id})

class HeartBeat(Model):
    """
    Every command will cause a heartbeat, usually used for tracking cron jobs.
    """
    name = CharField(max_length=128, db_index=True, help_text="Command Name (after manage.py)")
    user = CharField(max_length=128, db_index=True, help_text="User who ran the command.")
    error = TextField(null=True, blank=True, help_text="Any error message from the process.")

    started = DateTimeField(help_text="Date when the command was started")
    ended = DateTimeField(help_text="Date when the command ended", null=True, blank=True)
    status = IntegerField(default=0, help_text="Exit code of the process")

    created = DateTimeField(auto_now_add=True)
    beats = IntegerField(default=1, help_text="Number of times run since creation.")

    class Meta:
        unique_together = ('name', 'user')

    def __str__(self):
        return self.name
