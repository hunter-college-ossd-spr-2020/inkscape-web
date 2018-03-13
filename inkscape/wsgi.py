"""
WSGI config for c project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.7/howto/deployment/wsgi/
"""

import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "inkscape.settings")

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

# Only load Dozer if it's available.
try:
    from dozer import Dozer
    application = Dozer(application)
except ImportError:
    pass
