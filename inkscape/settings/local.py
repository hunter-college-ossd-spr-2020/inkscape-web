"""
Local settings (generated)
"""

from .base import * #pylint: disable=wildcard-import,unused-wildcard-import

IS_TEST = len(sys.argv) > 1 and sys.argv[1] in ('test',)

CODE_PATH = os.path.dirname(os.path.abspath(__file__))
PROJECT_PATH = os.path.abspath(os.path.join(CODE_PATH, ".."))

SITE_ADDRESS = 'localhost:8000'
SITE_NAME = 'inkscape-website-dev'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'inkscape2',
        'USER': 'inkscape',
        'PASSWORD': 'sdjusd848983',
        'HOST': 'localhost',
        'PORT': '',
    },
}

ENABLE_CACHING = False
CACHE_MIDDLEWARE_SECONDS = 120
CMS_CACHE_DURATIONS = {
    'content': 120,
    'menus': 3600, # One hour
    'permissions': 3600,
}
CACHES = {
    'default': {
        'TIMEOUT': 3600, # One hour
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'prefix1',
        #'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
        #'LOCATION': '127.0.0.1:11211',
    }
}

FASTLY_CACHE_API_KEY = '11db9b71d6bd4571b84d068b64441fff'
FASTLY_CACHE_SERVICE = '5iJRk5f4O40zatkoP4Dlqj'
#MEDIA_URL = 'https://media.inkscape.org/media/'
#STATIC_URL = 'https://media.inkscape.org/static/'

# This IRC setting is auto eaten by easyirc, so it's kinda sad
# the name is so generic. Oh well.
CONNECTIONS = [
    {
        'name': 'freenode',
        'host': 'irc.freenode.net',
        'port': 6667,
        'nick': 'doctormo_bot',
        'autojoins': [],
        'enabled': True,
        'autoreconnect': False,
    }
]

GOOGLE_ANID = 'UA-XXXXXX-X'

SECRET_KEY = 'iccj=*n_h03lm!)53e^ze&qudzcyoc+qi8s=$+fj6khix-w&*e'
YOUTUBE_API_KEY = 'AIzaSyBQmkHHLiNtuLf4Pgz1y0ENDcayNukpQBE'

ALLOWED_HOSTS = ['*', 'inkscape.org', 'localhost:8000']
DEBUG = True
ENABLE_DEBUG_TOOLBAR = True and DEBUG and not IS_TEST
ENABLE_DESIGN_TOOLBAR = ENABLE_DEBUG_TOOLBAR
ENABLE_PROFILER_TOOLBAR = True


# Auth Settings
#
# Localhost ReCapture Keys, sign up for live keys:
#   http://recaptcha.net/
#
NORECAPTCHA_SITE_KEY = '6Ldd6OsSAAAAAOOu3QVFc2_pBazt7H8Fuks7hBC3'
NORECAPTCHA_SECRET_KEY = '6Ldd6OsSAAAAANDyM9FbuAne2b2NKHkkpMWP3wIY'

# Localhost registration for oauth ONLY (not for use live)
SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = '112239585184-nuu42abso85v2f5t2nqstt1s'\
                                'tmkqa6u6.apps.googleusercontent.com'
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = 'eUHvEyHNfXJWOnbM_H26ZA9W'

MAILING_LIST_DIR = os.path.join(PROJECT_PATH, 'data', 'static', 'mailinglists')
GOOGLE_DEVELOPER_KEY = 'NOPE'

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    'socialauth.auth_backends.OpenIdBackend',
    'socialauth.auth_backends.TwitterBackend',
    'socialauth.auth_backends.FacebookBackend',
    'socialauth.auth_backends.LinkedInBackend',
)

# Server Email settings
SERVER_EMAIL = 'admin@%s' % SITE_ADDRESS
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
EMAIL_SUBJECT_PREFIX = '[%s] ' % SITE_NAME

EMAIL_HOST = 'smtp.gmail.com'
EMAIL_HOST_USER = 'noone@gmail.com'
EMAIL_HOST_PASSWORD = 'Nothing'
EMAIL_PORT = 587
EMAIL_USE_TLS = True

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
        }
    },
    'loggers': {
        'django.db.backends': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
    }
}
