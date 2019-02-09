#
# Copyright 2014-2019, Martin Owens <doctormo@gmail.com>
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
These CMS plugins are designed to work with django-cms 3.5 or later.
"""

from django.utils.translation import ugettext_lazy as _
from django.contrib.admin import *
from django.conf import settings

from cms.plugin_base import CMSPluginBase
from cms.plugin_pool import plugin_pool

from .models import InlinePage, InlinePages, ShieldPlugin, GroupPhotoPlugin, TeamPlugin
from .admin import TabInline

class InlinePagesPlugin(CMSPluginBase):
    model = InlinePages
    name = "Inline Pages (tabs)"
    render_template = "cms/plugins/inline_pages.html"
    allow_children = True
    child_classes = ["InlinePagePlugin"]

    def render(self, context, instance, placeholder):
        context.update({ 'instance': instance })
        return context


class InlinePagePlugin(CMSPluginBase):
    model = InlinePage
    name = "Single Inline Page"
    render_template = "cms/plugins/inline_page.html"
    parent_classes = ["InlinePagesPlugin"]
    allow_children = True

    def render(self, context, instance, placeholder):
        context.update({ 'instance': instance })
        return context

plugin_pool.register_plugin(InlinePagesPlugin)
plugin_pool.register_plugin(InlinePagePlugin)

class CMSShieldPlugin(CMSPluginBase):
    inlines = [TabInline]
    model   = ShieldPlugin
    name    = _('Front Shield')
    cache   = settings.ENABLE_CACHING

    render_template = "cms/plugins/shield.html"

    def render(self, context, instance, placeholder):
        context.update({
            'placeholder': placeholder,
            'tabs'       : instance.tabs.all().select_related('user', 'license', 'shield', 'tab_cat'),
            'instance'   : instance
        })
        return context

plugin_pool.register_plugin(CMSShieldPlugin)

class CMSGroupBioPlugin(CMSPluginBase):
    model = GroupPhotoPlugin
    name = _('Group of Users List')
    render_template = "cms/plugins/group.html"
    text_enabled = True

    def render(self, context, instance, placeholder):
        self.instance = instance
        if instance and instance.style:
            self.render_template = 'cms/plugins/group-%s.html' % instance.style

        context.update({
            'users'      : instance.source.user_set.all(),
            'group'      : instance.source,
            'instance'   : instance,
            'placeholder': placeholder,
            'random_user': self.random_user(instance.source.user_set.all()),
        })
        return context

    def random_user(self, users):
        from random import randint
        yield users[randint(0, users.count() - 1)]

plugin_pool.register_plugin(CMSGroupBioPlugin)

class CMSTeamPlugin(CMSPluginBase):
    """
    Render the team plugin into the page using the options.
    """
    name = _('Team Members Plugin')
    model = TeamPlugin
    render_template_template = "cms/plugins/team_{}.html"
    text_enabled = True

    @property
    def render_template(self):
        """Use the template specificed by the plugin instance"""
        return self.render_template_template.format(self.instance.template)

    def render(self, context, instance, placeholder):
        self.instance = instance
        members = instance.team.memberships.filter(
            joined__isnull=False,
            expired__isnull=True)
        if instance.role is not None:
            members = members.filter(role=instance.role)

        context.update({
            'instance': instance,
            'team': instance.team,
            'members': members,
            'placeholder': placeholder,
        })
        return context

plugin_pool.register_plugin(CMSTeamPlugin)
