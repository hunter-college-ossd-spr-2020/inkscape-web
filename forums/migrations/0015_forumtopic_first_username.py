# -*- coding: utf-8 -*-
# Generated by Django 1.11.15 on 2018-12-02 22:58
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('forums', '0014_userflag_created'),
    ]

    operations = [
        migrations.AddField(
            model_name='forumtopic',
            name='first_username',
            field=models.CharField(blank=True, max_length=128, null=True),
        ),
    ]