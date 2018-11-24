# -*- coding: utf-8 -*-
# Generated by Django 1.11.15 on 2018-11-20 17:44
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('forums', '0008_commentattachment_inline'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserFlag',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('flag', models.CharField(db_index=True, max_length=5, verbose_name='flag')),
                ('title', models.CharField(blank=True, max_length=32, null=True, verbose_name='title')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='forum_flags', to=settings.AUTH_USER_MODEL, verbose_name='user')),
            ],
            options={
                'verbose_name': 'user forum flag',
                'verbose_name_plural': 'user forum flags',
            },
        ),
        migrations.AlterUniqueTogether(
            name='userflag',
            unique_together=set([('user', 'flag')]),
        ),
    ]
