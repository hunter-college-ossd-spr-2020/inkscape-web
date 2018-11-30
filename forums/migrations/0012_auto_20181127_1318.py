# -*- coding: utf-8 -*-
# Generated by Django 1.11.15 on 2018-11-27 13:18
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('forums', '0011_moderationlog'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='forumtopic',
            options={'get_latest_by': 'last_posted', 'ordering': ('-sticky', '-last_posted'), 'permissions': (('can_post_comment', 'User can post comments to the forums.'), ('can_post_topic', 'User can make new forum topics.'))},
        ),
    ]