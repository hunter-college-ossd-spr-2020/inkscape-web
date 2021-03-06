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

from django.utils.functional import cached_property
from django.conf import settings
from django.apps import AppConfig
from django.db.models.signals import post_save

def post_create(model, func):
    """Signal wrapper around post_save that calls on create only"""
    def _inner(sender, instance, created=False, **kw):
        if created:
            func(instance, **kw)
    post_save.connect(_inner, sender=model, weak=False)


class ForumsConfig(AppConfig):
    """
    Control the signals and plugins for forum and comment creation
    """
    name = 'forums'
    # plugins is a list of all Plugin classes (based on BasePlugin)
    plugins = []
    # plugin is a dictionary of initialised plugin objects.
    plugin = {}

    @cached_property
    def get_topic_contenttype(self):
        """Return the content type for ForumTopic"""
        from .models import ForumTopic
        from django.contrib.contenttypes.models import ContentType
        return ContentType.objects.get_for_model(ForumTopic).pk

    def ready(self):
        from .models import Forum, ForumTopic
        from django_comments.models import Comment

        post_save.connect(self.save_comment, sender=Comment, weak=False)
        post_create(Forum, self.new_forum)

        topic_qset = ForumTopic.objects.select_related('forum')
        app = self

        def get_topic(self):
            """Get a topic for a comment"""
            if self.content_type_id == app.get_topic_contenttype:
                return topic_qset.get(pk=self.object_pk)
            try:
                return topic_qset.get(
                    object_pk=self.object_pk,
                    forum__content_type_id=self.content_type_id)
            except ForumTopic.DoesNotExist:
                pass
            return None

        Comment.get_topic = get_topic

        for key, conf in getattr(settings, 'FORUM_SYNCS', {}).items():
            try:
                module = import_module(conf['ENGINE'])
                self.plugins.append(module.Plugin)
                self.plugin[key] = self.plugins[-1](key, conf.copy())
            except (KeyError, AttributeError) as err:
                logging.warning("Failed to load plugin %s", key)
                logging.warning(" -> Engine error: %s", str(err))
            except ImportError as err:
                logging.warning("Failed to load plugin %s", (key))
                logging.warning(" -> %s", str(err))

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
            comments = Comment.objects.filter(content_type=instance.content_type)
            for comment in comments.order_by('-submit_date'):
                if comment.object_pk not in done:
                    self.create_comment(comment)
                    done.append(comment.object_pk)

    def save_comment(self, instance, created=False, **kw):
        """Called when any comment is saved"""
        if created:
            self.create_comment(instance, **kw)

        if instance.user:
            topic = instance.get_topic()
            if topic is not None:
                topic.refresh_meta_data()

        # The alert is focused on topics, not comments
        from .alert import ForumTopicAlert
        alert = ForumTopicAlert.get_alert_type()
        action = 'new' if created else 'edit'
        alert.call(instance=instance.get_topic(), comment=instance, action=action)

    def create_comment(self, instance, **kw):
        """Called when a new comment has been saved"""
        from .models import Forum, ForumTopic
        defaults = {
            'subject': str(instance.content_object),
            'first_username': instance.user.username,
        }

        for forum in Forum.objects.filter(content_type=instance.content_type):
            try:
                (topic, create) = ForumTopic.objects.get_or_create(forum_id=forum.pk,
                                  object_pk=instance.object_pk, defaults=defaults)
            except ForumTopic.MultipleObjectsReturned:
                continue

        topic = instance.get_topic()
        if topic is not None:
            topic.refresh_meta_data(instance)
            topic.forum.refresh_meta_data(instance)
