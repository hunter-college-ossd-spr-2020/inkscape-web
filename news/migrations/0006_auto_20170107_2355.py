# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cmsplugin_news', '0005_auto_20160324_0248'),
    ]

    operations = [
        migrations.AlterField(
            model_name='news',
            name='language',
            field=models.CharField(help_text='Translated version of another news item.', max_length=8, verbose_name='Language', db_index=True, choices=[('ar', 'Arabic'), ('de', 'German'), ('da', 'Danish'), ('fr', 'French'), ('nl', 'Dutch'), ('it', 'Italian'), ('es', 'Spanish'), ('pt', 'Portuguese'), ('pt-br', 'Brazilian Portuguese'), ('cs', 'Czech'), ('ru', 'Russian'), ('sk', 'Slovak'), ('ja', 'Japanese'), ('zh', 'Simplified Chinese'), ('zh-hant', 'Traditional Chinese'), ('ko', 'Korean')]),
        ),
    ]
