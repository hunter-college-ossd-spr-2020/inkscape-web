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
Takes posts from a phpBB forum and adds them to the website to random
users. This can be used to populate a forum with threads.
"""

import random

from django.core.management.base import BaseCommand
from django.core.files.temp import NamedTemporaryFile
from django.core.files.base import File

from ...plugins.phpbb import BeeBeeSite

class Command(BaseCommand):
    """Provide a command for creating users"""
    help = __doc__
    @staticmethod
    def add_arguments(parser):
        parser.add_argument(
            '--site',
            action='store',
            dest='url',
            default="http://inkscapeforum.com/",
            help='URL to a phpBB forum to source the random posts from.')
        parser.add_argument(
            '--num',
            action='store',
            dest='num',
            default=20,
            help='Number of posts to add to this forum.')
        return parser

    def handle(self, url, num=20, **options):
        for count, post in enumerate(self.get_posts(url)):
            if count >= num:
                break
            print("DEBUG", post.thread.forum, post.thread, post)
            # ['26', {'link': './viewforum.php?f=26&sid=b4d69d5b059fa128de849cbdc49290fb', 'name': 'Announcements', 'parent': None, 'desc': None}] ['16791', 'Trialling no moderation of posts for new users', {'link': './viewtopic.php?f=27&t=16791&sid=b4d69d5b059fa128de849cbdc49290fb', 'author': 'microUgly', 'created': 'Thu Jan 30, 2014 9:47 pm', 'views': '8284 '}] ['p62529', {'date': 'Sun Feb 23 2014 9:33 am', 'content': "<blockquote><div><cite>v1nce wrote:</cite>Why not but then you should grant moderation rights to more users IMHO.<br/><br/>Too much spam for kitchen announcements for me.</div></blockquote><br/><br/>In a way, everyone is a moderator.  If you are seeing spam, it's either because you are the first of 2 people to see it, or nobody before you bothered to report it.<br/><br/>I didn't think we would have trouble finding 2 people reporting spam.  If the entire community does not contain 2 regular visitors who would report spam, what are the odds of finding someone willing to give up their time to moderate?", 'author': 'microUgly'}]

    def get_posts(self, url):
        """Loops through forums and fields to get posts"""
        phpbb = BeeBeeSite(url)
        while True:
            forum = random.choice(list(phpbb.forums))
            thread = random.choice(list(forum.threads))
            for post in thread.posts:
                yield post
