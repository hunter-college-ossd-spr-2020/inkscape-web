# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('elections', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='election',
            name='min_votes',
            field=models.PositiveIntegerField(default=2, help_text='A minimum number of votes required to make this a fair election. Insufficiant votes will force the election to fail and be canceled.'),
        ),
        migrations.AlterField(
            model_name='ballot',
            name='user',
            field=models.ForeignKey(related_name='ballots', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='election',
            name='places',
            field=models.PositiveIntegerField(default=1, help_text='The number of places that are available to be won in this election. If fewer candidates are available to stand, this election will fail and be canceled'),
        ),
        migrations.AlterField(
            model_name='election',
            name='status',
            field=models.CharField(default=b'.', max_length=1, db_index=True, choices=[(b'.', 'Planning the election.'), (b'N', 'Nominating candidates to stand.'), (b'S', 'Candidates accepting to stand'), (b'V', 'Voting is open to constituents'), (b'F', 'Voting is closed, Results announced'), (b'!', 'Electing Canceled, Failed to get enough candidates.'), (b'*', 'Electing Canceled, Failed to get enough voters to vote.')]),
        ),
    ]
