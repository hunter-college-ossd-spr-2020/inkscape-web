"""
Allow tags to be created on the fly
"""

import json

from collections import defaultdict

from django.forms import ValidationError
from django.utils.encoding import force_text
from django.utils.safestring import mark_safe

from django.forms.models import ModelMultipleChoiceField
from django.forms.widgets import Select, SelectMultiple


from .validators import Range

class FilterSelect(Select):
    """
    A select dropdown with extra data-filter attributes which
    are picked up by javascript to provide client-side filtering.

    Options which are not applicable are disabled by default.
    """
    def __init__(self, qs, m2m_field, filter_by, replace):
        self.filter_by = filter_by
        self.filters = defaultdict(list)
        for (pk, m2m_pk) in list(qs.values_list('pk', m2m_field)):
            if m2m_pk is not None:
                self.filters[pk].append(int(m2m_pk))

        super(FilterSelect, self).__init__(replace.attrs, replace.choices)

    def get_context(self, *args, **kwargs):
        context = super().get_context(*args, **kwargs)
        if not context['widget']['value']:
            context['widget']['attrs']['novalue'] = 'true'
        context['widget']['attrs']['data-filter_by'] = self.filter_by
        return context

    def create_option(self, name, value, label, selected, *args, **kwargs):
        """Reimplement and generate option tags for this select"""
        context = super().create_option(name, value, label, selected, *args, **kwargs)
        attrs = context['attrs']
        if value and int(value) in self.filters:
            attrs['data-filter'] = str(self.filters[int(value)])
        return context


class DisabledSelect(Select):
    """If there is only one choice, disable and set to this choice"""
    option_template_name = 'widgets/select_disabled_option.html'

    def get_context(self, *args, **kwargs):
        context = super().get_context(*args, **kwargs)
        context['widget']['attrs']['disabled'] = 'disabled'
        self.name = context['widget']['name']
        return context

class CategorySelect(Select):
    """Provide extra data for validating a resource within the option"""
    def get_context(self, *args, **kwargs):
        context = super().get_context(*args, **kwargs)
        if context['widget']['value']:
            context['widget']['attrs']['novalue'] = 'true'
        return context

    def create_option(self, name, value, label, selected, *args, **kwargs):
        """Reimplement and generate option tags for this select"""
        context = super().create_option(name, value, label, selected, *args, **kwargs)
        if value and not isinstance(value, (int, str)):
            attrs = context['attrs']
            # CSV list of types, treat as string
            if value.acceptable_types:
                attrs['data-types'] = value.acceptable_types

            for field in ('media_x', 'media_y', 'size'):
                f_value = getattr(value, 'acceptable_' + field)
                if f_value not in (None, ''):
                    scale = 1024 if field == 'size' else 1
                    for method in (min, max):
                        # Add both min and max for every range field
                        name = '-'.join(['data', field, method.__name__])
                        attrs[name] = method(Range(f_value)) / scale

            # Add tag options, if needed
            names = []
            for x, tagcat in enumerate(value.tags.all()):
                names.append(tagcat.name)
                key = 'data-tagcat-{}'.format(x)
                attrs[key] = json.dumps(list(tagcat.tags.values_list('name', flat=True)))

            attrs['data-tagcat'] = json.dumps(names)
            context['value'] = force_text(value.pk)
        return context

class SelectTags(SelectMultiple):
    template_name = 'widgets/select_tags.html'
    option_template_name = 'widgets/select_tags_option.html'

    class Media:
        css = {
            'all': ('css/bootstrap-tagsinput.css', 'css/bootstrap-tagsinput-typeahead.css',)
        }
        js = ('js/bootstrap-tagsinput.js', 'js/typeahead.js')

class TagsChoiceField(ModelMultipleChoiceField):
    widget = SelectTags

    def _check_values(self, value):
        tags = list(self.get_or_create(value))
        return super(TagsChoiceField, self)._check_values(tags)

    def get_or_create(self, values):
        from .models import Tag
        for tag in frozenset(values):
            if isinstance(tag, int):
                yield tag
                continue
            try:
                yield Tag.objects.get_or_create(name=tag.lower())[0].pk
            except Exception as error:
                if "value too long" in str(error):
                    raise ValidationError("Tag is too long!")
                raise

