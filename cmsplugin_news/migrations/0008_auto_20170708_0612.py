# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cmsplugin_news', '0007_auto_20170614_2059'),
    ]

    operations = [
        migrations.AddField(
            model_name='news',
            name='is_notified',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='news',
            name='pub_date',
            field=models.DateTimeField(null=True, verbose_name='Publication date'),
        ),
        migrations.AlterField(
            model_name='news',
            name='slug',
            field=models.SlugField(help_text='A slug is a short name which provides a unique url.', null=True, verbose_name='Slug'),
        ),
        migrations.AlterField(
            model_name='newsbacklink',
            name='news',
            field=models.ForeignKey(related_name='backlinks', to='cmsplugin_news.News'),
        ),
    ]
