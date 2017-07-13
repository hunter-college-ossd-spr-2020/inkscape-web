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
"""
"""

from django.utils.safestring import mark_safe
from django.utils.encoding import force_text
from django.utils.html import strip_tags, strip_spaces_between_tags, linebreaks
import json

try:
    from diff_match_patch import diff_match_patch
except ImportError:
    generate_diffs = None
else:
    differ = diff_match_patch()

#
# Adding fields here will force the field to be included in any diff
# regardless of if it has been set in the plugin's serch fields.
#
PLUGIN_FIELDS = { 
    'Link': ('url',),
}

def clean_text(text):
    return strip_tags(force_text(text)).replace("\n\n\n", "\n\n").strip()

def generate_content(plugin):
    """Generates the raw content for this plugin"""
    # Resolve the actual plugin object
    (plugin, _) = plugin.get_plugin_instance()

    # Get a list of fields to track content for (keep order)
    #field_names = PLUGIN_FIELDS.get(type(plugin).__name__, tuple()) \
    #                + getattr(plugin, 'search_fields', tuple())
    #for field in field_names:

    fields = {}
    bodies = {}

    for field in model._meta.get_fields():
        name = field.name
        value = getattr(plugin, name)
        if value is not None:
            value = clean_text(value)
            if '\n' in value:
                bodies[name] = value
            else:
                fields[name] = value

    if not fields and not bodies:
        return None

    return json.dumps({
        'fields': fields,
        'bodies': bodies,
    })


def stub_text():
    """Returns a html of the stub text""" 
    return mark_safe(stub.replace('<span>', '\n\n').replace('</span>', '')\
                  .replace('<del style="background:#ffe6e6;">', '<--').replace('</del>', '-->')\
                  .replace('<ins style="background:#e6ffe6;">', '<++').replace('</ins>', '++>'))

def stub(diffs):
    diffs = list(self.__iter__(diffs=True))
    diffs = [o for d in diffs for o in d]
    return differ.diff_prettyHtml(get_segment(diffs)).replace('&para;','')


def get_segment(diffs):
    """Returns the first section of the diff as a stub"""
    size = 1024
    cleaned = stem_diff(diffs)
    tot = 0
    for (op, text) in cleaned:
        tot += len(text)
        if tot > size:
            break
        yield (op, text)

def stem_diff(diffs):
    left_size = 10
    right_size = 10
    # First step is to stem non-changed parts with elipsis
    for x, (op, text) in enumerate(diffs):
        if op == 0:
            lines = text.splitlines()
            if len(lines) == 0:
                continue

            if len(lines) == 1 and len(text) <= left_size + right_size \
              and x > 0 and x < len(diffs):
                yield (op, text)
                continue

            if x > 0:
                if len(lines[0]) > left_size:
                    yield (op, lines[0][:left_size] + "...")
                else:
                    yield (op, lines[0])

            if x < len(diffs):
                if len(lines[-1]) > right_size:
                    yield (op, "..." + lines[-1][-right_size:])
                else:
                    yield (op, lines[-1])
        else:
            yield (op, text)


