#
# Copyright 2017, Martin Owens <doctormo@gmail.com>
#
# This file is part of the software inkscape-web, consisting of custom 
# code for the Inkscape project's django-based website.
#
# inkscape-web is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# inkscape-web is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with inkscape-web.  If not, see <http://www.gnu.org/licenses/>.
#
"""
Hold elections for group memberships.
"""

import json
from pyvotecore.irv import IRV
from pyvotecore.stv import STV

from django.utils.timezone import now
from django.utils.translation import ugettext_lazy as _
from django.core.urlresolvers import reverse
from django.contrib.auth import get_user_model

from django.conf import settings
from django.db.models import *

from person.models import Team

from collections import Counter
from random import choice
from string import ascii_letters

from .results import BALLOT_TYPES, get_log, make_log

User = settings.AUTH_USER_MODEL

def get_hash():
    return ''.join(choice(ascii_letters) for _ in range(50))


null = dict(null=True, blank=True)

STATUSES = [
    ('.', _('Planning'), _('Planning the election.')),
    ('N', _('Nominating'), _('Nominating candidates to stand.')),
    ('S', _('Selecting'), _('Candidates accepting to stand')),
    ('V', _('Voting'), _('Voting is open to constituents')),
    ('F', _('Finished'), _('Voting is closed, Results announced')),
    ('!', _('Failed'), _('Electing Canceled, Failed.')),
]
RESTAT = zip(*STATUSES)
(PLANNING, NOMINATING, SELECTING, VOTING, FINISHED, FAILED) = RESTAT[0]

class Election(Model):
    slug = SlugField(max_length=32, help_text=_('Unique name used to identify'
        ' this election in urls.'))

    for_team = ForeignKey(Team, help_text=_('The team wanting new members.'),
        related_name='elections')
    constituents = ForeignKey(Team, help_text=_('People allowed to vote.'),
        related_name='election_votes')
    called_by = ForeignKey(User,
        help_text=_('You, the responsible person for this election.'))
    called_on = DateTimeField(auto_now=True)

    status = CharField(max_length=1, db_index=True,
        choices=zip(RESTAT[0], RESTAT[2]), default=PLANNING)

    invite_from = DateField(help_text=_('Start the nominations process on this'
        ' date, invitations are collected (UTC).'))
    accept_from = DateField(help_text=_('Invitation process stops and emails'
        ' sent out to potential candidates. (UTC)'))
    voting_from = DateField(help_text=_('Finish the nominations and start'
        ' voting (UTC).'))
    finish_on = DateField(help_text=_('Finish the contest, voting closed,'
        ' winners announced (UTC).'))

    places = PositiveIntegerField(default=1)
    notes  = TextField(help_text=_('Any notes about this election, why it was'
        ' called or why new people are needed. Message is sent to constituents'
        ' during the invitation and voting periods.'), **null)

    # log records all the voters once the vote is finished. Votes are removed
    # as soon as the log is generated and saved. This also records all the
    # candidates. (see STV log for example of the kind of output we could have)
    # probably in json format.
    log = TextField(**null)

    parent = property(lambda self: self.for_team)
    intro = property(lambda self: self.notes)
    name = property(lambda self: _("Election for %s (%d)") % (
        self.for_team, self.voting_from.year))
    get_log = property(lambda self: get_log(self.log))

    def __str__(self):
        return self.slug

    @property
    def ballot_type(self):
        return BALLOT_TYPES['pyvotecore.stv']

    def state(self):
        ret = dict(process=[], index=RESTAT[0].index(self.status))
        dates = (now().date(), self.invite_from, self.accept_from,
                 self.voting_from, self.finish_on, now().date())
        for x, data in enumerate(STATUSES[:-1]):
            data = zip(['code', 'name', 'desc'], data)
            ret['process'].append(dict(data)) 
            ret['process'][-1]['index'] = x
            ret['process'][-1]['days'] = (dates[x] - now().date()).days
            ret[data[0][1]] = ret['process'][-1]
            if x == ret['index']:
                ret.update(data)
        return ret

    def send_team_email(self, subject, tmp):
        from .alert import send_team_email
        send_team_email(self.constituents,
            "Election {{ instance.for_team }}: {{ add }}",
            "elections/alert/email_%s.txt" % tmp,
            add=subject, instance=self)

    def invitation_open(self):
        """Move from PLANNING to NOMINATING"""
        self.send_team_email('Nominations', 'candidates_needed')
        self.status = NOMINATING
        self.save()

    def invitation_close(self):
        """Move from NOMINATING to SELECTING"""
        self.status = SELECTING
        self.save()

    def voting_open(self):
        """Move from ACCEPTED to VOTED"""
        # Change candidate hashes so they can't be added during the voting
        for candidate in self._candidates.all():
            candidate.slug = get_hash()
            candidate.save()

        # Create one ballot for each member of the constituent team
        for membership in self.constituents.members:
            self.ballots.get_or_create(user=membership.user)

        # Set the status mode to VOTING
        self.status = VOTING
        self.save()

        # Send a message advertising that voting is open
        self.send_team_email('Voting Open', 'voting_open')

    def voting_close(self):
        """Move from VOTED to FINISHED"""
        res = STV(list(self.ballots.get_votes()), required_winners=self.places)
        self.log = make_log(
            candidates=list(self._candidates.log()),
            results=res.as_dict(),
            votes=list(self.ballots.log()),
            type='pyvotecore.stv',
        )
        self.save()

        # Delete candidate and ballot objects out of the database
        self._candidates.all().delete()
        self.ballots.all().delete()

        # Add new users to target team
        for candidate in self.candidates:
            if 'winner' in candidate:
                self.for_team.update_membership(candidate['user'],
                    expired=None, joined=now(),
                    added_by=self.called_by)

        self.status = FINISHED
        self.save()

        # Send a message annoucing the results.
        self.send_team_email('Results', 'voting_finished')

    @property
    def candidates(self):
        return self._candidates.filter(accepted=True)

    @property
    def invites(self):
        return self._candidates.all()

    def voters(self):
        return self.ballots.filter(responded=True)

    def get_absolute_url(self):
        return reverse('elections:item', kwargs={
            'team': self.for_team.slug, 'slug': self.slug,
        })


