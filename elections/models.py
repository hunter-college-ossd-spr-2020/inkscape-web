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

from random import choice, sample
from collections import Counter
from string import ascii_letters

from py3votecore.stv import STV

from django.utils.timezone import now
from django.utils.translation import ugettext_lazy as _
from django.core.urlresolvers import reverse
from django.contrib.auth import get_user_model

from django.conf import settings
from django.db.models import (
    Manager, Model, SlugField, ForeignKey, CharField, DateTimeField,
    DateField, PositiveIntegerField, TextField, BooleanField
)

from person.models import Team

from .results import BALLOT_TYPES, get_log as _get_log, make_log


def get_hash():
    """Returns a generated hash to model fields"""
    return ''.join(choice(ascii_letters) for _ in range(50))


User = settings.AUTH_USER_MODEL # pylint: disable=invalid-name
null = dict(null=True, blank=True) # pylint: disable=invalid-name

STATUSES = [
    ('.', _('Planning'), _('Planning the election.')),
    ('N', _('Nominating'), _('Nominating candidates to stand.')),
    ('S', _('Selecting'), _("Candidates' extra time for accepting a nomination")),
    ('V', _('Voting'), _('Voting is open to constituents')),
    ('F', _('Finished'), _('Voting is closed, Results announced')),
    ('!', _('Insufficient Candidates'), _('Electing Canceled, Failed to get enough candidates.')),
    ('*', _('Insufficient Votes'), _('Electing Canceled, Failed to get enough voters to vote.')),
]
RESTAT = list(zip(*STATUSES))
(PLANNING, NOMINATING, SELECTING, VOTING, FINISHED, INCAN, INVOT) = RESTAT[0]
FAILURE = {'S': '!', 'V': '*'}

