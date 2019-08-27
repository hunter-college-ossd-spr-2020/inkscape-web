# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings
import elections.models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('person', '0020_auto_20170830_1713'),
    ]

    operations = [
        migrations.CreateModel(
            name='Ballot',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('slug', models.SlugField(default=elections.models.get_hash, unique=True)),
                ('responded', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='Candidate',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('slug', models.SlugField(default=elections.models.get_hash)),
                ('responded', models.BooleanField(default=False)),
                ('accepted', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='Election',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('slug', models.SlugField(help_text='Unique name used to identify this election in urls.', max_length=32)),
                ('called_on', models.DateTimeField(auto_now=True)),
                ('status', models.CharField(default='.', max_length=1, db_index=True, choices=[('.', 'Planning the election.'), ('N', 'Nominating candidates to stand.'), ('S', 'Candidates accepting to stand'), ('V', 'Voting is open to constituents'), ('F', 'Voting is closed, Results announced'), ('!', 'Electing Canceled, Failed.')])),
                ('invite_from', models.DateField(help_text='Start the nominations process on this date, invitations are collected (UTC).')),
                ('accept_from', models.DateField(help_text='Invitation process stops and emails sent out to potential candidates. (UTC)')),
                ('voting_from', models.DateField(help_text='Finish the nominations and start voting (UTC).')),
                ('finish_on', models.DateField(help_text='Finish the contest, voting closed, winners announced (UTC).')),
                ('places', models.PositiveIntegerField(default=1)),
                ('notes', models.TextField(help_text='Any notes about this election, why it was called or why new people are needed. Message is sent to constituents during the invitation and voting periods.', null=True, blank=True)),
                ('log', models.TextField(null=True, blank=True)),
                ('called_by', models.ForeignKey(help_text='You, the responsible person for this election.', to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE)),
                ('constituents', models.ForeignKey(related_name='election_votes', to='person.Team', help_text='People allowed to vote.', on_delete=models.CASCADE)),
                ('for_team', models.ForeignKey(related_name='elections', to='person.Team', help_text='The team wanting new members.', on_delete=models.CASCADE)),
            ],
        ),
        migrations.CreateModel(
            name='Vote',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('rank', models.PositiveIntegerField(null=True, blank=True)),
                ('ballot', models.ForeignKey(related_name='votes', to='elections.Ballot', on_delete=models.CASCADE)),
                ('candidate', models.ForeignKey(to='elections.Candidate', on_delete=models.CASCADE)),
            ],
            options={
                'ordering': ('rank',),
            },
        ),
        migrations.AddField(
            model_name='candidate',
            name='election',
            field=models.ForeignKey(related_name='_candidates', to='elections.Election', on_delete=models.CASCADE),
        ),
        migrations.AddField(
            model_name='candidate',
            name='invitor',
            field=models.ForeignKey(related_name='election_invitation', to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE),
        ),
        migrations.AddField(
            model_name='candidate',
            name='user',
            field=models.ForeignKey(related_name='election_stump', to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE),
        ),
        migrations.AddField(
            model_name='ballot',
            name='election',
            field=models.ForeignKey(related_name='ballots', to='elections.Election', on_delete=models.CASCADE),
        ),
        migrations.AddField(
            model_name='ballot',
            name='user',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE),
        ),
        migrations.AlterUniqueTogether(
            name='vote',
            unique_together=set([('ballot', 'rank'), ('ballot', 'candidate')]),
        ),
        migrations.AlterUniqueTogether(
            name='candidate',
            unique_together=set([('election', 'invitor'), ('election', 'user')]),
        ),
        migrations.AlterUniqueTogether(
            name='ballot',
            unique_together=set([('user', 'election')]),
        ),
    ]
