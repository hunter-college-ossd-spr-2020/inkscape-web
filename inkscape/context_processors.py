
from django.conf import settings

def design(request):
    """
    Adds static-related context variables to the context.
    """
    return {
        'MEDIA_URL': settings.MEDIA_URL,
        'DEBUG': settings.DEBUG,
        'REVISION': settings.REVISION,
        'GOOGLE_ANID': settings.GOOGLE_ANID,
    }
