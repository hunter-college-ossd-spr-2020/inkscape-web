#
# Copyright 2015, Martin Owens <doctormo@gmail.com>
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
Test team functions
"""
from autotest.base import ExtraTestCase

from ..models import Team, Group, User

URL_TO_LIST = {
  'join': 'members',
  'leave': 'old_members',
  'watch': 'watchers',
  'unwatch': 'old_watchers',
  'remove': 'old_members',
  'approve': 'members',
  'disapprove': 'old_requests',
  '': 'requests',
}
MSG = {
  'not-allowed': 'add user to team. (not allowed)',
  'no-watch': 't watch this team',
  'not-removed': 'Cannot remove user from team. (not allowed)',
}
ERR = [
  "User %s NOT found in list:%s when expected",
  "User %s found in list:%s, but expected it to be missing",
]

class TeamBase(object):
    fixtures = ('test-auth', 'test-teams')

    def assertAction(self, team_id, url, msg=None, _not=False, **kw):
        try:
            team = Team.objects.get(slug=team_id)
            user = User.objects.get(username=kw['username']) \
                if 'username' in kw else self.user
        except User.DoesNotExist:
            self.assertFalse(True, "User '%s' doesn't exist" % kw['username'])

        list_name = kw.pop('list_name', URL_TO_LIST[url])
        #self._debug(team, url, user=user.pk, **kw)
        response = self.assertGet('team.'+url, team=team_id, status=302, **kw)
        #self._debug(team, url, user=user.pk, **kw)

        lst = getattr(team, list_name)
        # Make sure the action caused (or did not cause) a change in the
        # list of members for the related list. i.e. join changed members
        err = ERR[_not] % (user.pk, self._user_list(url, lst))
        self.assertEqual(lst.filter(user=user).count(), int(not _not), err)

        # When changing 'members' the permission group should change too.
        if list_name.endswith('members'):
            # When it's an old member, or the action failed
            if list_name.startswith('old') is _not:
                self.assertIn(user, team.group.user_set.all())
            else:
                self.assertNotIn(user, team.group.user_set.all())

        if msg is not None:
            self.assertMessage(response, MSG.get(msg, msg))

    def assertNotAction(self, team, url, msg=None, **kw):
        return self.assertAction(team, url, msg=msg, _not=True, **kw)

    def _debug(self, team, url, **kw):
        print " -= DEBUG (%s:%s) =-" % (url, str(kw))
        for name in set(URL_TO_LIST.values()):
            print self._user_list(name, getattr(team, name))
        print ""

    def _user_list(self, name, lst):
        return "%s: %s" % (name, ", ".join([str(pk)
            for pk in lst.values_list('user_id', flat=True)]))


class TeamTests(TeamBase, ExtraTestCase):
    credentials = dict(username='tester', password=True)

    def test_01_team_details(self):
        response = self.assertGet('team', team='c_team')
        self.assertContains(response, 'England')

    def test_02_secret_not_visible(self):
        """Secret teams are not visisble on the page"""
        response = self.assertGet('teams')
        self.assertNotContains(response, 'Atlantis')
        response = self.assertGet('team', team='s_team', status=404)

    def test_03_watch_secret_team(self):
        """Fail to watch a secret team"""
        self.assertNotAction('s_team', 'watch', msg='no-watch')

    def test_04_join_closed_team_user(self):
        """Fail to join a closed team"""
        self.assertNotAction('c_team', 'join', msg='not-allowed')

    def test_05_add_request_to_join(self):
        """Successfully request to join a team"""
        self.assertAction('t_team', 'join', 'Membership Request Received', list_name='requests')
        self.assertAction('t_team', 'join', 'already requested', list_name='requests')
        # XXX Is visible on page too
        self.assertAction('t_team', 'leave', 'User removed from membership requests', list_name='old_requests')

    def test_06_join_open_team(self):
        """Any user can join an open team"""
        self.assertAction('o_team', 'join', msg='sucessfully add')

    def test_07_watch_team(self):
        """A user can watch an open team"""
        self.assertAction('o_team', 'watch', msg='Now watching')

    def test_08_no_removal_by_user(self):
        """Random other user can not remove from team"""
        self.assertNotAction('o_team', 'remove', msg='not-removed', username='team_peer')


class TeamAdminTests(TeamBase, ExtraTestCase):
    credentials = dict(username='team_admin', password=True)

    def test_01_add_closed_team_admin(self):
        """Fail to add another user to a closed team"""
        self.assertNotAction('c_team', 'approve', msg='not-allowed', username='team_requester')

    def test_02_add_user_by_admin(self):
        """Successfully add requested users to team by admin"""
        self.assertAction('t_team', 'approve', msg='sucessfully add', username='team_requester')

    def test_03_remove_from_team_by_admin(self):
        """User removed by admin from team"""
        self.assertAction('t_team', 'remove', msg='User removed from team', username='team_peer')
        self.assertAction('t_team', 'remove', msg='User removed from membership', username='team_requester', list_name='old_requests')


class TeamPeerTests(TeamBase, ExtraTestCase):
    credentials = dict(username='team_peer', password=True)

    def test_01_add_user_by_peer(self):
        """Fail to approve a user by a peer"""
        self.assertNotAction('t_team', 'approve', msg='not allowed', username='team_requester')

    def test_02_add_user_by_peer(self):
        """Successfully add requested users to team by peer"""
        self.assertAction('p_team', 'approve', msg='sucessfully add', username='team_requester')
        # Fail to add user not requested
        self.assertNotAction('p_team', 'approve', msg='This user has not requested', username='tester')
        self.assertNotAction('p_team', 'approve', msg='This user has not requested', username='team_watcher')

    def test_03_join_open_team(self):
        """Fail to rejoin open team when already a member"""
        self.assertAction('o_team', 'join', msg='You are already')

    def test_04_no_removal_by_peer(self):
        """Peer can not remove user from team"""
        self.assertAction('o_team', 'approve', username="team_requester")
        self.assertNotAction('o_team', 'remove', msg="Cannot remove user from team", username="team_requester")

    def test_05_remove_from_team_by_user(self):
        """User removes themselves from team"""
        self.assertAction('o_team', 'leave', msg='User removed from team')

    def test_06_join_closed_team_peer(self):
        """Fail to join a closed team as a peer"""
        self.assertNotAction('c_team', 'approve',
            msg='Can\'t add user to team', username='team_requester')


class TeamWatcherTests(TeamBase, ExtraTestCase):
    credentials = dict(username='team_watcher', password=True)

    def test_01_join_open_team(self):
        """Any user can join an open team"""
        self.assertAction('o_team', 'join', msg='sucessfully add')

    def test_02_watch_then_join_team(self):
        """Watch and then join a team"""
        self.assertAction('o_team', 'join', msg='sucessfully add')

    def test_03_watch_unwatch(self):
        """Watch and then unwatch a team"""
        self.assertAction('o_team', 'unwatch', msg='No longer watching')


class TeamRequesterTests(TeamBase, ExtraTestCase):
    credentials = dict(username='team_requester', password=True)

    def test_01_remove_from_team_by_requester(self):
        """User removes themselves from requests list"""
        self.assertAction('o_team', 'leave', msg='User removed from membership', list_name="old_requests")

