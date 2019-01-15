#
# Copyright 2014, Martin Owens <doctormo@gmail.com>
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
"""Extra template tags for use only in the inkscape website"""

from datetime import datetime

# Not the typical translator
from django.utils.translation import ungettext_lazy as _un, ugettext_lazy as _
from django.utils.timezone import is_aware, utc
from django.template import Library
from django.forms import widgets

from cms.models.pagemodel import Page

register = Library() # pylint: disable=invalid-name

CHUNKS_AGO = (
    # Note to translator: Short varients are for display. Keep short but use your better judgement.
    (60 * 60 * 24 * 365, _un('%d year ago', '%d years ago'), _('%dyr')),
    (60 * 60 * 24 * 30, _un('%d month ago', '%d months ago'), _('%dmon')),
    (60 * 60 * 24 * 7, _un('%d week ago', '%d weeks ago'), _('%dwk')),
    (60 * 60 * 24, _un('%d day ago', '%d days ago'), _('%dd')),
    (60 * 60, _un('%d hour ago', '%d hours ago'), _('%dhr')),
    (60, _un('%d minute ago', '%d minutes ago'), _('%dmin'))
)

@register.filter("ago")
def time_ago(dtime, mode=0):
    """Turn a date time into a string saying how long ago the time was"""
    if not dtime:
        return _('Never')
    # Convert datetime.date to datetime for comparison.
    if not isinstance(dtime, datetime):
        dtime = datetime(dtime.year, dtime.month, dtime.day)

    now = datetime.now(utc if is_aware(dtime) else None)

    delta = (now - dtime)
    # ignore microseconds
    since = delta.days * 24 * 60 * 60 + delta.seconds
    if since <= 0:
        # dtime is in the future compared to now, stop processing.
        return _('Now') if int(mode) == 1 else _('0 minutes')
    for i, (seconds, name, small) in enumerate(CHUNKS_AGO):
        count = since // seconds
        # If there's a positive number in this unit, OR we have the last unit.
        if count != 0 or i == len(CHUNKS_AGO) - 1:
            result = (int(mode) == 1 and small or name) % count
            if i + 1 < len(CHUNKS_AGO) and int(mode) == 0:
                # Now get the second item unit if in mode 0
                seconds2, name2 = CHUNKS_AGO[i + 1][:2]
                count2 = (since - (seconds * count)) // seconds2
                if count2 != 0:
                    result += ', ' + (name2 % count2)
            return result
    return str(dtime)

@register.filter("percent")
def percent(x, y):
    """Format the two numbers as a percent"""
    if int(y) == 0:
        return "0%"
    return '{:.0%}'.format(float(x) / float(y))

@register.filter("placeholder")
def add_placeholder(bound_field, text=None):
    """Add a placeholder attribute to any form field object"""
    if text is None:
        raise ValueError("Placeholder requires text content for widget.")
    if type(bound_field.field).__name__ == 'ReCaptchaField':
        return bound_field
    bound_field.field.widget.attrs.update({"placeholder": text})
    return bound_field

@register.simple_tag()
def app_info(request, obj, lst, form):
    """Generate detail about the app generating the response"""
    if hasattr(request, 'resolver_match') and request.resolver_match is not None:
        cls = request.resolver_match.func.__module__.split('.')[0]
        if hasattr(request.resolver_match.func, '__name__'):
            view = request.resolver_match.func.__name__
        else:
            view = type(request.resolver_match.func).__name__
        if form is not None:
            form = type(form).__name__
            model = getattr(getattr(form, '_meta', None), 'model', None)
            if model is not None:
                model = model.__name__
                return "{}.{} (form: {} for {})".format(cls, view, model, form)
            return "{}.{} (form: {})".format(cls, view, form)
        if obj is not None:
            model = type(obj).__name__
            return "{}.{} ({} item {})".format(cls, view, model, obj)
        if lst is not None:
            model = getattr(lst, 'model', type(None)).__name__
            return "{}.{} ({} list)".format(cls, view, model)
        return "{}.{}".format(cls, view)
    return 'Unknown App'

@register.filter("autofocus")
def add_autofocus(bound_field):
    """Add an autofocus attribute to any form field object"""
    bound_field.field.widget.attrs.update({"autofocus": "autofocus"})
    return bound_field

@register.filter("tabindex")
def add_tabindex(bound_field, number):
    """Add table attribute to any form field object"""
    bound_field.field.widget.attrs.update({"tabindex": number})
    return bound_field

@register.filter("formfield")
def add_form_control(bound_field):
    """Add a form-control attribute to any form field"""
    if isinstance(bound_field.field.widget, widgets.CheckboxSelectMultiple):
        return bound_field

    cls = ['form-control']
    if bound_field.errors:
        cls.append("form-control-danger")
    bound_field.field.widget.attrs.update({"class": ' '.join(cls)})
    return bound_field

@register.filter("is_checkbox")
def is_checkbox_field(bound_field):
    """Returns true if the form field object is a checkbox"""
    return type(bound_field.field.widget).__name__ == 'CheckboxInput'

@register.filter("root_nudge")
def root_nudge(root, page):
    """
    django cms has a serious flaw with how it manages the 'root' of menus.
    This is because cms attempts to manage the root sent to menu via
    checking in_navigation options. this conflicts with the menus.NavigationNode
    system which controls the system via the templates.

    This tag stops django-cms interfering by correcting menus input when needed.
    """
    is_draft = page.publisher_is_draft if page else False
    for child_page in Page.objects.filter(is_home=True, publisher_is_draft=is_draft):
        return root + int(child_page.in_navigation)