class Election(Model):
    """A single election as held by a group"""
    slug = SlugField(max_length=32,\
         help_text=_('Unique name used to identify this election in urls.'))

    for_team = ForeignKey(Team, related_name='elections',\
        help_text=_('The team wanting new members.'))
    for_role = CharField(max_length=128, null=True, blank=True,\
        help_text=_('The role the elected members will have in the team.'))
    constituents = ForeignKey(Team, related_name='election_votes',\
        help_text=_('People allowed to vote.'))
    called_by = ForeignKey(User,\
        help_text=_('You, the responsible person for this election.'))
    called_on = DateTimeField(auto_now=True)

    status = CharField(max_length=1, db_index=True,\
        choices=zip(RESTAT[0], RESTAT[2]), default=PLANNING)

    invite_from = DateField(help_text=_('Start the nominations process on this'\
        ' date, emails are sent out as invites are created (UTC).'))
    accept_from = DateField(help_text=_('Invitation process stops and'\
        ' invitees have this extra amount of time to accept it. (UTC)'))
    voting_from = DateField(\
        help_text=_('Finish the nominations and start voting (UTC).'))
    finish_on = DateField(\
        help_text=_('Finish the election, vote closed, wins announced (UTC).'))

    places = PositiveIntegerField(default=1, help_text=_('The number of place'\
        's that are available to be won in this election. If fewer candidates'\
        ' are available to stand, this election will fail and be canceled'))
    min_votes = PositiveIntegerField(default=2, help_text=_('A minimum number'\
        ' of votes required to make this a fair election. Insufficient votes'\
        ' will force the election to fail and be canceled.'))
    notes = TextField(help_text=_('Any notes about this election, why it was'\
        ' called or why new people are needed. Message is sent to constituent'\
        's during the invitation and voting periods.'), **null)

    # log records all the voters once the vote is finished. Votes are removed
    # as soon as the log is generated and saved. This also records all the
    # candidates. (see STV log for example of the kind of output we could have)
    # probably in json format.
    log = TextField(**null)

    year = property(lambda self: self.voting_from.year)
    parent = property(lambda self: self.for_team)
    intro = property(lambda self: self.notes)
    get_log = property(lambda self: _get_log(self.log))

    @property
    def name(self):
        """Generate a useful specific name for this election"""
        if not self.for_role:
            return _("Election for {0.for_team} ({0.year})").format(self)
        if self.constituents == self.for_team:
            return _("Election for {0.for_role} in {0.for_team}").format(self)
        return _("Election for {0.for_team} ({0.for_role})").format(self)

    class Meta:
        ordering = ('-finish_on',)

    def __str__(self):
        return self.slug

    @property
    def ballot_type(self):
        """Returns the ballot type"""
        return BALLOT_TYPES['pyvotecore.stv']

    def state(self):
        """Returns a state structure for this election"""
        ret = dict(process=[], index=RESTAT[0].index(self.status), fail=99)
        dates = (now().date(), self.invite_from, self.accept_from,
                 self.voting_from, self.finish_on, now().date())

        for x, data in enumerate(STATUSES):
            data = dict(zip(['code', 'name', 'desc'], data))
            if data['code'] not in '!*':
                # Generate some extra data about this state
                data['index'] = x
                data['date'] = dates[x]
                data['days'] = (dates[x] - now().date()).days

                # Save the data under it's code for easy template access
                ret[data['code']] = data

                # Append this to the process chain
                ret['process'].append(data)

                # Set the failure flag if required
                data['failed'] = self.status == FAILURE.get(data['code'], -1)
                if data['failed']:
                    ret['fail'] = x
            else:
                data['failed'] = True

            if x == ret['index']:
                ret.update(data)
        return ret

    def send_team_email(self, subject, tmp, **kw):
        """Send an email to the team involved"""
        from .alert import send_team_email
        send_team_email(self.constituents,
                        "Election {{ instance.for_team }}: {{ add }}",
                        "elections/alert/email_%s.txt" % tmp,
                        add=subject, instance=self, **kw)

    def invitation_open(self):
        """Move from PLANNING to NOMINATING"""
        self.send_team_email('Nominations', 'candidates_needed')
        self.status = NOMINATING
        self.save()

    def invitation_close(self):
        """Move from NOMINATING to SELECTING"""
        if self._candidates.count() < self.places:
            self.failed_to_invite()

        self.status = SELECTING
        self.save()

    def failed_to_invite(self):
        """This election doesn't have enough candidates"""
        self.status = INCAN
        self.save()
        # Send a message saying the election failed.
        self.send_team_email(_('Not enough candidates'), 'failed_candidates')

    def voting_open(self):
        """Move from ACCEPTED to VOTED"""
        # Change candidate hashes so they can't be added during the voting
        for candidate in self._candidates.all():
            candidate.slug = get_hash()
            candidate.save()

        count = self.candidates.count()
        if count == self.places:
            winners = self.candidates.values_list('user_id', flat=True)
            return self.voting_close(winners)
        elif count < self.places:
            return self.failed_to_invite()

        # Create one ballot for each member of the constituent team
        for membership in self.constituents.members:
            self.ballots.get_or_create(user=membership.user)

        # Set the status mode to VOTING
        self.status = VOTING
        self.save()

        # Send a message advertising that voting is open
        return self.send_team_email('Voting Open', 'voting_open')

    def failed_to_vote(self):
        """This election doesn't have enough candidates"""
        self.status = INVOT
        self.save()
        # Send a message saying the election failed.
        self.send_team_email(_('Not enough voters'), 'failed_votes')

    def voting_close(self, ballot=None):
        """Move from VOTED to FINISHED"""
        votes = list(self.ballots.get_votes())
        if self.ballots.count() < self.min_votes:
            if ballot:
                votes = [{'count': 1.0, 'ballot': ballot}]
            else:
                return self.failed_to_vote()

        res = STV(votes, required_winners=self.places)
        self.log = make_log(
            candidates=list(self._candidates.log()),
            results=res.as_dict(),
            votes=list(self.ballots.log()),
            type='pyvotecore.stv',
            counts=dict(
                candidates=self.candidates.count(),
                invites=self.invites.count(),
                ignored=self.ignored.count(),
                rejected=self.rejected.count(),
                ballots=self.ballots.count(),
                voters=self.voters.count(),
            ),
        )
        self.save()

        # Delete candidate and ballot objects out of the database, you may ask
        # Martin: why would you ever delete the voting record. This is because
        # django objects can be easily edited and are harder to backup. Plus
        # the nature of the log means we want to make sure ALL our results code
        # uses the log for it's information and not any residual stale objects.
        self._candidates.all().delete()
        self.ballots.all().delete()

        # Add new users to target team
        for user_id in res.winners:
            self.for_team.update_membership(
                get_user_model().objects.get(pk=user_id),
                expired=None, joined=now(),
                title=self.for_role,
                added_by=self.called_by
            )

        self.status = FINISHED
        self.save()

        # Send a message annoucing the results.
        self.send_team_email('Results', 'voting_finished')

    invites = property(lambda self: self._candidates.all())
    candidates = property(lambda self: self.invites.filter(accepted=True))
    ignored = property(lambda self: self.invites.filter(responded=False))
    rejected = property(lambda self: self.invites.filter(responded=True, accepted=False))
    voters = property(lambda self: self.ballots.filter(responded=True))

    def get_absolute_url(self):
        """Return a link to the election"""
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
    """Each candidate who is standing for an election"""
    slug = SlugField(default=get_hash)

    election = ForeignKey(Election, related_name='_candidates')
    invitor = ForeignKey(User, related_name='election_invitation')
    user = ForeignKey(User, related_name='election_stump')

    responded = BooleanField(default=False)
    accepted = BooleanField(default=False)

    objects = CandidateManager()

    def __str__(self):
        return "Candidate: %s" % str(self.user)

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
            result.update((tuple(ballot.get_vote()),))

        for ballot in result:
            # Return in grouped ballot format
            yield {'count': result[ballot], 'ballot': list(ballot)}


class Ballot(Model):
    """
    A vote is any user's capacity to vote on an election. 
    """
    slug = SlugField(default=get_hash, unique=True)
    user = ForeignKey(User, related_name='ballots')
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
            for v in qs.filter(rank__isnull=null)\
              .values_list('candidate__user_id').order_by('rank'):
                yield v[0]

    def random_vote(self):
        """Apply a random vote to this ballot (for testing)"""
        self.votes.all().delete()
        users = list(self.election.candidates)
        for x, user in enumerate(sample(users, len(users))):
            self.votes.update_or_create(candidate=user, defaults={'rank': x+1})
            self.responded = True
            self.save()


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

