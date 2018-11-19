from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class BasicMenuConfig(AppConfig):
    name = 'basic menu'
    verbose_name = _("basic menu system")
