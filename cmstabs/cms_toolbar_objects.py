#
# Copyright 2016-2017, Martin Owens <doctormo@gmail.com>
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
Provide django cms with object editing toolbar.
"""

from django.db.models import QuerySet, Model

from django.core.urlresolvers import NoReverseMatch, reverse
from django.utils.translation import ugettext_lazy as _, get_language
from django.contrib.contenttypes.models import ContentType

from cms.toolbar.toolbar import CMSToolbar
from cms.toolbar_base import CMSToolbar as SubToolbar
from cms.toolbar.items import Menu
from cms.constants import LEFT

OLD_RWS = CMSToolbar.render_with_structure
def new_rws(self, context, nodelist):
    """Monkey patch the CMSToolbar to provide context"""
    self.response_context = context
    return OLD_RWS(self, context, nodelist)
CMSToolbar.render_with_structure = new_rws


class ObjectsToolbar(SubToolbar):
    """Adds an Objects menu item for quick admin access to current context"""
    def populate(self):
        if self.request.user.is_authenticated() and self.request.user.is_staff:
            self.add_menu(self.toolbar.response_context)

    def add_menu(self, context):
        """Do the population now we have permission"""
        for name in context.get('object-bar', ['object', 'object_list']):
            target = context.get(name, None)
            menu = Menu("%(otype)s", self.toolbar.csrf_token, side=LEFT)

            type_name = None
            if isinstance(target, Model):
                type_name = self.add_object_menu(menu, target)
            elif target:
                type_name = self.add_list_menu(menu, target)

            if type_name:
                key = 'object-menu-%s' % type_name
                if key not in self.toolbar.menus:
                    self.toolbar.menus[key] = menu
                    self.toolbar.add_item(menu, position=None)

    def admin_link(self, model, method='change', obj=None):
        ct = ContentType.objects.get_for_model(model)
        bits = (ct.app_label, ct.model, method)
        args = (obj.pk,) if obj is not None else ()
        perm = '%s.%s_%s' % (ct.app_label, method, ct.model)
        if self.request.user.has_perm(perm):
            return reverse('admin:%s_%s_%s' % bits, args=args)
        raise NoReverseMatch("No permission")

    def menu_item(self, menu, label, action, then, obj=None, model=None):
        if obj is not None and model is None:
            model = type(obj)

        if action != 'add' and not obj.pk:
            return None

        bits = {'otype': model.__name__}
        menu.name = menu.name % bits
        try:
            url = self.admin_link(model, action, obj=obj)
        except NoReverseMatch as err:
            return None

        return menu.add_modal_item(label % bits, url=url, on_close=then)

    def add_object_menu(self, menu, obj):
        if type(obj).__name__ == 'SimpleLazyObject':
            obj = obj._wrapped

        if obj is None:
            return

        br = None
        model = type(obj)

        then = getattr(model, 'get_list_url', lambda: False)
        if self.menu_item(menu, _('New %(otype)s'), 'add', then, model=model):
            br = menu.add_break()

        if get_language() not in ('en', None):
            then = getattr(obj, 'get_absolute_url', lambda: 'REFRESH_PAGE')()
            if self.menu_item(menu, _('Translate %(otype)s'), 'translate', then, obj):
                br = menu.add_break()

        then = getattr(obj, 'get_absolute_url', lambda: 'REFRESH_PAGE')()
        ed = self.menu_item(menu, _('Edit %(otype)s'), 'change', then, obj)

        then = getattr(model, 'get_list_url', lambda: '/')
        de = self.menu_item(menu, _('Delete %(otype)s'), 'delete', then, obj)

        if not (ed or de) and br:
            menu.remove_item(br)

        return model.__name__

    def add_list_menu(self, menu, lst):
        model = None

        if isinstance(lst, QuerySet):
            model = lst.model
        elif lst:
            for item in lst:
                model = type(item)
                break
        else:
            return

        if model:
            then = getattr(model, 'get_list_url', lambda: False)
            self.menu_item(menu, _('New %(otype)s'), 'add', then, model=model)
            return model.__name__
