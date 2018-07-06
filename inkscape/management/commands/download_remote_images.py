#
# Copyright 2018, Martin Owens <doctormo@gmail.com>
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
Downloads remote images in a given model's field and replaces the URL links.
"""
from bs4 import BeautifulSoup as Soup
from django.core.management import BaseCommand
from inkscape.models import RemoteImage

class Command(BaseCommand):
    """Command to check http image links and reset them"""
    help = __doc__

    def handle(self, *args, **options):
        """Handle downloading images"""
        # Future: We're making this fixed for now, there areways to make callers
        # pass which models and fields we should fix, but for now, we're
        # nailing these models and fields here.

        from releases.models import Release
        for release in Release.objects.all():
            print("Release: {}".format(release))
            release.release_notes = self.require_https(release.release_notes)
            release.save()

    def require_https(self, html):
        """
        Scans the given html for http images and downloads them locally
        redirecting the links to the new https local version.

        Returns: html with replaced links
        """
        html = Soup(html, 'html.parser')
        for img in html.find_all('img'):
            if 'src' in img.attrs:
                img['src'] = self.src(img['src'])
            if 'srcset'in img.attrs:
                img['srcset'] = ", ".join(self.srcset(*img['srcset'].split(',')))
        return html.prettify()

    @staticmethod
    def src(link):
        """Attempts to get the http link and downloads it locally"""
        if not link.startswith('http:'):
            return link
        print(" < Downloading: {}".format(link))
        obj, created = RemoteImage.objects.get_or_create(remote_url=link)
        print(" > {}: {}".format(['Existing', 'Downloaded'][created], obj.local_file.name))
        return obj.get_absolute_url()

    def srcset(self, *pairs):
        """Take the odd formatted srcset attribute and parse out src links"""
        for pair in pairs:
            try:
                (link, zoom) = pair.strip().rsplit(' ', 1)
                yield "{} {}".format(self.src(link), zoom)
            except IOError:
                yield pair
