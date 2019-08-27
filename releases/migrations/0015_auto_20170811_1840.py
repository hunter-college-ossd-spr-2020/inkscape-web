# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('releases', '0014_auto_20170808_2342'),
    ]

    operations = [
        migrations.CreateModel(
            name='PlatformTranslation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('language', models.CharField(help_text='Which language is this translated into.', max_length=8, verbose_name='Language', db_index=True, choices=[('ar', 'Arabic'), ('de', 'German'), ('da', 'Danish'), ('fr', 'French'), ('nl', 'Dutch'), ('it', 'Italian'), ('es', 'Spanish'), ('pt', 'Portuguese'), ('pt-br', 'Brazilian Portuguese'), ('cs', 'Czech'), ('ru', 'Russian'), ('sk', 'Slovak'), ('ja', 'Japanese'), ('zh', 'Simplified Chinese'), ('zh-hant', 'Traditional Chinese'), ('ko', 'Korean')])),
                ('name', models.CharField(max_length=64, verbose_name='Name')),
                ('desc', models.CharField(max_length=255, verbose_name='Description')),
                ('instruct', models.TextField(null=True, verbose_name='Instructions', blank=True)),
                ('platform', models.ForeignKey(related_name='translations', to='releases.Platform', on_delete=models.CASCADE)),
            ],
        ),
        migrations.CreateModel(
            name='ReleasePlatformTranslation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('language', models.CharField(help_text='Which language is this translated into.', max_length=8, verbose_name='Language', db_index=True, choices=[('ar', 'Arabic'), ('de', 'German'), ('da', 'Danish'), ('fr', 'French'), ('nl', 'Dutch'), ('it', 'Italian'), ('es', 'Spanish'), ('pt', 'Portuguese'), ('pt-br', 'Brazilian Portuguese'), ('cs', 'Czech'), ('ru', 'Russian'), ('sk', 'Slovak'), ('ja', 'Japanese'), ('zh', 'Simplified Chinese'), ('zh-hant', 'Traditional Chinese'), ('ko', 'Korean')])),
                ('howto', models.URLField(null=True, verbose_name='Instructions Link', blank=True)),
                ('info', models.TextField(null=True, verbose_name='Release Platform Information', blank=True)),
                ('release_platform', models.ForeignKey(related_name='translations', to='releases.ReleasePlatform', on_delete=models.CASCADE)),
            ],
        ),
        migrations.RenameField(
            model_name='releasetranslation',
            old_name='translated_notes',
            new_name='release_notes',
        ),
        migrations.AlterUniqueTogether(
            name='releasetranslation',
            unique_together=set([('release', 'language')]),
        ),
        migrations.AlterUniqueTogether(
            name='releaseplatformtranslation',
            unique_together=set([('release_platform', 'language')]),
        ),
        migrations.AlterUniqueTogether(
            name='platformtranslation',
            unique_together=set([('platform', 'language')]),
        ),
    ]
