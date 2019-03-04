#
# Copyright 2018, Martin Owens <doctormo@gmail.com>
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
# pylint: disable=too-many-ancestors
"""
Provide a visual of all the errors on the website.
"""

import os
import json
import hashlib

from django.utils.translation import ugettext_lazy as _
from django.views.generic import ListView, DetailView
from django.views.generic.base import RedirectView
from django.views.generic.detail import SingleObjectMixin
from django.core.urlresolvers import reverse
from django.utils.timezone import now
from django.conf import settings

from .parse_errors import parse_stream
from .models import Error

class ErrorDetail(DetailView):
    """View a single error, no updating"""
    slug_field = 'traceback_id'
    model = Error

    def get_parent(self):
        return (reverse('cog:errors'), "Website Errors")

class MarkFixed(SingleObjectMixin, RedirectView):
    """Mark an error as fixed"""
    slug_field = 'traceback_id'
    model = Error

    def get_redirect_url(self, slug):
        """Redirect back to the errors page"""
        obj = self.get_object()
        obj.fixed = now()
        obj.save()
        return reverse('cog:errors')

class ErrorList(ListView):
    """Returns a list of errors on the website"""
    title = _('All Website Errors')
    model = Error

    @staticmethod
    def add_item(item):
        """Count the collected data"""
        if not item['error']:
            return
        obj, created = Error.objects.get_or_create(
                traceback_id=item['key'][:255], defaults={
                'traceback': json.dumps(item['traceback']),
                'urls': json.dumps([item['url']]),
                'name': item['error'][0][:255],
                'description': '\n'.join(item['error']),
                'started': item['datetime'],
                'ended': item['datetime'],
            })
        if not created:
            obj.count += 1
            obj.fixed = None
            obj.started = min(obj.started, item['datetime'])
            obj.ended = max(obj.ended, item['datetime'])
            #obj.urls = list(set(obj.get_urls()) & {item['url']})
            obj.save()
        return obj

    @staticmethod
    def scan_file(filename):
        """Read the given filename for new errors"""
        if not filename or not os.path.isfile(filename):
            return

        pos = 0
        pos_file = filename + '.pos'
        new_hash, old_hash = None, None

        # 1. Load position of last read.
        if os.path.isfile(pos_file):
            with open(pos_file, 'r') as fhl:
                try:
                    data = json.loads(fhl.read())
                    pos = data['pos']
                    old_hash = data['hash']
                except json.JSONDecodeError:
                    pass

        # 2. Load the first part of the file and compile to hash
        with open(filename, 'r') as fhl:
            content = fhl.read(1024)
            if len(content) == 1024:
                new_hash = hashlib.md5(content.encode('utf-8')).hexdigest()

        # 3. If the uuid is different, we have a new file, set pos to 0
        if new_hash != old_hash:
            pos = 0

        # 4. Load data from pos and parse it for errors
        with open(filename, 'r') as fhl:
            fhl.seek(pos)
            yield from parse_stream(fhl)
            pos = fhl.tell()

        # 5. Save position we have finished reading the file at
        with open(pos_file, 'w') as fhl:
            fhl.write(json.dumps({'pos': pos, 'hash': new_hash}))

    def get_queryset(self):
        """Load the errors, but also scan_file them"""
        for item in self.scan_file(getattr(settings, 'ERROR_FILE')):
            self.add_item(item)
        qset = super().get_queryset()
        for sort in self.get_sorting():
            if sort['sorted']:
                qset = qset.order_by(sort['this'])
        return qset

    def get_sorting(self):
        order = self.request.GET.get('order', '') or '-ended'
        for name in ['Count', 'Name', 'Started', 'Ended', 'Fixed']:
            code = name.lower()
            acc = order[0] == '-'
            yield {
                'name': name,
                'code': code,
                'sorted': order.lstrip('-') == code,
                'accending': acc,
                'this': order,
                'next': [code, '-'+code][not acc],
            }

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data['headers'] = self.get_sorting()
        return data
