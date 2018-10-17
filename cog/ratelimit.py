#
# PD - https://djangosnippets.org/snippets/2242/
#
"""
Limit the rate emails are sent to admins about errors
"""

import traceback
from hashlib import md5
from datetime import datetime, timedelta

from django.conf import settings
from django.core.cache import cache

class RateLimitFilter(object): # pylint: disable=too-few-public-methods
    """Limit the number of errors before skipping messages"""
    _errors = {}

    def filter(self, record):
        """Filter the given record"""
        trace = '\n'.join(traceback.format_exception(*record.exc_info))

        # Track duplicate errors
        duplicate = False
        rate = getattr(settings, 'ERROR_RATE_LIMIT', 10)  # seconds
        if rate > 0:
            key = md5(trace.encode('utf-8')).hexdigest()
            prefix = getattr(settings, 'ERROR_RATE_CACHE_PREFIX', 'ERROR_RATE')

            # Test if the cache works
            cache_key = '%s_%s' % (prefix, key)
            try:
                cache.set(prefix, 1, 1)
                use_cache = cache.get(prefix) == 1
            except KeyError:
                use_cache = False

            if use_cache:
                duplicate = cache.get(cache_key) == 1
                cache.set(cache_key, 1, rate)
            else:
                min_date = datetime.now() - timedelta(seconds=rate)
                max_keys = getattr(settings, 'ERROR_RATE_KEY_LIMIT', 100)
                duplicate = (key in self._errors and self._errors[key] >= min_date)
                self._errors = dict(filter(lambda x: x[1] >= min_date,
                                           sorted(self._errors.items(),
                                                  key=lambda x: x[1]))[0-max_keys:])
                if not duplicate:
                    self._errors[key] = datetime.now()

        return not duplicate
