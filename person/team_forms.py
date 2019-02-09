#
# Copyright 2013-2019, Martin Owens <doctormo@gmail.com>
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
Membership and team admin editing forms.
"""

from typing import List
from django.forms import ModelForm
from django.utils.translation import ugettext_lazy as _

from djangocms_text_ckeditor.widgets import TextEditorWidget

from .models import Team, TeamMembership

class TeamForm(ModelForm):
    """Edit a team's basic details"""
    class Meta:
        exclude = ('mailman',)
        model = Team

    def __init__(self, *args, **kw):
        super(TeamForm, self).__init__(*args, **kw)

        for field in ('desc', 'charter', 'side_bar'):
            if field in self.fields:
                self.fields[field].widget = TextEditorWidget()

class TeamAdminForm(TeamForm):
    """Administration form for showing teams in the admin interface"""
    class Meta:
        fields = ('name', 'email', 'icon', 'intro', 'desc',
                  'charter', 'side_bar', 'enrole', 'auto_expire')
        model = Team
