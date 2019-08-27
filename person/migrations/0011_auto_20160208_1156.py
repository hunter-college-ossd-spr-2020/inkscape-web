# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('person', '0010_auto_20160206_0535'),
    ]

    operations = [
        migrations.CreateModel(
            name='TeamChatRoom',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('channel', models.CharField(max_length=64, verbose_name='IRC Chatroom Name')),
                ('language', models.CharField(default='en', max_length=5, choices=[('en', 'English'), ('de', 'German'), ('da', 'Danish'), ('fr', 'French'), ('nl', 'Dutch'), ('it', 'Italian'), ('es', 'Spanish'), ('pt', 'Portuguese'), ('pt-br', 'Brazilian Portuguese'), ('cs', 'Czech'), ('ru', 'Russian'), ('ja', 'Japanese'), ('zh', 'Chinese'), ('zh-hant', 'Simplified Chinese'), ('ko', 'Korean')])),
                ('admin', models.ForeignKey(blank=True, to=settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE)),
            ],
        ),
        migrations.RemoveField(
            model_name='team',
            name='ircroom',
        ),
        migrations.AddField(
            model_name='teamchatroom',
            name='team',
            field=models.ForeignKey(related_name='ircrooms', to='person.Team', on_delete=models.CASCADE),
        ),
        migrations.AlterUniqueTogether(
            name='teamchatroom',
            unique_together=set([('language', 'team')]),
        ),
    ]
