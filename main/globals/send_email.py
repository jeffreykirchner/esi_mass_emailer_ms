
from smtplib import SMTPException

import logging
import random

from django.conf import settings
from django.core.mail import send_mass_mail
from django.template.loader import render_to_string
from django.utils.crypto import get_random_string
from django.utils.html import strip_tags
from django.core.mail import send_mail

from main.models import Parameters

def send_mass_email_to_template(user_list, subject, message, use_test_subject):
    '''
    send mass email to user list filling in variables
        user_list : {email:email, variables:[{name:text},{name:text}] }
        subject : string subject line of email
        message : string message template to be sent
    '''
    logger = logging.getLogger(__name__)
    logger.info("Send mass email to list")

    parameters = Parameters.objects.first()

    message_list = []
    message_list.append(())
    from_email = get_from_email()   
    test_subject_email = settings.EMAIL_TEST_ACCOUNT       #email address sent to during debug

    logger.info(f'{settings.DEBUG} {test_subject_email}')

    block_count = 0   #number of message blocks
    cnt = 0           #message counter within block 

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
        if use_test_subject:
            message_list[block_count] += ((subject, new_message, from_email, [test_subject_email]),)   #use for test emails
        else:
            message_list[block_count] += ((subject, new_message, from_email, [user["email"]]),)  

        cnt += 1
    
    return send_mass_email(block_count, message_list)

#return the from address
def get_from_email():    
    return f'"{settings.EMAIL_HOST_USER_NAME}" <{settings.EMAIL_HOST_USER }>'

#send mass email to list,takes a list
def send_mass_email(block_count, message_list):
    logger = logging.getLogger(__name__)
    logger.info("Send mass email to list")

    logger.info(message_list)

    errorMessage = ""
    mailCount=0
    if len(message_list)>0 :
        try:
            for x in range(block_count+1):            
                logger.info("Sending Block " + str(x+1) + " of " + str(block_count+1))
                mailCount += send_mass_mail(message_list[x], fail_silently=False) 
        except SMTPException as e:
            logger.info('There was an error sending email: ' + str(e)) 
            errorMessage = str(e)
    else:
        errorMessage="Message list empty, no emails sent."

    return {"mailCount":mailCount,"errorMessage":errorMessage}