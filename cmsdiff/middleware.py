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

from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _
from django.contrib.contenttypes.models import ContentType
from reversion.revisions import revision_context_manager as manager

from cms.toolbar.items import Menu
from cms.constants import LEFT
from cmsdiff.app import DRAFT_ID

class CommentMiddleware(object):
    """Adds a comment to the current draft revision if possible."""
    def process_request(self, request):
        self.comment = request.POST.get('revision_comment', None)
        if request.method == 'POST' and self.comment:
            manager.start()

    def process_response(self, request, response):
        if getattr(self, 'comment', None):
            manager.set_comment(DRAFT_ID + request.POST['revision_comment'])
            manager.end()
        return response

class ObjectToolbarMiddleware(object):
    """Adds an Objects menu item for quick admin access to current context"""
    def admin_link(self, obj, method='change'):
       ct = ContentType.objects.get_for_model(type(obj))
       return reverse('admin:%s_%s_%s' % (ct.app_label, ct.model, method), args=(obj.pk,)) 

    def menu_item(self, obj, menu, label, action, qs=''):
        try:
            url = self.admin_link(obj, action)
            menu.add_modal_item(label % {'otype': type(obj).__name__}, url=url+qs)
        except:
            pass

    def process_template_response(self, request, response):
        if request.user.is_authenticated() and request.user.is_superuser:
            obj = getattr(response, 'context_data', {}).get('object', None)
            if type(obj).__name__ == 'SimpleLazyObject':
                obj = obj._wrapped
            if obj:
                menu = Menu(_('Object'), request.toolbar.csrf_token, side=LEFT)
                request.toolbar.menus['object-menu'] = menu
                request.toolbar.add_item(menu, position=None)

                self.menu_item(obj, menu, _('Purge %(otype)s'), 'delete', '?next=/')
                self.menu_item(obj, menu, _('Edit %(otype)s'), 'change')
        return response

