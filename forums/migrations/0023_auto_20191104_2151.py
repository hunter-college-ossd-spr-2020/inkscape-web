# -*- coding: utf-8 -*-
# Generated by Django 1.11.15 on 2019-11-04 21:51
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('forums', '0022_auto_20191101_0446'),
    ]

    operations = [
        migrations.AlterField(
            model_name='commentattachment',
            name='inline',
            field=models.IntegerField(choices=[(0, 'Attachment'), (1, 'Gallery'), (2, 'Embeded')], default=0),
        ),
    ]
