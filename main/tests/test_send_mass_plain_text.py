'''
test send mass plain text email
'''
from datetime import datetime, timedelta

import json
import logging

from django.test import TestCase
from django.contrib.auth.models import User

from main.globals import send_mass_email_from_template

from django.core import mail

class TestAutoPay(TestCase):
    '''
    test send mass plain text email
    '''
    fixtures = ['users.json']

    message_template = '''
                       *** TEST MESSAGE *** 
                       [name],
                       You are invited to an experiment on [date].
                       Log into you account and confirm.
                       Thanks,
                       ESI
                       '''

    message_template_2 = "test"
    
    message_subject = '*** TEST MESSAGE ***'

    user = None

    def setUp(self):
        logger = logging.getLogger(__name__)

        self.user = User.objects.get(id = 1)

    def test_mass_email_plain_text(self):
        '''
        test mass email
        '''
        logger = logging.getLogger(__name__)

        user_list=[]
        user_list.append({'email' : 'abc@123.edu',
                          'variables':[{'name':'name','text':'sam'}, {'name':'date','text':'1/11/11 3:30pm Pacific'}]})

        memo = 'just testing'

        result = send_mass_email_from_template(self.user, user_list, self.message_subject, self.message_template_2,memo, True)

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(result["code"], 201)

        #test send 12 emails
        mail.outbox=[]
        user_list2=[]
        
        for user in range(12):
            user_list2.append({'email' : 'abc@123.edu',
                               'variables':[{'name':'name','text':'sam'}, {'name':'date','text':'1/11/11 3:30pm Pacific'}]})

        result = send_mass_email_from_template(self.user, user_list2, self.message_subject, self.message_template_2,memo, True)

        self.assertEqual(len(mail.outbox), 12)
        self.assertEqual(result["code"], 201)

        #test malformed email
        mail.outbox=[]
        user_list3=[]

        user_list3.append({'email' : 'abc@123.edu',
                           'variable':[{'name':'name','text':'sam'}, {'name':'date','text':'1/11/11 3:30pm Pacific'}]})
        
        result = send_mass_email_from_template(self.user, user_list3, self.message_subject, self.message_template_2,memo, True)

        self.assertEqual(result["code"], 400)
        self.assertEqual(len(mail.outbox), 0)







        
        