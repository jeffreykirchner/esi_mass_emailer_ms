'''
send email view
'''
from datetime import datetime

import logging
import time

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework import permissions

from django.conf import settings

#from main.globals import send_mass_email_from_template
from main.globals import send_mass_email_message_from_template
from main.globals import send_mass_email_message_from_template_sendgrid
from main.globals import MailSystem

import main

class SendEmailView(APIView):
    '''
    take a mass email for sending
    '''
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        '''
        handle incoming send mass email
        '''
        logger = logging.getLogger(__name__)
        logger.info(f'SendEmailView: data: {request.data}')

        result = take_and_send_incoming_email(request.user, request.data, settings.DEBUG)

        return Response(result['text'], status=result['code'])

def take_and_send_incoming_email(user, data, use_test_subject):
    '''
    take incoming email and send it, send emails in groups of block size to limit overloading
    '''

    p = main.models.Parameters.objects.first()

    if p.mail_system == MailSystem.EXCHANGE:
        email_block = 250
        sleep_length = 61
    elif p.mail_system == MailSystem.SEND_GRID:
        email_block = 1000
        sleep_length = 1
    else:
        return {'text' : {"mail_count" : 0, "error_message" : "Invalid mail system."},
                'code' : status.HTTP_400_BAD_REQUEST}
    
    result_list = []
    email_counter = 0
    user_list = []    

    for u in data["user_list"]:

        email_counter += 1
        user_list.append(u)

        #if email counter hits block size, send emails then pause for cool down
        if email_counter == email_block:
            
            time_start = datetime.now()      
        
            if p.mail_system == MailSystem.EXCHANGE:
                result_list.append(send_mass_email_message_from_template(user,
                                                    user_list,
                                                    data["message_subject"],
                                                    data["message_text"],
                                                    data.get("message_text_html", None),
                                                    data["memo"],
                                                    use_test_subject))
                
                time.sleep(max(sleep_length-time_span.total_seconds(), 1))

            elif p.mail_system == MailSystem.SEND_GRID:
                result_list.append(send_mass_email_message_from_template_sendgrid(user,
                                                    user_list,
                                                    data["message_subject"],
                                                    data["message_text"],
                                                    data.get("message_text_html", None),
                                                    data["memo"],
                                                    use_test_subject))


            time_end = datetime.now()
            time_span = time_end-time_start

            email_counter = 0
            user_list = []
            
    #send remaining partial email block
    if len(user_list) > 0:
        if p.mail_system == MailSystem.EXCHANGE:
            result_list.append(send_mass_email_message_from_template(user,
                                                            user_list,
                                                            data["message_subject"],
                                                            data["message_text"],
                                                            data.get("message_text_html", None),
                                                            data["memo"],
                                                            use_test_subject))
        elif p.mail_system == MailSystem.SEND_GRID:
            result_list.append(send_mass_email_message_from_template_sendgrid(user,
                                                    user_list,
                                                    data["message_subject"],
                                                    data["message_text"],
                                                    data.get("message_text_html", None),
                                                    data["memo"],
                                                    use_test_subject))

    mail_count = 0
    mail_code = status.HTTP_201_CREATED
    error_message = ""

    for r in result_list:
        mail_count += r["text"]["mail_count"]

        if r["text"]["error_message"] != "":
            error_message += r["text"]["error_message"] + " "
        
        if r["code"] == status.HTTP_400_BAD_REQUEST:
            mail_code = status.HTTP_400_BAD_REQUEST
        
    return {'text' : {"mail_count" : mail_count, "error_message" : error_message},
            'code' : mail_code}