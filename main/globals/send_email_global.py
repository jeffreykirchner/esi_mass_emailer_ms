
from smtplib import SMTPException
from rest_framework import status

from asgiref.sync import async_to_sync

import logging
import random
import asyncio

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

    #no emails to send
    if len(user_list) == 0:
        return {"mail_count" : 0, "error_message" : "Message list empty, no emails sent."}

    parameters = Parameters.objects.first()

    from_email = get_from_email()   
    test_account_email = settings.EMAIL_TEST_ACCOUNT       #email address sent to during debug

    #store message
    mass_email = MassEmail()
    mass_email.app = user
    mass_email.message_subject = subject
    mass_email.message_text = message
    mass_email.user_list = user_list
    mass_email.memo = memo

    mass_email.save()

    logger.info(f'{settings.DEBUG} {test_account_email}')

    message_block_count = 20           #number of message blocks to send
    message_block_counter = 0          #loop counter

    message_block_list = []            #list of all messages

    #fill with empty tuples
    for i in range(message_block_count):
        message_block_list.append(())

    try:
        for user in user_list:
                           
            #fill in variables
            new_message = message

            for variable in user["variables"]:
                new_message = new_message.replace(f'[{variable["name"]}]', variable["text"])

            #fill in subject parameters
            if use_test_account:
                message_block_list[message_block_counter] += ((subject, new_message, from_email, [test_account_email]),)   #use for test emails
            else:
                message_block_list[message_block_counter] += ((subject, new_message, from_email, [user["email"]]),)  

            message_block_counter += 1

            if message_block_counter == 20:
                message_block_counter = 0

    except KeyError as key_error:
        logger.warning(f"send_mass_email_from_template: {key_error} was not found in {user}")
        return {'text' : {"mail_count" : 0, "error_message" : f'{key_error} was not found in {user}'},
                'code' : status.HTTP_400_BAD_REQUEST}
    
    #send emails
    mail_count = 0
    error_message = ""

    try:

        mail_count = send_email_blocks(message_block_list)    

        # for message_block in message_block_list:            
        #     mail_count += send_email_block(message_block)
    except SMTPException as e:
        logger.warning('There was an error sending email: ' + str(e)) 
        error_message = str(e)

    mass_email.email_result = {"mail_count" : mail_count, "error_message" : error_message}
    mass_email.save()

    if mass_email.email_result["error_message"] == "":
        return {'text' : mass_email.email_result, 'code' : status.HTTP_201_CREATED}
    else:
        return {'text' : mass_email.email_result, 'code' : status.HTTP_400_BAD_REQUEST}

#return the from address
def get_from_email():    
    return f'"{settings.EMAIL_HOST_USER_NAME}" <{settings.EMAIL_HOST_USER }>'

@async_to_sync
async def send_email_blocks(message_block_list):
    mail_count = 0

    task_list = []
    for message_block in message_block_list:
        task_list.append(send_email_block(message_block))

    mail_count = await asyncio.gather(*task_list)

    # for task in task_list:
    #     mail_count += await task
    
    return sum(mail_count)

async def send_email_block(message_block):
    '''
    send single email block
    '''
    return send_mass_mail(message_block, fail_silently=False) 