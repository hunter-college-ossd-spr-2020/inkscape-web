# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0006_require_contenttypes_0002'),
        ('cmsplugin_news', '0006_auto_20170107_2355'),
    ]

    operations = [
        migrations.CreateModel(
            name='NewsBacklink',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('url', models.URLField()),
                ('delibrate', models.BooleanField(default=True, help_text='Was this post done by a known contributor?')),
            ],
            options={
                'db_table': 'cmsplugin_news_newsbacklink',
            },
        ),
        migrations.CreateModel(
            name='SocialMediaType',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=255)),
                ('icon', models.ImageField(upload_to='news/icons')),
            ],
            options={
                'db_table': 'cmsplugin_news_socialmediatype',
            },
        ),
        migrations.AddField(
            model_name='latestnewsplugin',
            name='group',
            field=models.ForeignKey(blank=True, to='auth.Group', help_text='Limit this news plugin to this group only. If set to  "None" then this plugin will only show news with NO group.', null=True),
        ),
        migrations.AddField(
            model_name='news',
            name='group',
            field=models.ForeignKey(blank=True, to='auth.Group', help_text="News group indicates that this news is exclusive to this group only. This usually means it won't be visible on the main news listings, but instead is listed elsewhere.", null=True),
        ),
        migrations.AlterField(
            model_name='latestnewsplugin',
            name='cmsplugin_ptr',
            field=models.OneToOneField(parent_link=True, related_name='cmsplugin_news_latestnewsplugin', auto_created=True, primary_key=True, serialize=False, to='cms.CMSPlugin'),
        ),
        migrations.AddField(
            model_name='newsbacklink',
            name='news',
            field=models.ForeignKey(to='cmsplugin_news.News'),
        ),
        migrations.AddField(
            model_name='newsbacklink',
            name='social_media',
            field=models.ForeignKey(blank=True, to='cmsplugin_news.SocialMediaType', null=True),
        ),
    ]
