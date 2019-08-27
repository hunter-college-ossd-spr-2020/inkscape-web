# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('releases', '0009_auto_20160604_1633'),
    ]

    operations = [
        migrations.AlterField(
            model_name='release',
            name='bug_manager',
            field=models.ForeignKey(related_name='bug_releases', blank=True, to=settings.AUTH_USER_MODEL, help_text='Manages critical bugs and decides what needs fixing.', null=True, verbose_name='Bug Manager', on_delete=models.CASCADE),
        ),
        migrations.AlterField(
            model_name='release',
            name='manager',
            field=models.ForeignKey(related_name='releases', blank=True, to=settings.AUTH_USER_MODEL, help_text='Looks after the release schedule and release meetings.', null=True, verbose_name='Manager', on_delete=models.CASCADE),
        ),
        migrations.AlterField(
            model_name='release',
            name='reviewer',
            field=models.ForeignKey(related_name='rev_releases', blank=True, to=settings.AUTH_USER_MODEL, help_text='Reviewers help to make sure the release is working.', null=True, verbose_name='Reviewer', on_delete=models.CASCADE),
        ),
        migrations.AlterField(
            model_name='release',
            name='translation_manager',
            field=models.ForeignKey(related_name='tr_releases', blank=True, to=settings.AUTH_USER_MODEL, help_text='Translation managers look after all translations for the release.', null=True, verbose_name='Translation Manager', on_delete=models.CASCADE),
        ),
        migrations.AlterField(
            model_name='releasetranslation',
            name='language',
            field=models.CharField(help_text='Which language is this translated into.', max_length=8, verbose_name='Language', db_index=True, choices=[('ar', 'Arabic'), ('de', 'German'), ('da', 'Danish'), ('fr', 'French'), ('nl', 'Dutch'), ('it', 'Italian'), ('es', 'Spanish'), ('pt', 'Portuguese'), ('pt-br', 'Brazilian Portuguese'), ('cs', 'Czech'), ('ru', 'Russian'), ('sk', 'Slovak'), ('ja', 'Japanese'), ('zh', 'Simplified Chinese'), ('zh-hant', 'Traditional Chinese'), ('ko', 'Korean')]),
        ),
    ]
