# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('news', '0003_auto_20160302_0515'),
    ]

    operations = [
        migrations.AlterField(
            model_name='news',
            name='language',
            field=models.CharField(help_text='Translated version of another news item.', max_length=8, verbose_name='Language', db_index=True, choices=[('de', 'German'), ('da', 'Danish'), ('fr', 'French'), ('nl', 'Dutch'), ('it', 'Italian'), ('es', 'Spanish'), ('pt', 'Portuguese'), ('pt-br', 'Brazilian Portuguese'), ('cs', 'Czech'), ('ru', 'Russian'), ('ja', 'Japanese'), ('zh', 'Chinese'), ('zh-hant', 'Simplified Chinese'), ('ko', 'Korean')]),
        ),
    ]
