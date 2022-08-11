from django.db import models
from django.utils.translation import gettext_lazy as _

class MailSystem(models.TextChoices):
    EXCHANGE = 'Exchange', _('Exchange')
    SEND_GRID = 'SendGrid', _('SendGrid')