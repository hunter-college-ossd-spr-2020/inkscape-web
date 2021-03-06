# -*- coding: utf-8 -*-
# Generated by Django 1.11.15 on 2018-11-23 05:32
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('forums', '0009_auto_20181120_1744'),
    ]

    operations = [
        migrations.AddField(
            model_name='forumtopic',
            name='has_attachments',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='forumtopic',
            name='last_username',
            field=models.CharField(blank=True, max_length=128, null=True),
        ),
    ]
