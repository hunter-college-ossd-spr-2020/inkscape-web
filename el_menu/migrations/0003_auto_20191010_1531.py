# -*- coding: utf-8 -*-
# Generated by Django 1.11.15 on 2019-10-10 15:31
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('el_menu', '0002_auto_20190222_0211'),
    ]

    operations = [
        migrations.CreateModel(
            name='MenuTranslation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('language', models.CharField(choices=[('ar', 'Arabic'), ('en', 'English'), ('de', 'German'), ('fr', 'French'), ('hr', 'Croatian'), ('it', 'Italian'), ('es', 'Spanish'), ('pt', 'Portuguese'), ('pt-br', 'Brazilian Portuguese'), ('cs', 'Czech'), ('ru', 'Russian'), ('ja', 'Japanese'), ('zh', 'Simplified Chinese'), ('zh-hant', 'Traditional Chinese'), ('ko', 'Korean')], db_index=True, max_length=12)),
                ('url', models.CharField(blank=True, max_length=255, null=True)),
                ('name', models.CharField(blank=True, max_length=128, null=True)),
                ('title', models.CharField(blank=True, max_length=255, null=True)),
            ],
        ),
        migrations.AlterModelOptions(
            name='menuitem',
            options={'ordering': ('order',)},
        ),
        migrations.RenameField(
            model_name='menuitem',
            old_name='root',
            new_name='lang',
        ),
        migrations.AlterField(
            model_name='menuitem',
            name='lang',
            field=models.CharField(choices=[('all', 'All Languages'), ('ar', 'Arabic'), ('en', 'English'), ('de', 'German'), ('fr', 'French'), ('hr', 'Croatian'), ('it', 'Italian'), ('es', 'Spanish'), ('pt', 'Portuguese'), ('pt-br', 'Brazilian Portuguese'), ('cs', 'Czech'), ('ru', 'Russian'), ('ja', 'Japanese'), ('zh', 'Simplified Chinese'), ('zh-hant', 'Traditional Chinese'), ('ko', 'Korean')], db_column='root_id', db_index=True, default='all', help_text='If set, this menu will only be available to this language. DO NOT use this for translations!', max_length=12),
        ),
        migrations.AlterField(
            model_name='menuitem',
            name='cms_id',
            field=models.IntegerField(blank=True, help_text='A content id (sometimes the CMS ID) which can link pages in different languages together.', null=True, verbose_name='Content ID'),
        ),
        migrations.DeleteModel(
            name='MenuRoot',
        ),
        migrations.AddField(
            model_name='menutranslation',
            name='item',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='translations', to='el_menu.MenuItem'),
        ),
        migrations.AlterUniqueTogether(
            name='menutranslation',
            unique_together=set([('item', 'language')]),
        ),
        migrations.RemoveField(
            model_name='menuitem',
            name='cms_id',
        ),
        migrations.AlterModelOptions(
            name='menutranslation',
            options={'ordering': ('language',)},
        ),
        migrations.AlterField(
            model_name='menuitem',
            name='parent',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='children', to='el_menu.MenuItem'),
        ),
        migrations.AlterField(
            model_name='menuitem',
            name='category',
            field=models.SlugField(blank=True, choices=[(None, 'Main Menu'), ('foot', 'Footer'), ('hidden', 'Hidden')], max_length=12, null=True),
        ),
    ]
