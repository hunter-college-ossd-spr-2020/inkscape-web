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
Test the forum app
"""
import time

from datetime import datetime

import django_comments
from django.utils import translation
from django.utils.timezone import utc
from django.core.urlresolvers import reverse

from extratest.base import ExtraTestCase

from django_comments.models import Comment
from forums.models import Forum, ForumTopic, ContentType

from django.db.models import Model, CharField

class TestObject(Model):
    """Test object for model"""
    name = CharField(max_length=12)

    class Meta:
        app_label = 'forums'

    def __str__(self):
        return self.name


class BaseCase(ExtraTestCase):
    fixtures = ['test-auth', 'test-contenttype', 'test-forums', 'test-comments']
    credentials = dict(username='tester', password='123456')


class ForumsTests(BaseCase):
    """Tests for forums listings"""
    def test_list_forums(self):
        """List all forums, with names and descriptions"""
        get = self.assertGet('forums:list', status=200)
        self.assertContains(get, 'Section One')
        self.assertContains(get, 'Section Two')

        self.assertContains(get, 'Art')
        self.assertContains(get, 'General Discussion')
        self.assertContains(get, 'Talk about Trees')

        self.assertNotContains(get, 'German Forum')

    def test_lang_forums(self):
        """List forums with special language"""
        lang = translation.get_language()
        translation.activate('de')
        get = self.assertGet('forums:list', status=200)

        self.assertContains(get, 'General Discussion')
        self.assertContains(get, 'Talk about Trees')

        self.assertContains(get, 'German Forum')
        translation.activate(lang)


class CleanForumTests(BaseCase):
    """Tests for non-object forum details"""
    def setUp(self):
        super(type(self), self).setUp()
        self.forum = self.getObj(Forum, content_type__isnull=True).slug

    def test_list_all_topics(self):
        """List all topics in clean forum"""
        get = self.assertGet('forums:detail', slug=self.forum, status=200)
        self.assertContains(get, "Talk about Trees")
        self.assertContains(get, "New Topic")
        self.assertContains(get, "Topic Five")

    def test_crate_topic(self):
        """Crate a new clean topic"""
        (get, post) = self.assertBoth('forums:create', slug=self.forum,
            status=200, data={'subject': "Fish", 'comment': "Hello World"})

        self.assertEqual(post.context_data['object'].forum.slug, self.forum)
        self.assertEqual(post.context_data['object'].subject, 'Fish')

    def test_sticky_post(self):
        """A topic which is sticky"""
        get = self.assertGet('forums:detail', slug='general', status=200)
        topics = get.context_data['object'].topics.values_list('slug', flat=True)
        self.assertEqual(tuple(topics[:3]), (u'sticky_two', u'sticky_three', u'sticky_one'))


class ObjectForumTests(BaseCase):
    """Tests for object forum details"""
    def setUp(self):
        super(type(self), self).setUp()
        self.forum = self.getObj(Forum, content_type__isnull=False)

    def test_list_all_topics(self):
        """List all objects as discussions"""
        get = self.assertGet('forums:detail', slug=self.forum.slug, status=200)
        self.assertContains(get, "<h2>Art</h2>")
        self.assertNotContains(get, "New Topic")
        self.assertContains(get, "Topic Two")
        self.assertContains(get, "Topic Three")
        self.assertContains(get, "Topic One")

    def test_non_commented_objects(self):
        """Objects without comments aren't listed"""
        ct = ContentType.objects.get_for_model(TestObject)
        obj = Forum.objects.create(name="New Art Forum", content_type=ct, group_id=1)
        obj = Forum.objects.get(slug=obj.slug)
        self.assertEqual(obj.topics.count(), 2)
        self.assertEqual(obj.last_posted, datetime(2011, 3, 1, 10, 10, 10, tzinfo=utc))
        get = self.assertGet(obj.get_absolute_url(), status=200)
        self.assertContains(get, "Test Object One")
        self.assertContains(get, "Test Object Two")
        self.assertNotContains(get, "Test Object Three")

    def test_create_topic(self):
        """Fail to crate a new object topic"""
        self.assertBoth('forums:create', slug=self.forum.slug, status=404)

    def test_crate_new_comment(self):
        """Commenting on object creates topic"""
        pks = set(self.forum.topics.values_list('object_pk', flat=True))
        obj = self.getObj(TestObject, not_id__in=list(pks))
        self.assertEqual(self.forum.topics.count(), 3)
        com = Comment.objects.create(
          submit_date=datetime(2015, 5, 5, 5, 5, 5, tzinfo=utc),
          content_type=self.forum.content_type,
          object_pk=obj.pk,
          site_id=1,
        )
        forum = self.getObj(Forum, pk=self.forum.pk)
        self.assertEqual(forum.topics.count(), 4)
        self.assertEqual(forum.last_posted, com.submit_date)


