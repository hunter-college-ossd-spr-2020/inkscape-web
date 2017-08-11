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
                ('language', models.CharField(help_text='Which language is this translated into.', max_length=8, verbose_name='Language', db_index=True, choices=[(b'ar', b'Arabic'), (b'de', b'German'), (b'da', b'Danish'), (b'fr', b'French'), (b'nl', b'Dutch'), (b'it', b'Italian'), (b'es', b'Spanish'), (b'pt', b'Portuguese'), (b'pt-br', b'Brazilian Portuguese'), (b'cs', b'Czech'), (b'ru', b'Russian'), (b'sk', b'Slovak'), (b'ja', b'Japanese'), (b'zh', b'Simplified Chinese'), (b'zh-hant', b'Traditional Chinese'), (b'ko', b'Korean')])),
                ('name', models.CharField(max_length=64, verbose_name='Name')),
                ('desc', models.CharField(max_length=255, verbose_name='Description')),
                ('instruct', models.TextField(null=True, verbose_name='Instructions', blank=True)),
                ('platform', models.ForeignKey(related_name='translations', to='releases.Platform')),
            ],
        ),
        migrations.CreateModel(
            name='ReleasePlatformTranslation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('language', models.CharField(help_text='Which language is this translated into.', max_length=8, verbose_name='Language', db_index=True, choices=[(b'ar', b'Arabic'), (b'de', b'German'), (b'da', b'Danish'), (b'fr', b'French'), (b'nl', b'Dutch'), (b'it', b'Italian'), (b'es', b'Spanish'), (b'pt', b'Portuguese'), (b'pt-br', b'Brazilian Portuguese'), (b'cs', b'Czech'), (b'ru', b'Russian'), (b'sk', b'Slovak'), (b'ja', b'Japanese'), (b'zh', b'Simplified Chinese'), (b'zh-hant', b'Traditional Chinese'), (b'ko', b'Korean')])),
                ('howto', models.URLField(null=True, verbose_name='Instructions Link', blank=True)),
                ('info', models.TextField(null=True, verbose_name='Release Platform Information', blank=True)),
                ('release_platform', models.ForeignKey(related_name='translations', to='releases.ReleasePlatform')),
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
