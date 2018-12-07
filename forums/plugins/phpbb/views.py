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
The phpBB importer allows the moderators to select threads on other
forums on the internet and download their contents into this forum.

New forum sites can be added to the settings.py as in this example:

    FORUMS_PHPBB_SITES = {
        'mysite': ('https://onlineforum.com/index.php?site=forum', 'My Website Forum'),
    }
"""

from django.views.generic import TemplateView
from django.utils.functional import cached_property
from django.utils.translation import ugettext_lazy as _
from django.core.urlresolvers import reverse
from django.conf import settings

from ...mixins import ModeratorRequired

from .parser import BeeBeeSite

#WEBSITES = getattr(settings, 'FORUMS_PHPBB_SITES', {})
WEBSITES = {
    'brynns': ('https://forum.inkscapecommunity.com/index.php?action=forum', 'Inkscape Community Forum'),
    'courneys': ('http://www.inkscapeforum.com/', 'Inkscape Forum'),
}

class SelectionView(ModeratorRequired, TemplateView):
    """Select One of the given options"""
    template_name = "forums/select_modal.html"
    options = []

    @property
    def item_url(self):
        """URL of the sub-item"""
        raise NotImplementedError("Please provide the name of the item_url to lookup.")

    def get_options(self):
        """Provide a list of options to choose from"""
        return self.options

    def proccess_list(self):
        """Process the options list"""
        for label, url in self.get_options():
            if isinstance(url, (tuple, list)):
                url = reverse(self.item_url, args=url)
            elif isinstance(url, dict):
                url = reverse(self.item_url, kwargs=url)
            yield {
                'label': label,
                'url': url, # URL of option
            }

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data['list'] = self.proccess_list()
        data['title'] = self.title
        return data

class SelectSite(SelectionView):
    """A - Select Website to scrape"""
    title = _("Select Forum Website Source")
    item_url = 'forums:phpbb:select_forum'
    options = [(label, (slug,)) for (slug, (url, label)) in WEBSITES.items()]


class SelectForum(SelectionView):
    """B - Select Forum from website"""
    item_url = 'forums:phpbb_select_thread'

    @property
    def title(self):
        """Return the title to display at the top of the page"""
        return "Import from: {}".format(self.get_site_datum()[1])

    def get_site_datum(self):
        """Return the selected forum, important first step"""
        return WEBSITES.get(self.kwargs.get('site', None), None)

    @cached_property
    def site(self):
        """Return the phpBB site object"""
        return BeeBeeSite(self.get_site_datum()[0])

    def get_options(self):
        for forum in self.site:
            kwargs = self.kwargs.copy()
            kwargs['forum'] = forum.resource_id
            yield (forum.data['name'], kwargs)

class SelectThread(SelectForum):
    """Select from a list of threads"""
    item_url = 'phpbb:import_thread'

    @property
    def title(self):
        return "Import from: {}".format(self.get_site_datum()[1])

    @cached_property
    def forum(self):
        """Return the phpBB forum object"""
        for forum in self.site:
            if forum.resource_id == self.kwargs['forum']:
                return forum
        return []

    def get_options(self):
        for thread in self.forum:
            kwargs = self.kwargs.copy()
            kwargs['thread'] = thread.resource_id
            yield (thread.data['name'], kwargs)

class ImportThread(SelectThread):
    """Import Thread, select comments and choose to import attachments / inlines"""
    form = None
