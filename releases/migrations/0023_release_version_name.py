# -*- coding: utf-8 -*-
# Generated by Django 1.11.15 on 2019-10-08 15:31
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('releases', '0022_auto_20191008_1425'),
    ]

    operations = [
        migrations.AddField(
            model_name='release',
            name='version_name',
            field=models.CharField(blank=True, help_text='If set, uses this string for the version in the display.', max_length=64, null=True, verbose_name='Version Name'),
        ),
    ]
