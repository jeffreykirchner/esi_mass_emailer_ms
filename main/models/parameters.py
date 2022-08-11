'''
site wide parameters
'''
#import logging
#import traceback

from django.db import models

from main.globals import MailSystem

#gloabal parameters for site
class Parameters(models.Model):
    '''
    site wide parameters
    '''
    contact_email =  models.CharField(max_length = 1000, default = "JohnSmith@abc.edu")      #contact email 
    site_URL = models.CharField(max_length = 200, default = "https://www.google.com/")         #site URL used for display in emails
    mail_system = models.CharField(max_length=100, choices=MailSystem.choices, verbose_name='Mail System')

    timestamp = models.DateTimeField(auto_now_add= True)
    updated= models.DateTimeField(auto_now= True)

    def __str__(self):
        return f"Site Parameters {self.contact_email}"

    class Meta:
        verbose_name = 'Site Parameters'
        verbose_name_plural = 'Site Parameters'