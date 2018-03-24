# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings
import cms.utils.permissions
import inkscape.fields


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0004_auto_20161211_0746'),
    ]

    operations = [
        migrations.AlterField(
            model_name='project',
            name='banner',
            field=inkscape.fields.ResizedImageField(format=b'PNG', default=b'/static/images/project_banner.png', upload_to=b'project/banner', max_width=920, min_height=90, max_height=120, min_width=600, verbose_name='Banner (920x120)'),
        ),
        migrations.AlterField(
            model_name='project',
            name='is_fundable',
            field=models.BooleanField(default=False, verbose_name='Fundable'),
        ),
        migrations.AlterField(
            model_name='project',
            name='logo',
            field=inkscape.fields.ResizedImageField(format=b'PNG', default=b'/static/images/project_logo.png', upload_to=b'project/logo', max_width=150, min_height=150, max_height=150, min_width=150, verbose_name='Logo (150x150)'),
        ),
        migrations.AlterField(
            model_name='project',
            name='proposer',
            field=models.ForeignKey(related_name='proposes_projects', default=cms.utils.permissions.get_current_user, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='report',
            name='image',
            field=inkscape.fields.ResizedImageField(format=b'PNG', upload_to=b'project/update/%Y', max_width=400, min_height=0, max_height=400, blank=True, min_width=0, null=True, verbose_name='Image'),
        ),
    ]
