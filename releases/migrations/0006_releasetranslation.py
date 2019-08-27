# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('releases', '0005_auto_20160212_1459'),
    ]

    operations = [
        migrations.CreateModel(
            name='ReleaseTranslation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('language', models.CharField(help_text='Which language is this translated into.', max_length=8, verbose_name='Language', db_index=True, choices=[('de', 'German'), ('da', 'Danish'), ('fr', 'French'), ('nl', 'Dutch'), ('it', 'Italian'), ('es', 'Spanish'), ('pt', 'Portuguese'), ('pt-br', 'Brazilian Portuguese'), ('cs', 'Czech'), ('ru', 'Russian'), ('ja', 'Japanese'), ('zh', 'Chinese'), ('zh-hant', 'Simplified Chinese'), ('ko', 'Korean')])),
                ('translated_notes', models.TextField(verbose_name='Release notes')),
                ('release', models.ForeignKey(related_name='translations', to='releases.Release', on_delete=models.CASCADE)),
            ],
        ),
    ]
