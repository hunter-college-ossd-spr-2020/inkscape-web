# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('releases', '0015_auto_20170811_1840'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='releaseplatform',
            options={'ordering': ('platform__parent_id',)},
        ),
        migrations.AlterModelOptions(
            name='releasestatus',
            options={'verbose_name_plural': 'Release Statuses'},
        ),
        migrations.AddField(
            model_name='platform',
            name='keywords',
            field=models.CharField(max_length=255, null=True, verbose_name='HTML Keywords', blank=True),
        ),
        migrations.AddField(
            model_name='platformtranslation',
            name='keywords',
            field=models.CharField(max_length=255, null=True, verbose_name='HTML Keywords', blank=True),
        ),
        migrations.AddField(
            model_name='release',
            name='html_desc',
            field=models.CharField(max_length=255, null=True, verbose_name='HTML Description', blank=True),
        ),
        migrations.AddField(
            model_name='release',
            name='keywords',
            field=models.CharField(max_length=255, null=True, verbose_name='HTML Keywords', blank=True),
        ),
        migrations.AddField(
            model_name='releasetranslation',
            name='html_desc',
            field=models.CharField(max_length=255, null=True, verbose_name='HTML Description', blank=True),
        ),
        migrations.AddField(
            model_name='releasetranslation',
            name='keywords',
            field=models.CharField(max_length=255, null=True, verbose_name='HTML Keywords', blank=True),
        ),
    ]
