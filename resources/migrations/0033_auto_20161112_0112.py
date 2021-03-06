# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from inkscape.fields import ResizedImageField

class Migration(migrations.Migration):

    dependencies = [
        ('resources', '0032_auto_20161109_2014'),
    ]

    operations = [
        migrations.AddField(
            model_name='resource',
            name='rendering',
            field=ResizedImageField(format='PNG', upload_to='resources/render', max_width=780, min_height=0, max_height=600, blank=True, min_width=0, null=True, verbose_name='Rendering'),
        ),
        migrations.AlterField(
            model_name='resource',
            name='thumbnail',
            field=ResizedImageField(format='PNG', upload_to='resources/thum', max_width=190, min_height=0, max_height=190, blank=True, min_width=0, null=True, verbose_name='Thumbnail'),
        ),
    ]
