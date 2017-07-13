#
# Copyright 2016-2017, Martin Owens <doctormo@gmail.com>
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
Provide middleware items for django-cms
"""

from django.utils.translation import ugettext_lazy as _, get_language
from django.contrib.auth import get_user_model

from cms.signals import post_publish
from cms.models import CMSPlugin

from .utils import generate_content

class LogContentMiddleware(object):
    """When CMS is edited"""
    def process_request(self, request):
        """Just before a plugin is saved"""
        if request.method == 'POST' and '/admin/cms/' in request.path_info:
            ps = request.path_info.split('/')
            ps = ps[ps.index('cms')+1:-1]
            if ps[0] == 'page' and ps[1] == 'edit-plugin':
                self.previous = self.record_plugin(int(ps[-1]))

    def process_response(self, request, response):
        """When the saving of plugin content is complete"""
        if hasattr(self, 'previous'):
            comment = request.POST.get('comment', None)
            self.record_plugin(self.previous, comment, request.user)
        return response
 
    # Note: Do not make 'Inital' comment translatable.
    def record_plugin(self, plugin_id, comment='Initial', user=None):
        """Record an editing event"""
        from .models import EditHistory
        plugin = CMSPlugin.objects.get(pk=plugin_id)
        if not plugin.placeholder_id:
            # If it's not a part of a page
            return

        content = generate_content(plugin)
        if content is None:
            # There wasn't any content for this plugin
            return

        if isinstance(plugin_id, int):
            # We're looking at an initalisation request.
            history = EditHistory.objects.filter(plugin_id=plugin_id)
            if history.count() > 0:
                return history.latest()
            User = get_user_model()
            try:
                username = plugin.placeholder.page.changed_by
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                pass
        elif content == plugin_id.content:
            # Nothing changed, even though the user saved.
            return
        else:
            # Turn back into a proper plugin_id 
            plugin_id = plugin_id.plugin_id

        # We save the content BEFORE it was changed by the new content.
        return EditHistory.objects.create(
            user_id=user.pk,
            plugin_id=plugin_id,
            comment=comment,
            page=plugin.placeholder.page,
            language=get_language(),
            content=content,
        )


@receiver(post_publish, sender=Page)
def record_history(sender, instance, **kwargs):
    """When a page is published, make a new PublishHistory object"""
    history = EditHistory.filter(page_id=instance.id, published_in__isnull=True) 
    if history.count() == 0:
        # No changes happened, skip!
        return

    User = get_user_model()
    try:
        user = User.objects.get(username=instance.changed_by)
    except User.DoesNotExist:
        return

    return PublishHistory.objects.create(
        page=instance,
        user=user,
        language=,
        editings=history)

