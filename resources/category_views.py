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
Provides as very good filtering system with automatic category generation
for ListView. This allows multiple categories to be specified and for them
to automatically filter the list.

Supports both url based key words e.g. /(?<category>\w+)/ and
get kwargs on the request. Define the urls with the right category id
to get automatic url based atrtirubution.

Example in views.py:

class MyView(CategoryListView):
    model = my_model
    cats = ('status', _("Status")),\
           ('type', _("Type")),\
           ('foo', _("Bar"), Baz),
    opts = ('user', 'username'),

in urls.py:

url('^$', MyView.as_view(), name='myview')
url('^(?P<type>[\ w-]+)/$', MyView.as_view(), name='myview')

In this example our ListView is created as normal with a model.
It also specifies a cats class attribute which defines each category
and it's title that will appear in the template.

Status is a ForeignKey on my_model and this will generate a list of selectable
status items which when selected will filter my_model via it's status=item link
The value of status is passed in via the request.GET dictionary. Generated urls
for each selectable item will include the attribute after the quest mark

e.g. /url/?status=value

Type does the same as status, but instead of the attribute existing in the GET
dictionary, it will be passed in via the url kwargs. These are automatically
detected so there isn't any further boilerplait code.

e.g. /type1/

foo acts differently. Where status and type are ForeignKey fields and the linked
model is detected automatically. foo isn't a foreignkey field. We pass in the
categories model which will be listed and the lookup is done on it's direct value
instead of it's link id.

The code depends on a 'value' field or object property existing on each of the
category objects in order to get it's 'slug' name rather than it's display name.

opts contains similar filtering as cats, but are not displayed. They are either
selected by previous/other pages or are selected via simple links which reset
all other category selections.

This allows filtering of fields that don't appear in the category list.

The CategoryFeed allows the same categories to be turned into an rss feed.

