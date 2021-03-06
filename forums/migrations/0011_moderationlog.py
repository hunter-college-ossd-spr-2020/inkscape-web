# -*- coding: utf-8 -*-
# Generated by Django 1.11.15 on 2018-11-24 01:01
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('django_comments', '0003_add_submit_date_index'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('forums', '0010_auto_20181123_0532'),
    ]

    operations = [
        migrations.CreateModel(
            name='ModerationLog',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('action', models.CharField(max_length=128)),
                ('performed', models.DateTimeField(auto_now=True, db_index=True)),
                ('detail', models.TextField(blank=True, null=True)),
                ('comment', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='django_comments.Comment')),
                ('moderator', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='forum_moderation_actions', to=settings.AUTH_USER_MODEL)),
                ('topic', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='forums.ForumTopic')),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ('performed',),
            },
        ),
    ]
