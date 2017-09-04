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

def make_log(**items):
    """
    This should be replaced by a json Decoder/Encoder pair.
    """
    res = items['results']
    res['winners'] = list(res['winners'])
    res['candidates'] = list(res['candidates'])
    for round_ in res['rounds']:
        round_['winners'] = list(round_['winners'])
    return json.dumps(items)

def get_log(log):
    User = get_user_model()
    items = json.loads(log)
    res = items['results']
    cands = []
    for pk in res['candidates']:
        try:
	    user = User.objects.get(pk=pk)
        except User.DoesNotExist:
            # XXX Reconstruct user from details in log
            user = User(username='anon_%d' % pk)
            
	user.winner = pk in res['winners']
        cands.append(user)
    items['candidates'] = sorted(cands, key=lambda x: not x.winner)
    return items