class CleanTopicTests(BaseCase):
    """Topic tests without an object"""
    topic = dict(forum='general', slug='topic_four')
    override_settings = dict(DEBUG=True)

    def assertPostComment(self, obj, comment, status=200, **kw):
        kw['form'] = django_comments.get_form()(obj)
        data = kw.setdefault('data', {})
        data['comment'] = comment
        post = self.assertPost('comments-post-comment', **kw)
        if post.status_code == 400 and status != 400:
            text = post.content
            x = text.find("<td>", text.find('Why'))
            y = text.find("</td>", x)
            msg = text[x+4:y]
        else:
            msg = "Expected status %d, found %d" % (status, post.status_code)
        self.assertEqual(status, post.status_code, msg)
        return post

    def test_all_comments(self):
        """List all comments on this topic"""
        get = self.assertGet('forums:topic', status=200, **self.topic)
        self.assertContains(get, 'BarBzr')
        self.assertContains(get, 'Buz')

    def test_can_comment(self):
        """A new comment can be added"""
        get = self.assertGet('forums:topic', status=200, **self.topic)
        self.assertContains(get, 'comments/post/')
        obj = get.context_data['object']

        post = self.assertPostComment(obj, "Plums are the best")

        get = self.assertGet('forums:topic', status=200, **self.topic)
        self.assertContains(get, 'Plums are the best')

    def test_locked_post(self):
        """A topic can be locked and no new comments are allowed"""
        obj = self.getObj(ForumTopic, slug=self.topic['slug'])
        obj.locked = True
        obj.save()
        
        get = self.assertGet('forums:topic', status=200, **self.topic)
        self.assertNotContains(get, 'comments/post/')

        post = self.assertPostComment(obj, "Apples are Oranges from Wales", status=400)
        get = self.assertGet(obj.get_absolute_url(), status=200)
        self.assertNotContains(get, 'Apples are Oranges')


class ObjectTopicTests(BaseCase):
    """Topic tests when we have an object"""
    def test_header_template(self):
        """Topic shows custom topic header"""
        get = self.assertGet('forums:topic',
                forum='art', slug='topic_one', status=200)
        self.assertContains(get, 'HEADER<<Test Object Two>>END')

    def test_all_comments(self):
        """List of all comments in the topic"""
        get = self.assertGet('forums:topic',
                forum='art', slug='topic_one', status=200)
        self.assertContains(get, 'Who Don IT')

    def test_comments_on_topic(self):
        """Comments attached to the topic itself is ignored"""
        topic = ForumTopic.objects.get(slug='topic_one')
        ct = ContentType.objects.get_for_model(ForumTopic)
        com = Comment.objects.create(
          comment='Guess What',
          content_type=ct,
          object_pk=topic.pk,
          site_id=1,
        )
        get = self.assertGet('forums:topic',
                forum='art', slug='topic_one', status=200)
        self.assertNotContains(get, 'Guess What')

