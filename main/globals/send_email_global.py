
from smtplib import SMTPException
from rest_framework import status

import logging
import random

from django.conf import settings
from django.core.mail import send_mass_mail
from django.template.loader import render_to_string
from django.utils.crypto import get_random_string
from django.utils.html import strip_tags
from django.core.mail import send_mail

from main.models import Parameters, MassEmail

def send_mass_email_from_template(user, user_list, subject, message, memo, use_test_account):
    '''
    send mass email to user list filling in variables
        user_list : {email:email, variables:[{name:text},{name:text}] }
        subject : string subject line of email
        message : string message template to be sent
        memo : string about message's purpose
        use_test_accout : send all email to test accout
    '''
    logger = logging.getLogger(__name__)
    logger.info("Send mass email to list")

    parameters = Parameters.objects.first()

    message_list = []
    message_list.append(())
    from_email = get_from_email()   
    test_account_email = settings.EMAIL_TEST_ACCOUNT       #email address sent to during debug

    mass_email = MassEmail()
    mass_email.app = user
    mass_email.message_subject = subject
    mass_email.message_text = message
    mass_email.user_list = user_list
    mass_email.memo = memo

    mass_email.save()

    logger.info(f'{settings.DEBUG} {test_account_email}')

    block_count = 0   #number of message blocks
    cnt = 0           #message counter within block 

    try:
        for user in user_list:

            if cnt == 100:
                cnt = 0
                block_count += 1
                message_list.append(())

            #fill in variables
            new_message = message

            for variable in user["variables"]:
                new_message = new_message.replace(f'[{variable["name"]}]', variable["text"])

            #fill in subject parameters
            if use_test_account:
                message_list[block_count] += ((subject, new_message, from_email, [test_account_email]),)   #use for test emails
            else:
                message_list[block_count] += ((subject, new_message, from_email, [user["email"]]),)  

            cnt += 1

    except KeyError as key_error:
        logger.warning(f"send_mass_email_from_template: {key_error} was not found in {user}")
        return {'text' : {"mail_count" : 0, "error_message" : f'{key_error} was not found in {user}'},
                'code' : status.HTTP_400_BAD_REQUEST}
    
    mass_email.email_result = send_mass_email(block_count, message_list)
    mass_email.save()

    if mass_email.email_result["error_message"] == "":
        return {'text' : mass_email.email_result, 'code' : status.HTTP_201_CREATED}
    else:
        return {'text' : mass_email.email_result, 'code' : status.HTTP_400_BAD_REQUEST}

#return the from address
def get_from_email():    
    return f'"{settings.EMAIL_HOST_USER_NAME}" <{settings.EMAIL_HOST_USER }>'

#send mass email to list,takes a list
def send_mass_email(block_count, message_list):
    logger = logging.getLogger(__name__)
    logger.info("Send mass email to list")

    logger.info(message_list)

    error_message = ""
    mail_count=0
    if len(message_list)>0 :
        try:
            for x in range(block_count+1):            
                logger.info("Sending Block " + str(x+1) + " of " + str(block_count+1))
                mail_count += send_mass_mail(message_list[x], fail_silently=False) 
        except SMTPException as e:
            logger.info('There was an error sending email: ' + str(e)) 
            error_message = str(e)
    else:
        error_message = "Message list empty, no emails sent."

    return {"mail_count" : mail_count, "error_message" : error_message}