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
Provides some base functionality for all search indexes
"""

import re

from django.core.exceptions import FieldDoesNotExist

from django.db import models
from django.db.models.fields.related_descriptors import (
    ReverseManyToOneDescriptor as RMR_OD,
    ManyToManyDescriptor as MR_OD,
)

from haystack.query import SearchQuerySet, AutoQuery
from haystack.indexes import (
    MultiValueField, IntegerField, FloatField, DecimalField, CharField,
    get_facet_field_name
)

EXACT_MATCH_RE = re.compile(r'(?P<phrase>[-+]?".*?")')

def get_haystack_query(query, hs_models=None, using=None):
    """
    Wrap the haystack query to provide logical OR between tokens in
    a query string.
    """
    queryset = SearchQuerySet()
    if using:
        queryset = queryset.using(using)
    if hs_models:
        queryset = queryset.models(*hs_models)

    exacts = EXACT_MATCH_RE.findall(query)
    tokens = []
    for term in EXACT_MATCH_RE.split(query):
        if term in exacts:
            tokens.append(term) # add quotes back
        else:
            tokens += term.split()
    for token in tokens:
        if token[0] in '-+':
            queryset &= queryset.filter(content=AutoQuery(token.lstrip('+')))
        else:
            queryset |= queryset.filter(content=AutoQuery(token))
    return queryset

def many_to_many(field):
    """Return a list of values from many to many field"""
    def _inner(self, obj): # pylint: disable=unused-argument
        return [g.value for g in getattr(obj, field).all()]
    return _inner

def add_field(cls, field_name, model_attr=None, model=None):
    """Add a field post meta-class, not with setattr, but fields"""
    model_attr = model_attr or field_name
    target = cls.fields

    if field_name in target:
        return

    try:
        field = model._meta.get_field(model_attr) # pylint: disable=protected-access
    except FieldDoesNotExist:
        field = model and getattr(model, model_attr, None)

    if field and isinstance(field, (MR_OD, RMR_OD)):
        setattr(cls, 'prepare_%s' % field_name, many_to_many(model_attr))
        field = MultiValueField()
    elif isinstance(field, models.IntegerField):
        field = IntegerField(model_attr=model_attr, null=field.null)
    elif isinstance(field, models.FloatField):
        field = FloatField(model_attr=model_attr, null=field.null)
    elif isinstance(field, models.DecimalField):
        field = DecimalField(model_attr=model_attr, null=field.null)
    else:
        field = CharField(model_attr=model_attr, null=getattr(field, 'null', True))

    field.set_instance_name(field_name)
    target[field_name] = field

    # Copied from haystack/indexes.py
    # Only check non-faceted fields for the following info.
    if not hasattr(field, 'facet_for') and field.faceted is True:
        shadow_facet_name = get_facet_field_name(field_name)
        shadow_facet_field = field.facet_class(facet_for=field_name)
        shadow_facet_field.set_instance_name(shadow_facet_name)
        target[shadow_facet_name] = shadow_facet_field

def add_fields(cls, viewcls):
    """Gather the fields from the viewcls (attributes to be searched on)"""
    model = viewcls.model
    for (cid, link, field) in viewcls._opts(): # pylint: disable=protected-access
        if isinstance(field, str):
            add_field(cls, cid, model_attr=field+'__'+link, model=model)
    for cat in viewcls.cats:
        add_field(cls, cat[0], model_attr=cat[0], model=model)
    for (cid, _) in viewcls.orders:
        if cid[0] == '-':
            cid = cid[1:]
        add_field(cls, cid, model=model)


class SearchIter(object): #pylint: disable=too-few-public-methods
    """This provides the output queryset a way to
       pretend to be a normal QuerySet"""
    def __init__(self, qset):
        self.qset = qset

    def __getitem__(self, name):
        if isinstance(name, slice):
            return SearchIter(self.qset.__getitem__(name))
        return self.qset[name].object

    def __len__(self):
        return len(self.qset)

    def __getattr__(self, name):
        return getattr(self.qset, name)

    def __iter__(self):
        for item in self.qset:
            yield item.object