class CandidateManager(Manager):
    def log(self):
        """Create a list of candidates and add to log"""
        for candidate in self.get_queryset():
            yield {
              'user_id': candidate.user.pk,
              'first_name': candidate.user.first_name,
              'last_name': candidate.user.last_name,
              'username': candidate.user.username,
              'email': candidate.user.email,
              'invitor': candidate.invitor_id,
              'responded': candidate.responded,
              'accepted': candidate.accepted,
            }

class Candidate(Model):
    slug = SlugField(default=get_hash)

    election = ForeignKey(Election, related_name='_candidates')
    invitor = ForeignKey(User, related_name='election_invitation')
    user = ForeignKey(User, related_name='election_stump')

    responded = BooleanField(default=False)
    accepted = BooleanField(default=False)

    objects = CandidateManager()

    class Meta:
        unique_together = (('election', 'user'), ('election', 'invitor'))


class BallotManager(Manager):
    def log(self):
        """Collect votes and save to log"""
        for ballot in self.get_queryset():
            yield {
              'user_id': ballot.user.pk,
              'first_name': ballot.user.first_name,
              'last_name': ballot.user.last_name,
              'username': ballot.user.username,
              'email': ballot.user.email,
              'responded': ballot.responded,
              'paper': list(ballot.get_vote()),
            }

    def get_votes(self):
        """Returns a list of lists with ranked votes for IRV"""
        result = Counter()
        for ballot in self.get_queryset().filter(responded=True):
            # Add each ballot to the ballot count
            result.update((tuple(sorted(ballot.get_vote())),))

        for ballot in result:
            # Return in grouped ballot format
            yield {'count': result[ballot], 'ballot': list(ballot)}


class Ballot(Model):
    """
    A vote is any user's capacity to vote on an election. 
    """
    slug = SlugField(default=get_hash, unique=True)
    user = ForeignKey(User)
    election = ForeignKey(Election, related_name='ballots')
    responded = BooleanField(default=False)

    objects = BallotManager()

    class Meta:
        unique_together = ('user', 'election')

    def get_vote(self):
        # WARNING: Your database could spoil the ballot here by ordering
        # the votes with NULL before 1, this happens with sqlitedb, so we
        # force the database to give us non-null results first.
        qs = self.votes.all()
        for null in (False, True):
            for v in qs.filter(rank__isnull=null).values_list('candidate__user_id'):
                yield v[0]


class Vote(Model):
    """
    A ranked vote for a specific candidate
    """
    ballot = ForeignKey(Ballot, related_name='votes')
    candidate = ForeignKey(Candidate)
    rank = PositiveIntegerField(**null)

    class Meta:
        unique_together = (('ballot', 'rank'), ('ballot', 'candidate'))
        ordering = ('rank',)

