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
Calculate the results of an election easily.
"""

# bc = [
#  {'count': 1.0, 'ballot': ['1', '2', '3', '4']},
#  {'count': 1.0, 'ballot': ['1', '4', '2', '3']},
#  {'count': 1.0, 'ballot': ['4', '2', '1', '3']},
#  {'count': 1.0, 'ballot': ['4', '1', '3', '2']},
#  {'count': 1.0, 'ballot': ['3', '1', '4', '2']},
#  {'count': 1.0, 'ballot': ['1']},
#  {'count': 1.0, 'ballot': ['1', '2', '4', '3']},
#  {'count': 2.0, 'ballot': ['3', '4', '1', '2']},
#  {'count': 2.0, 'ballot': ['4', '2', '3', '1']},
#  {'count': 1.0, 'ballot': ['1', '3']}]
# IRV(bc).as_dict()['rounds']
# [{'tallies': {'1': 5.0, '3': 3.0, '4': 4.0}, 'loser': '3'},
#  {'tallies': {'1': 6.0, '4': 6.0}, 'tied_losers': set(['1', '4']),
#  'loser': '4'}, {'tallies': {'1': 9.0, '2': 3.0}, 'winner': '1'}]

import json
from django.contrib.auth import get_user_model
from django.utils.translation import ugettext_lazy as _

# This part can be expanded in the future if we ever need different voting
BALLOT_TYPES = {
  'pyvotecore.stv': {
    'system': {
      'name': _("Single Transferable Vote"),
      'link': 'http://en.wikipedia.org/wiki/Single_transferable_vote',
      'icon': 'images/vote/stv.svg',
    },
    'library': {
      'name': 'pyvotecore',
      'link': 'https://github.com/bradbeattie/python-vote-core',
      'module': 'stv',
    },
  },
  'conservancy.stv': {
    'system': {
      'name': _("Single Transferable Vote"),
      'link': 'http://en.wikipedia.org/wiki/Single_transferable_vote',
      'icon': 'images/vote/old.svg',
    },
    'library': {
      'name': 'conservancy',
      'link': 'https://github.com/conservancy/voting',
      'module': 'voting',
    },
  },
  'old.stv': {
    'system': {
      'name': _("Single Transferable Vote"),
      'link': 'http://en.wikipedia.org/wiki/Single_transferable_vote',
      'icon': 'images/vote/old.svg',
    },
  },
}

class LogEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, set):
            return list(obj)
        return json.JSONEncoder.default(self, obj)

def make_log(**items):
    return json.dumps(items, cls=LogEncoder, sort_keys=True, indent=4)

def get_log(log):
    User = get_user_model()
    items = json.loads(log)
    user_log = dict([(v['user_id'], v) for v in items['votes']])
    user_log.update([(v['user_id'], v) for v in items['candidates']])
    res = items['results']

    # Build a list of candidate user objects
    candidates = {}
    for pk in res['candidates']:
        try:
            details = user_log[int(pk)]
            user = User.objects.get(pk=pk)
        except User.DoesNotExist:
            # Reconstruct user from details in log
            user = User(
              username=details['username'],
              first_name=details['first_name'],
              last_name=details['last_name'],
              email=details['email'],
            )
        except KeyError:
            user = None
            
        if user is not None:
            user.winner = pk in res['winners']
            candidates[pk] = user

    for r in res['rounds']:
        tals = []
        for user_id, score in r['tallies'].items():
            user_id = int(user_id)
            tals.append({
              'user': candidates.get(user_id, None),
              'score': score,
              'winner': user_id in r.get('winners', []),
              'loser': user_id in r.get('tied_losers', []) \
                    or user_id == r.get('loser', '')
            })
        r['tallies'] = tals

    items['type'] = BALLOT_TYPES[items['type']]
    items['candidates'] = sorted(candidates.values(), key=lambda x: not x.winner)
    return items


