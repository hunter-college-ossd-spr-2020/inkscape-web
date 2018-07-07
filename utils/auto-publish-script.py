#
# This script was used to update resources to published and email all users effected.
#
"""Use once script"""

import time
from datetime import timedelta

from django.utils.timezone import now

from resources.models import Resource

resources = Resource.objects.filter(created__lt=now()-timedelta(days=14), published=False).exclude(download='')

for user in set([res.user for res in resources]):
    rec = resources.filter(user_id=user.pk)
    items = "\n".join([" * {0} ({0.created}) https://inkscape.org{1}".format(
        record, record.get_absolute_url()[3:]) for record in rec])
    msg = """

Dear {},

The website has upgraded it's publishing user interface to make it more obvious when uploads are published. There are quite a few older uploads which are not published after a long time. So we're automatically setting uploads to published if they were uploaded more than two weeks ago. Please see the list below of items from your gallery that have been effected:

{}

""".format(user, items)
    rec.update(published=True)
    try:
        user.email_user("Uploads Automatically Published", msg, from_email="webmaster@inkscape.org")
    except KeyError:
        print("Error sending email.")
    print(user)
    time.sleep(0.5)
