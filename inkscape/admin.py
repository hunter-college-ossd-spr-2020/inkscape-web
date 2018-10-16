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
from django.contrib.contenttypes.models import ContentType

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
