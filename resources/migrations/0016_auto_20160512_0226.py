# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('resources', '0015_auto_20160425_1047'),
    ]

    operations = [
        migrations.CreateModel(
            name='TagCategory',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=48)),
                ('categories', models.ManyToManyField(help_text='Only show with these categories', to='resources.Category')),
            ],
        ),
        migrations.RemoveField(
            model_name='tag',
            name='parent',
        ),
        migrations.AddField(
            model_name='resourcefile',
            name='checked_by',
            field=models.ForeignKey(related_name='resource_checks', blank=True, to=settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE),
        ),
        migrations.AddField(
            model_name='resourcefile',
            name='checked_sig',
            field=models.FileField(upload_to='resources/sigs', null=True, verbose_name='Counter Signature', blank=True),
        ),
        migrations.AddField(
            model_name='tag',
            name='category',
            field=models.ForeignKey(related_name='tags', blank=True, to='resources.TagCategory', null=True, on_delete=models.CASCADE),
        ),
    ]
