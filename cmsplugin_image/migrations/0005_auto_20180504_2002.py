# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cmsplugin_image', '0004_auto_20170107_2355'),
    ]

    operations = [
        migrations.AddField(
            model_name='image',
            name='nofollow',
            field=models.BooleanField(default=False, verbose_name='Add nofollow to link'),
        ),
        migrations.AlterField(
            model_name='image',
            name='cmsplugin_ptr',
            field=models.OneToOneField(parent_link=True, related_name='cmsplugin_image_image', auto_created=True, primary_key=True, serialize=False, to='cms.CMSPlugin'),
        ),
    ]
