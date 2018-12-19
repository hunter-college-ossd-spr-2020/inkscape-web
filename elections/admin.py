#
# Copyright 2017-2018, Martin Owens <doctormo@gmail.com>
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
"""Administrative interface to elections"""

from django.contrib.admin import ModelAdmin, site

from .models import Election

class ElectionAdmin(ModelAdmin):
    """Election admin interface"""
    raw_id_fields = ('called_by',)
    list_display = ('slug', 'called_by', 'called_on', 'status')
    readonly_fields = ('log',)

site.register(Election, ElectionAdmin)
