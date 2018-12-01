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
from haystack.utils.highlighting import Highlighter
from django.utils.safestring import mark_safe
from django.utils.html import strip_tags
from django import template

register = template.Library() # pylint: disable=invalid-name

@register.filter("haystacker")
def haystacker(search_results):
    """Loops through haystack results and returns objects instead"""
    for result in search_results:
        obj = result.object
        obj.haystack = result
        yield obj

@register.simple_tag(takes_context=True)
def highlight_all(context, content):
    """
    Reformat highlighter so it doesn't create a snipped window of content with elipsis
    """
    hlight = Highlighter(context['query'])
    hlight.text_block = strip_tags(content)
    html = hlight.render_html(hlight.find_highlightable_words(), 0, len(content))
    return mark_safe(html)
