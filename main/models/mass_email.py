'''
mass email model
'''

from django.db import models
from django.contrib.auth.models import User

def default_email_result():
    return {"mail_count":0, "error_message":""}

class MassEmail(models.Model):
    '''
    mass email model
    '''

    app = models.ForeignKey(User, on_delete=models.CASCADE, related_name="app_name")

    message_subject = models.CharField(max_length = 300, default="Message Subject", verbose_name="Message Subject")    #message subject
    message_text = models.CharField(max_length = 100000, default="Message Text", verbose_name="Message Text")           #message text
    user_list = models.JSONField(verbose_name="User List")                                                             #list of users and template variables
    email_result = models.JSONField(verbose_name="Email Result", default = default_email_result)                       #number of emials successfully sent
    memo = models.CharField(max_length = 300, default="", verbose_name="Memo")                                         #note about message's purpose

    timestamp = models.DateTimeField(auto_now_add= True)
    updated= models.DateTimeField(auto_now= True)

    def __str__(self):
        return f"{self.message_subject}"

    class Meta:
        verbose_name = 'Mass Email'
        verbose_name_plural = 'Mass Emails'

