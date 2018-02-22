
import os

ENABLE_CACHING = True
ENABLE_DEBUG_TOOLBAR = False
CODE_PATH = os.path.dirname(os.path.abspath(__file__))
PROJECT_PATH = os.path.abspath(os.path.join(CODE_PATH, ".."))

SITE_ADDRESS = 'www.inkscape.org'
SITE_NAME = 'inkscape-website-www'
 
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': '{{DBNAME}}',
        'USER': '{{USER}}',
        'PASSWORD': '{{PWD}}',
        'HOST': '{{IP}}',
        'POST': '',
    },
}

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
        'LOCATION': '{{IP}}:11211',
        'TIMEOUT': 3600, # One hour
    }
}

# >= haystack 2.0
HAYSTACK_CONNECTIONS = {
    'default': {
        'ENGINE': 'haystack.backends.whoosh_backend.WhooshEngine',
        'PATH': "%s/data/woosh_search" % PROJECT_PATH,
    },
}

# Fastly caching service
MEDIA_URL = 'https://media.inkscape.org/media/'
STATIC_URL = 'https://media.inkscape.org/static/'
FASTLY_CACHE_API_KEY = '{{API_KEY}}'
FASTLY_CACHE_SERVICE = '{{API_SEC}}'

SESSION_COOKIE_AGE = 1209600
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

SECRET_KEY = '{{RAND}}'
RECAPTCHA_PUBLIC_KEY = '{{API_KEY}}'
RECAPTCHA_PRIVATE_KEY = '{{API_SEC}}'

ALLOWED_HOSTS = ['inkscape.org','inkscape.org.','www.inkscape.org','www.inkscape.org.', 'test.inkscape.org', 'media.inkscape.org']
DEBUG = False

# This IRC setting is auto eaten by easyirc, so it's kinda sad
# the name is so generic. Oh well.
CONNECTIONS = [ 
    {   
        'name': 'freenode',
        'host': 'irc.freenode.net',
        'port': 6667,
        'nick': 'inkscape_bot',
        'autojoins': [],
        'enabled': True,
        'autoreconnect': False,
    }   
]


# Auth Settings

OPENID_REDIRECT_NEXT = '/accounts/openid/done/'

OPENID_SREG = {"requred": "nickname, email, fullname",
               "optional":"postcode, country",
               "policy_url": ""}

OPENID_AX = [{"type_uri": "http://axschema.org/contact/email",
              "count": 1,
              "required": True,
              "alias": "email"},
             {"type_uri": "http://axschema.org/schema/fullname",
              "count":1 ,
              "required": False,
              "alias": "fname"}]

OPENID_AX_PROVIDER_MAP = {'Google': {'email': 'http://axschema.org/contact/email',
                                     'firstname': 'http://axschema.org/namePerson/first',
                                     'lastname': 'http://axschema.org/namePerson/last'},
                          'Default': {'email': 'http://axschema.org/contact/email',
                                      'fullname': 'http://axschema.org/namePerson',
                                      'nickname': 'http://axschema.org/namePerson/friendly'}
                          }

SOCIAL_AUTH_TWITTER_KEY = '{{API_KEY}}'
SOCIAL_AUTH_TWITTER_SECRET = '{{API_SEC}}'

SOCIAL_AUTH_FACEBOOK_KEY = '{{API_KEY}}'
SOCIAL_AUTH_FACEBOOK_SECRET = '{{API_SEC}}'

SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = '{{API_KEY}}'
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET  = '{{API_SEC}}'

# Server Email settings

DEFAULT_FROM_EMAIL   = 'webmaster@inkscape.org'
SERVER_EMAIL         = 'webmaster@inkscape.org'
EMAIL_USE_TLS        = False
EMAIL_HOST           = '{{IP}}'
EMAIL_PORT           = 25

EMAIL_HOST_USER      = ''
EMAIL_HOST_PASSWORD  = ''
EMAIL_SUBJECT_PREFIX = '[InkscapeWeb] '


