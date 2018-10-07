# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('elections', '0002_auto_20170905_0355'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='election',
            options={'ordering': ('-finish_on',)},
        ),
        migrations.AlterField(
            model_name='election',
            name='accept_from',
            field=models.DateField(help_text='Invitation process stops and invitees have this extra amount of time to accept their invitations. (UTC)'),
        ),
        migrations.AlterField(
            model_name='election',
            name='finish_on',
            field=models.DateField(help_text='Finish the election, voting closed, winners announced (UTC).'),
        ),
        migrations.AlterField(
            model_name='election',
            name='invite_from',
            field=models.DateField(help_text='Start the nominations process on this date, emails are sent out as invites are created (UTC).'),
        ),
        migrations.AlterField(
            model_name='election',
            name='status',
            field=models.CharField(default='.', max_length=1, db_index=True, choices=[('.', 'Planning the election.'), ('N', 'Nominating candidates to stand.'), ('S', "Candidates' extra time for accepting a nomination"), ('V', 'Voting is open to constituents'), ('F', 'Voting is closed, Results announced'), ('!', 'Electing Canceled, Failed to get enough candidates.'), ('*', 'Electing Canceled, Failed to get enough voters to vote.')]),
        ),
    ]
