# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.utils.timezone
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='News',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=255, verbose_name='Title')),
                ('slug', models.SlugField(unique_for_date='pub_date', blank=True, help_text='A slug is a short name which uniquely identifies the news item.', null=True, verbose_name='Slug')),
                ('excerpt', models.TextField(verbose_name='Excerpt', blank=True)),
                ('content', models.TextField(verbose_name='Content', blank=True)),
                ('is_published', models.BooleanField(default=False, verbose_name='Published')),
                ('pub_date', models.DateTimeField(default=django.utils.timezone.now, verbose_name='Publication date')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('link', models.URLField(help_text='This link will be used a absolute url for this item and replaces the view logic. <br />Note that by default this only applies for items with an empty "content" field.', null=True, verbose_name='Link', blank=True)),
                ('language', models.CharField(help_text='Translated version of another news item.', max_length=5, verbose_name='Language', choices=[('de', 'German'), ('da', 'Danish'), ('fr', 'French'), ('nl', 'Dutch'), ('it', 'Italian'), ('es', 'Spanish'), ('pt', 'Portuguese'), ('pt-br', 'Brazilian Portuguese'), ('cs', 'Czech'), ('ru', 'Russian'), ('ja', 'Japanese'), ('zh', 'Chinese'), ('zh-tw', 'Simplified Chinese'), ('ko', 'Korean')])),
                ('creator', models.ForeignKey(related_name='created_news', default=None, to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE)),
                ('editor', models.ForeignKey(related_name='edited_news', blank=True, to=settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE)),
                ('translation_of', models.ForeignKey(related_name='translations', blank=True, to='news.News', null=True, on_delete=models.CASCADE)),
            ],
            options={
                'ordering': ('-pub_date',),
                'verbose_name': 'News',
                'verbose_name_plural': 'News',
                'permissions': (('translate', 'Translate News'),),
                'db_table': 'cmsplugin_news_news',
            },
            bases=(models.Model,),
        ),
    ]
