#
# Copyright 2016, Martin Owens <doctormo@gmail.com>
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
"""Register the content-type model in the admin interface"""

from django.utils.safestring import mark_safe

from django.contrib.admin import ModelAdmin, site
from django.contrib.admin.models import LogEntry, DELETION
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse
from django.utils.html import escape

BOLD = "<strong style='display: block; width: 98%%; padding: 6px; color: "\
    "white; background-color: %s;'>%s</strong>"

class ContentTypeAdmin(ModelAdmin):
    """Administration for the content type"""
    list_display = ('__str__', 'app_label', 'model', 'is_defunct')
    list_filter = ('app_label',)
    search_fields = ('model',)

    @staticmethod
    def is_defunct(obj):
        """Return HTML if the content type nolonger exists"""
        if not obj.model_class():
            return mark_safe(BOLD % ('red', 'DEFUNCT'))
        return "OK"

site.register(ContentType, ContentTypeAdmin)

class LogEntryAdmin(ModelAdmin):

    date_hierarchy = 'action_time'

    #readonly_fields = LogEntry._meta.get_all_field_names()

    def get_readonly_fields(self, request, obj=None):
        if request.user.is_superuser and False:
            return self.readonly_fields

        return list(set(
            [field.name for field in self.opts.local_fields] +
            [field.name for field in self.opts.local_many_to_many]
        ))

    list_filter = [
        'content_type',
        'action_flag'
    ]

    search_fields = [
        'object_repr',
        'change_message'
    ]


    list_display = [
        'action_time',
        'user',
        'content_type',
        'object_link',
        'action_flag_',
        'change_message',
    ]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser and request.method != 'POST'

    def has_delete_permission(self, request, obj=None):
        return False

    def action_flag_(self, obj):
        flags = {
            1: "Addition",
            2: "Changed",
            3: "Deleted",
        }
        return flags[obj.action_flag]

    def object_link(self, obj):
        if obj.action_flag == DELETION:
            link = escape(obj.object_repr)
        else:
            ct = obj.content_type
            link = u'<a href="%s">%s</a>' % (
                reverse('admin:%s_%s_change' % (ct.app_label, ct.model), args=[obj.object_id]),
                escape(obj.object_repr),
            )
        return link
    object_link.allow_tags = True
    object_link.admin_order_field = 'object_repr'
    object_link.short_description = u'object'


site.register(LogEntry, LogEntryAdmin)
