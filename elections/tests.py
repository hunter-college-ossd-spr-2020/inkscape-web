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
Test the election process
"""
from datetime import timedelta
from extratest.base import ExtraTestCase

from django.core import mail
from django.utils.timezone import now

from person.models import Team, User
from .models import Election

class ElectionTests(ExtraTestCase):
    fixtures = ('test-auth', 'test-teams', 'test-elections')
    credentials = dict(username='v1', password=True)

    # XXX Change election to invitation mode, email send out to voting team

    def test_01_election_workflow(self):
        response = self.assertGet('elections:item', team='e_team', slug='test-election-2011')
        self.assertContains(response, 'Election for King (2011)')
        self.assertContains(response, 'Planning')

        election = Election.objects.get(slug='test-election-2011')

        election.invitation_open()
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, 'Election King: Nominations')
        
        response = self.assertGet('elections:invite', team='e_team', slug='test-election-2011', user_id=1)
        self.assertContains(response, 'Your Invitation sent to')
        self.assertEqual(len(mail.outbox), 2)
        self.assertEqual(mail.outbox[1].subject, 'Stand for Election: test-election-2011')
        election._candidates.create(user_id=42, invitor_id=45)
        election._candidates.create(user_id=43, invitor_id=44)
        election._candidates.create(user_id=44, invitor_id=43)
        election._candidates.create(user_id=45, invitor_id=42)

        cs = election._candidates.order_by('id').values_list('slug', flat=True)
        response = self.assertGet('elections:accept-yes', team='e_team', slug='test-election-2011', hash=cs[0])
        self.assertContains(response, 'Invitation Accepted')
        self.assertEqual(election.candidates.count(), 1)

        # Check Invitations lists
        self.assertContains(response, 'Testing Admin')

        # Change election to invitations sent
        election.invitation_close()

        response = self.assertGet('elections:accept-yes', team='e_team', slug='test-election-2011', hash=cs[1])
        self.assertEqual(election.candidates.count(), 2)

        response = self.assertGet('elections:accept-yes', team='e_team', slug='test-election-2011', hash=cs[2])
        self.assertEqual(election.candidates.count(), 3)

        # Reject invitation
        response = self.assertGet('elections:accept-no', team='e_team', slug='test-election-2011', hash=cs[3])
        self.assertContains(response, 'Invitation NOT Accepted')
        self.assertEqual(election.candidates.count(), 3)

        # No ballots yet created
        self.assertEqual(election.ballots.count(), 0)

        # Change election to voting mode, email to voting team is sent
        election.voting_open()
        self.assertEqual(len(mail.outbox), 3)
        self.assertEqual(mail.outbox[-1].subject, 'Election King: Voting Open')

        # Ballots now exist
        self.assertEqual(election.ballots.count(), 5)
        for ballot in election.ballots.all():
            votes = dict([('vote_%d' % c.id, x+1) for x, c in enumerate(election.candidates)])
            response = self.assertPost('elections:vote', team='e_team',
                slug='test-election-2011', hash=ballot.slug, data=votes)
            self.assertContains(response, 'ballot has been saved')

        # Change election to finish mode, email to voting team is sent with results
        election.voting_close()
        self.assertEqual(len(mail.outbox), 4)
        self.assertEqual(mail.outbox[-1].subject, 'Election King: Results')

        log = election.get_log
        # Log contains an election type meta documentation
        self.assertIn('type', log)

        # All the counts for various things
        self.assertEqual(log['counts']['ignored'], 1)
        self.assertEqual(log['counts']['voters'], 5)
        self.assertEqual(log['counts']['rejected'], 1)
        self.assertEqual(log['counts']['candidates'], 3)
        self.assertEqual(log['counts']['ballots'], 5)
        self.assertEqual(log['counts']['invites'], 5)

        # The actual votes
        self.assertEqual(len(log['votes']), 5)
        self.assertEqual(set(log['votes'][0]['paper']), set([1, 42, 43]))
        self.assertEqual(log['votes'][0]['user_id'], 45)

        # Candidate objects
        self.assertTrue(isinstance(log['candidates'][0], User))

        # Election Results
        self.assertEqual(log['results']['winners'], [1])
        self.assertEqual(len(log['results']['rounds']), 1)
        # Votes and candidate lists are cleared
        self.assertEqual(election._candidates.count(), 0)
        self.assertEqual(election.ballots.count(), 0)



