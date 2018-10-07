# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import inkscape.fields


class Migration(migrations.Migration):

    dependencies = [
        ('resources', '0039_auto_20170505_1443'),
    ]

    operations = [
        migrations.AlterField(
            model_name='gallery',
            name='thumbnail',
            field=inkscape.fields.ResizedImageField(format='PNG', upload_to='resources/thum', max_width=190, min_height=0, max_height=190, blank=True, min_width=0, null=True, verbose_name='Thumbnail'),
        ),
        migrations.AlterField(
            model_name='resource',
            name='rendering',
            field=inkscape.fields.ResizedImageField(format='PNG', upload_to='resources/render', max_width=780, min_height=0, max_height=600, blank=True, min_width=0, null=True, verbose_name='Rendering'),
        ),
        migrations.AlterField(
            model_name='resource',
            name='thumbnail',
            field=inkscape.fields.ResizedImageField(format='PNG', upload_to='resources/thum', max_width=190, min_height=0, max_height=190, blank=True, min_width=0, null=True, verbose_name='Thumbnail'),
        ),
    ]
