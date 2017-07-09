#
# Copyright 2017, Martin Owens <doctormo@gmail.com>
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
Checkbox dropdown selection box.
"""

from django.forms.widgets import SelectMultiple
from django.forms.fields import MultipleChoiceField

class CheckdropSelectMultiple(SelectMultiple):

    class Media:
        css = {
            'all': ('css/sumoselect.css',)
        }
        js = ('js/sumoselect.min.js',)

    def render(self, name, *args, **kw):
        ret = super(CheckdropSelectMultiple, self).render(name, *args, **kw)
        ret += """
        <script type="text/javascript">$('#id_%s').SumoSelect();</script>
        """ % name
        return ret


class MultipleCheckboxField(MultipleChoiceField):
    widget = CheckdropSelectMultiple

    def clean(self, value):
        lst = super(MultipleCheckboxField, self).clean(value)
        return "|%s|" % '|'.join(lst)

    def prepare_value(self, value):
        if isinstance(value, (list, tuple)):
            return value
        return unicode(value).strip('|').split('|')