All View classes don't need as_view() and can be created directly from urls.
"""
__all__ = ('CategoryListView')

from django.urls import reverse, get_resolver, NoReverseMatch
from django.views.generic.list import MultipleObjectMixin
from django.utils.functional import cached_property
from django.views.generic.base import TemplateView as View
from django.utils.translation import ugettext_lazy as _
from django.utils.http import urlquote
from django.shortcuts import redirect
from django.db.models import Model

from django.core.exceptions import FieldError

from .search_base import get_haystack_query, MR_OD, RMR_OD, SearchIter

def get_url(name, *args, **kwargs):
    """Quick reverse lookup"""
    return reverse(name, kwargs=kwargs, args=args)

def clean_dict(target, translate=None):
    """Removes any keys where the values is None"""
    return dict((name, (translate or {}).get(str(value), value))
                for (name, value) in target.items()
                if value is not None)

def reverse_order(target, active=True):
    """Appends '-' to column ordering arguments"""
    if not active:
        return target
    if target[0] == '-':
        return target[1:]
    return '-' + target

class AllCategory(object): # pylint: disable=too-few-public-methods
    """A simple object for 'All' Menu Item"""
    value = None
    filterable = True
    name = _("All")

    def __str__(self):
        return "All"

class Category(list):
    """A menu of items in this category, created by ListView"""
    def __init__(self, view, queryset, cid, name=None):
        super(Category, self).__init__()
        self.value = view.get_value(cid)

        self.cid = cid
        self.name = name or cid.replace('_', ' ').title()
        self.item = AllCategory()

        # Populate items, mostly these models don't have slug columns.
        self.append(self.item)
        for item in queryset:
            if self.value is not None and item.value == self.value:
                self.item = item
            self.append(item)

    def conclude(self, view):
        """Items to finish at the last minute"""
        for item in self:
            try:
                item.url = view.get_url(self.cid, item.value)
            except NoReverseMatch:
                item.url = 'None'
            item.count = view.get_count(self.cid, item)

    def active_items(self):
        """Returns a list of active items (items with >0 results)"""
        return [item for item in self if item.count]

    def count(self):
        """Returns the number of active items"""
        return len(self.active_items()) - 1

    def __str__(self):
        return str(self.name)


class CategoryListView(View, MultipleObjectMixin):
    """ListView with categorisation functionality, provides a simple way to
    Define a set of categories and have them availab ein the template with urls"""
    cats = ()
    opts = ()
    orders = ()
    order = None
    rss_view = ''
    redirect = False
    using = 'default'
    paginate_by = 20

    def __init__(self, *args, **kwargs):
        super(CategoryListView, self).__init__(*args, **kwargs)
        self.object_list = None
        self.query = None

    def base_queryset(self):
        """Returns the default query for a given manager"""
        return self.model._default_manager.all() # pylint: disable=protected-access

    def base_haystack_query(self, query):
        """When doing full-text searching, use this instead of base_queryset"""
        return get_haystack_query(query, using=self.using, hs_models=(self.model,))

    @staticmethod
    def extra_filters():
        """Return a dictionary containing any extra filters to apply"""
        return {}

    def get_queryset(self, **kwargs):
        """Returns the queryset, plus any modifications specified in kwargs"""
        self.query = self.get_value('q', None)
        def _get(cat):
            field = getattr(self.model, cat.cid, None)
            if field and (not isinstance(field, (MR_OD, RMR_OD)) or not self.query):
                return cat.item
            return cat.item.value

        if self.query:
            queryset = self.base_haystack_query(self.query)
        else:
            queryset = self.base_queryset()
        filters = {}
        for cat in self.get_cats:
            if cat is not None and cat.item != cat[0]:
                filters[cat.cid] = _get(cat)

        filters.update(self.extra_filters())
        filters.update(clean_dict(dict(self.get_opts)))
        filters.update(kwargs)
        qset = queryset.filter(**clean_dict(filters, {'True':True, 'False':False}))

        for order in self.get_orders():
            if order['active']:
                return qset.order_by(order['order'])
        return qset

    def get_url(self, cid=None, value=None, view=None, exclude=None):
        """Returns the url for this category with this value"""
        kwargs = self.kwargs.copy()
        gets = self.request.GET.copy()
        view = view or self.request.resolver_match.url_name
        if cid is not None:
            args = list(self.get_possible_args(view))
            target = kwargs if cid in args else gets
            if value is None:
                target.pop(cid, None)
            else:
                target[cid] = value
        url = get_url(view, **kwargs)
        if gets:
            # Always remove page, start from begining
            gets.pop('page', None)
            get = ('&'.join('%s=%s' % (a, urlquote(b)) for (a, b) in gets.items() if a != exclude))
            if get:
                url += '?' + get
        return url

    @staticmethod
    def get_possible_args(view_name):
        """Returns a generator with all possible kwargs for this view name"""
        for poss, _, _ in get_resolver(None).reverse_dict.getlist(view_name):
            for _, params in poss:
                for param in params:
                    # Remove non-keyword arguments
                    if not param.startswith('_'):
                        yield param

    def get_count(self, cid, item=None):
        """Gets the number of items in this category, with this value"""
        if not hasattr(self.model, cid):
            item = item.value
        if item is None or getattr(item, 'value', item) is None:
            item = None
        return self.get_queryset(**{cid: item}).count()

    def get_value(self, cid, default=None):
        """Tries to find the category value from multiple sources"""
        return self.kwargs.get(cid, self.request.GET.get(cid, default))

    @cached_property
    def get_opts(self):
        """Gets a list of options selected based on opts"""
        return [self.get_opt(*opt) for opt in self._opts()]

    @classmethod
    def _opts(cls):
        """Returns a set of filtered links for manually defined options"""
        for opt in cls.opts:
            (cid, link, field) = (list(opt) + [None])[:3]
            if field is None and '__' in link:
                (nfield, rest) = link.split('__', 1)
                if not hasattr(cls.model, cid)\
                   and hasattr(cls.model, nfield):
                    (field, link) = (nfield, rest)
            yield (cid, link, field)
        # Yield extra options here via automatic association?

    def get_opt(self, cid, link, field=None, context=False):
        """Returns a value suitable for filtering"""
        value = self.get_value(cid)
        if self.query and not context:
            # No object lookup for haystack search
            return (cid, value)

        if value is not None:
            if field and hasattr(self.model, field):
                mfield = getattr(self.model, field)
                if type(mfield).__name__ == 'ManyRelatedObjectsDescriptor':
                    model = mfield.related.model.objects
                    qset = model.all()
                else:
                    model = mfield.field.rel.to
                    qset = mfield.get_queryset()
                try:
                    values = qset.filter(**{link: value})
                    if values.count() == 1:
                        value = values[0]
                    else:
                        value = [v for v in values]
                        field = field + '__in'
                except model.DoesNotExist:
                    value = None
            elif link.split('__')[-1] in ('isnull',):
                field = link
            elif link and not context:
                field = link
        return (context and cid or field, value)

    @cached_property
    def get_value_opts(self):
        """Similar to get_opt, but returns value useful for templates"""
        return [self.get_opt(*opt, context=True) for opt in self._opts()]

    @cached_property
    def get_cats(self):
        """Returns a list of category objects for each of the cats"""
        return [self.get_cat(*cat) for cat in self.cats]

    def get_cat(self, cid, name, model=None):
        """Gets the category object, which contains a list of possible options"""
        # We could move this into Category class XXX
        field = getattr(self.model, cid, None)
        if isinstance(model, str):
            qset = getattr(self, model)()
        elif field and hasattr(field, 'get_queryset'):
            qset = field.get_queryset()
        elif isinstance(model, Model):
            qset = model.objects.all()
        else:
            raise KeyError(("The field '%s' isn't a ForeignKey, please add "
                            "the linked model for this category.") % cid)
        if qset is None:
            return None
        return Category(self, qset, cid, name)

    def get(self, request, *args, **kwargs):
        """When the GET request is sent to this CategoryList"""
        qset = self.get_queryset()
        if self.redirect and not self.query and qset.count() == 1:
            item = qset.get()
            if hasattr(item, 'get_absolute_url'):
                return redirect(item.get_absolute_url())
        if self.query:
            qset = SearchIter(qset)
        context = self.get_context_data(object_list=qset, **kwargs)
        return self.render_to_response(context)

    def get_template_names(self):
        """Returns remplate name based on ListView.get_template_names()"""
        opts = self.model._meta
        return ["%s/%s_list.html" % (opts.app_label, opts.object_name.lower())]

    def get_context_data(self, **kwargs):
        """Allows search results and object queries to work the same way."""
        data = super().get_context_data(**kwargs)
        if not hasattr(self.model, 'object'):
            self.model.object = lambda self: self

        data['query'] = self.get_value('q')
        data['orders'] = self.get_orders()

        data['categories'] = []
        for cat in self.get_cats:
            if cat is not None:
                data['categories'].append(cat)
                cat.conclude(self)
                if cat.item != cat[0]:
                    data[cat.cid] = cat.item

        data.update(self.get_value_opts)

        if self.rss_view:
            data['rss_url'] = self.get_url(view=self.rss_view)
        data['clear_url'] = self.get_url(exclude='q')
        return data

    def get_orders(self):
        """Returns ordering information, column names and '-' prefixes"""
        order = self.get_value('order', self.order or self.orders[0][0])
        for (odr, label) in self.orders:
            yield {'id': odr, 'name': label, 'down': (order or '*')[0] == '-',
                   'active': order.strip('-') == odr.strip('-'),
                   'order': order,
                   'url': self.get_url('order', reverse_order(odr, odr == order))}
