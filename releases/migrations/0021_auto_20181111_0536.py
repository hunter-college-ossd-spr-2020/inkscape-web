# -*- coding: utf-8 -*-
# Generated by Django 1.11.15 on 2018-11-11 05:36
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('releases', '0020_auto_20181111_0530'),
    ]

    operations = [
        migrations.AlterField(
            model_name='release',
            name='version',
            field=models.CharField(db_index=True, max_length=16, verbose_name='Version'),
        ),
        migrations.AlterUniqueTogether(
            name='release',
            unique_together=set([('project', 'version')]),
        ),
    ]
