#
# Copyright 2018, Martin Owens <doctormo@gmail.com>
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
Update all forum counts (in case they get out of sync and init)
"""

import logging

from django.core.management.base import BaseCommand
from forums.models import ForumTopic, Forum

class Command(BaseCommand):
    help = "Run once a day to sync up the post count fields"

    def handle(self, **_):
        for forum in Forum.objects.all():
            forum.post_count = forum.comments.count()
            forum.save(update_fields=['post_count'])
        for topic in ForumTopic.objects.all():
            if topic.first_username is None:
                comment = topic.comments.first()
                if comment:
                    topic.first_username = comment.user.username
            try:
                topic.post_count = topic.comments.count()
            except topic.forum.model_class().DoesNotExist:
                # Topic object disapeared.
                logging.warning("Removing topic for missing object: %s", str(topic))
                topic.delete()
                continue

            topic.save(update_fields=['post_count', 'first_username'])
