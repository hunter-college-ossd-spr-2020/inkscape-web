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
Provide a way of intergrating membership into booleans
"""

from django.template import Library

from person.models import User, Team

register = Library() # pylint: disable=invalid-name

@register.filter()
def is_subscribed(this_user, that_user):
    """Returns true if that_user is subscribed to this_user"""
    if this_user.is_authenticated:
        return this_user.viewer_is_subscribed(that_user)
    return False

@register.filter()
def i_added(friendships, this_user):
    """Pass the currently logged in user to i_added"""
    return friendships.i_added(this_user)

@register.filter("membership")
def membership(obj, other):
    """Returns a queryset of membership for a given team"""
    if isinstance(obj, User) and isinstance(other, Team):
        return membership(other, obj)
    qset = obj.memberships.filter(user_id=other.pk)
    if qset.count() == 1:
        return qset.get()
    return {}
