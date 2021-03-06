#
# Copyright (C) 2014, Martin Owens <doctormo@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
"""
Template tags for the whole project
"""
import re
import html.entities

from datetime import timedelta, datetime

from django import template
from django.templatetags.static import StaticNode
from django.utils.safestring import mark_safe
from django.template.defaultfilters import date, timesince, stringfilter, _urlize
from django.templatetags.tz import localtime
from django.utils import timezone
from django.db.models import Model
from django.urls import resolve

register = template.Library() # pylint: disable=invalid-name

HTENT = re.compile('&([^;]+);')
NAMES = html.entities.name2codepoint

def _dt(arg):
    if not arg:
        return datetime.now(timezone.utc)
    elif isinstance(arg, str):
        try:
            (dat, time) = arg.split(' ')
            dat = [int(i) for i in dat.split('-')[:3] + time.split(':')[:3]]
            return datetime(*(dat + [0, timezone.utc]))
        except Exception:
            raise ValueError("Should be a datetime object, got string: %s" % arg)
    elif not isinstance(arg, datetime) or not arg.tzinfo:
        return datetime(arg.year, arg.month, arg.day,
                        arg.hour, arg.minute, arg.second,
                        arg.microsecond, timezone.utc)
    return arg

@register.filter("querydict_pop")
def kwarg_remove(qdict, item):
    """Removes a QueryDict item"""
    qdict = qdict.copy()
    qdict.pop(item, None)
    return qdict

@register.simple_tag(takes_context=True)
def url_name(context, equal=None, ok="active", nok=""):
    """Return the url_name for this page"""
    name = resolve(context['request'].path_info).url_name
    if equal:
        return ok if name == equal else nok
    return name

@register.filter("placeholder")
def add_placeholder(form, text=None):
    """Add a placeholder attribute to input widgets"""
    if text is None:
        raise ValueError("Placeholder requires text content for widget.")
    form.field.widget.attrs.update({"placeholder": text})
    return form

@register.filter("add")
def add_filter(value, arg=1):
    """Add a number to another, default is incriment by 1"""
    return int(value) + arg

@register.simple_tag(takes_context=True)
def track_object(context, obj):
    """This object, when changed, should invalidate this request"""
    if not isinstance(obj, Model):
        raise ValueError("track_object requires a model object, "
                         "%s object provided instead." % type(obj).__name__)

    request = context['request']
    if not hasattr(request, 'tracked_objects'):
        request.tracked_objects = []

    request.tracked_objects.append(obj)
    return mark_safe("<!--Cache Tracked-->")

class UrlStaticNode(StaticNode):
    """Returns either the url of a file field, or a static url default"""
    def __init__(self, field=None, **kw):
        self.field = field
        super(UrlStaticNode, self).__init__(**kw)

    def url(self, context):
        field = self.field.resolve(context)
        if field:
            return field.url
        return super(UrlStaticNode, self).url(context)

    @classmethod
    def handle_token(cls, parser, token):
        bits = token.split_contents()

        if len(bits) < 3:
            raise template.TemplateSyntaxError(
                "'%s' takes at least two arguments (file field and path to file)" % bits[0])

        field = parser.compile_filter(bits[1])
        path = parser.compile_filter(bits[2])

        if len(bits) >= 3 and bits[-2] == 'as':
            varname = bits[-1]
        else:
            varname = None

        return cls(field=field, varname=varname, path=path)

@register.tag("url_or_static")
def static_url(parser, token):
    """Return the url of a file field, or it's default static url"""
    return UrlStaticNode.handle_token(parser, token)

@register.filter("timetag", is_safe=True)
def timetag_filter(value, arg=None):
    """Formats a date as a time since if less than 1 day old or as a date otherwise
    Will return <time...> html tag as part of the output.
    """
    if not value:
        return ''
    value = _dt(value)
    arg = _dt(arg)

    if arg - value > timedelta(days=1):
        label = date(value, 'Y-m-d')
    else:
        label = timesince(value, arg) + " ago"

    return mark_safe("<time datetime=\"%s\" title=\"%s\">%s</time>" % (
        date(value, 'Y-m-d\\TH:i:sO'), date(localtime(value), 'Y-m-d H:i:sO'), label))

@register.filter("int2timedelta", is_safe=True)
def timedelta_filter(value):
    """Format seconds count as a timedelta"""
    return timedelta(seconds=int(value))

@register.filter("is_recent", is_safe=True)
def time_isrecent(value, arg=None):
    if not value:
        return ''
    value = _dt(value)
    arg = _dt(arg)
    return arg - value < timedelta(days=1)

@register.filter("timenotag", is_safe=True)
def timenotag(value, arg=None):
    if not value:
        return ''
    value = _dt(value)
    arg = _dt(arg)
    if arg - value > timedelta(days=1):
        return date(value, 'Y-m-d')
    return timesince(value, arg) + " ago"

@register.filter("decodetext", is_safe=True)
def decodetext(value):
    """Removes HTML entities from text"""
    return HTENT.sub(lambda m: chr(int(NAMES.get(m.group(1), m.group(1).strip('#')))), value)
  
@register.filter("urlized", is_safe=True, needs_autoescape=True)
@stringfilter
def urlized_filter(value, autoescape=True):
    """Turns plain text urls in a text into clickable html tags, with rel="nofollow noopener" target="_blank"
    for safety, and to not lose users to third-party sites. Use instead of django's urlize filter.
    """
    return mark_safe(_urlize(value, nofollow=True, autoescape=autoescape).replace('rel="nofollow"', 'rel="nofollow noopener" target="_blank"'))
