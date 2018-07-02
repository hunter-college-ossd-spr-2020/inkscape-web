#
# Copyright 2016, Martin Owens <doctormo@gmail.com>
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
Watches for comments so they can be registered.
"""
import logging
from importlib import import_module

from django.apps import AppConfig
from django.dispatch import receiver
from django.db.models.signals import post_save

from django.conf import settings


def post_create(model, fn):
    def _inner(sender, instance, created=False, **kw):
        if created:
            fn(instance, **kw)
    post_save.connect(_inner, sender=model, weak=False)


class ForumsConfig(AppConfig):
    name = 'forums'
    # plugins is a list of all Plugin classes (based on BasePlugin)
    plugins = []
    # plugin is a dictionary of initialised plugin objects.
    plugin = {}

    def ready(self):
        from .models import Forum
        from django_comments.models import Comment

        post_create(Comment, self.new_comment)
        post_create(Forum, self.new_forum)

        for key, conf in getattr(settings, 'FORUM_SYNCS', {}).items():
            try:
                module = import_module(conf['ENGINE'])
                self.plugins.append(module.Plugin)
                self.plugin[key] = self.plugins[-1](key, conf.copy())
            except (KeyError, AttributeError) as err:
                logging.warning("Failed to load plugin %s" % key)
                logging.warning(" -> Engine error: %s" % str(err))
            except ImportError as err:
                logging.warning("Failed to load plugin %s" % (key))
                logging.warning(" -> " + str(err))

    @property
    def sync_choices(self):
        """Returns a list of tuples useful for a choices dropdown"""
        return [(key, plugin.name) for key, plugin in self.plugin.items()]

    def new_forum(self, instance, **kw):
        """Called when a new forum is created"""
        from django_comments.models import Comment

        done = []
        if instance.content_type:
            # Look for all existing comments that might exist for this object
            cms = Comment.objects.filter(content_type=instance.content_type)
            for comment in cms.order_by('-submit_date'):
                if comment.object_pk not in done:
                    self.new_comment(comment)
                    done.append(comment.object_pk)

    def new_comment(self, instance, **kw):
        """Called when a new comment has been saved"""
        from .models import Forum, ForumTopic
        defaults = {'subject': unicode(instance.content_object)}

        for forum in Forum.objects.filter(content_type=instance.content_type):
            try:
                (topic, _) = ForumTopic.objects.get_or_create(forum_id=forum.pk,
                                  object_pk=instance.object_pk, defaults=defaults)
            except ForumTopic.MultipleObjectsReturned:
                continue

            self.update_times(forum, topic, instance.submit_date)

        co = instance.content_object
        if isinstance(instance.content_object, ForumTopic):
            self.update_times(co.forum, co, instance.submit_date)

    def update_times(self, forum, topic, submit_date):
        """Updates the topic and forum last modified stamp"""
        for obj in (forum, topic):
            if not obj.last_posted or obj.last_posted < submit_date:
                obj.last_posted = submit_date
                obj.save(update_fields=['last_posted'])
