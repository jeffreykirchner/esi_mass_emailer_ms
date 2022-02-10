
from smtplib import SMTPException
from rest_framework import status

from asgiref.sync import async_to_sync
from datetime import datetime
from multiprocessing import Pool

import logging
import random
import asyncio
import concurrent.futures

from django.conf import settings
from django.core.mail import send_mass_mail
from django.template.loader import render_to_string
from django.utils.crypto import get_random_string

from django.core.mail import send_mail
from django.core import mail
from django.core.mail import EmailMessage
from django.core.mail import EmailMultiAlternatives
from django.utils.html import strip_tags

from main.models import Parameters, MassEmail

#depreciated
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
        logger.warning("User list empty")
        return {'text' : {"mail_count" : 0, "error_message" : 'User list empty'},
                'code' : status.HTTP_400_BAD_REQUEST}

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

    message_block_count = 8            #number of message blocks to send
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
                email = user["email"]
                message_block_list[message_block_counter] += ((subject, new_message, from_email, [test_account_email]),)   #use for test emails
            else:
                message_block_list[message_block_counter] += ((subject, new_message, from_email, [user["email"]]),)  

            message_block_counter += 1

            if message_block_counter == message_block_count:
                message_block_counter = 0

    except KeyError as key_error:
        logger.warning(f"send_mass_email_from_template: {key_error} was not found in {user}")
        return {'text' : {"mail_count" : 0, "error_message" : f'{key_error} was not found in {user}'},
                'code' : status.HTTP_400_BAD_REQUEST}
    
    #send emails
    mail_count = 0
    error_message = ""

    logger.info(f'Start mail send {datetime.now()}')

    try:

        mail_count = send_email_blocks_pool(message_block_list)    

        # for message_block in message_block_list:            
        #     mail_count += send_email_block(message_block)
    except SMTPException as e:
        logger.warning('There was an error sending email: ' + str(e)) 
        error_message = str(e)
    
    logger.info(f'End mail send {datetime.now()}, mail count {mail_count}, error message: {error_message}')

    mass_email.email_result = {"mail_count" : mail_count, "error_message" : error_message}
    mass_email.save()

    if mass_email.email_result["error_message"] == "":
        return {'text' : mass_email.email_result, 'code' : status.HTTP_201_CREATED}
    else:
        return {'text' : mass_email.email_result, 'code' : status.HTTP_400_BAD_REQUEST}

def send_mass_email_message_from_template(user, user_list, subject, message_plain, message_html, memo, use_test_account):
    '''
    send mass EmailMessage to user list filling in variables
        user_list : {email:email, variables:[{name:text},{name:text}] }
        subject : string subject line of email
        message_plain : plain text string message template to be sent
        message_html : html text string message template to be sent
        memo : string about message's purpose
        use_test_accout : send all email to test accout
    '''

    logger = logging.getLogger(__name__)
    logger.info(f"send_mass_email_message_from_template: Count:{len(user_list)}")

    #no emails to send
    if len(user_list) == 0:
        logger.warning("send_mass_email_message_from_template: User list empty")
        return {'text' : {"mail_count" : 0, "error_message" : 'User list empty'},
                'code' : status.HTTP_400_BAD_REQUEST}

    parameters = Parameters.objects.first()

    from_email = get_from_email()   
    test_account_email = settings.EMAIL_TEST_ACCOUNT       #email address sent to during debug

    #store message
    mass_email = MassEmail()
    mass_email.app = user
    mass_email.message_subject = subject
    mass_email.message_text = message_plain
    mass_email.user_list = user_list
    mass_email.memo = memo

    mass_email.save()

    logger.info(f'send_mass_email_message_from_template: Debug:{settings.DEBUG}, Test Account:{test_account_email}')

    message_block_count = 8            #number of message blocks to send
    message_block_counter = 0          #loop counter

    message_block_list = []            #list of all messages

    #fill with empty tuples
    for i in range(message_block_count):
        message_block_list.append([])

    try:
        for user in user_list:
                           
            #fill in variables
            new_message_body_plain = message_plain
            new_message_body_html = message_html

            for variable in user["variables"]:
                new_message_body_plain = new_message_body_plain.replace(f'[{variable["name"]}]', variable["text"])

                if message_html:
                    new_message_body_html = new_message_body_html.replace(f'[{variable["name"]}]', variable["text"])

            #fill in subject parameters
            new_message = EmailMultiAlternatives()            
            new_message.from_email = from_email
            new_message.subject = subject
            new_message.body = new_message_body_plain
            
            #attach html version if provided
            if message_html:
                new_message.attach_alternative(new_message_body_html, "text/html")
            
            if use_test_account:
                new_message.to = [test_account_email]
            else:
                new_message.to =  [user["email"]]

            message_block_list[message_block_counter].append(new_message)

            message_block_counter += 1

            if message_block_counter == message_block_count:
                message_block_counter = 0

    except KeyError as key_error:
        logger.warning(f"send_mass_email_from_template: {key_error} was not found in {user}")
        return {'text' : {"mail_count" : 0, "error_message" : f'{key_error} was not found in {user}'},
                'code' : status.HTTP_400_BAD_REQUEST}
    
    #send emails
    mail_count = 0
    error_message = ""

    logger.info(f'send_mass_email_message_from_template: Start mail send {datetime.now()}')

    try:

   
        mail_count = send_email_blocks_pool(message_block_list)    

        # for message_block in message_block_list:            
        #     mail_count += send_email_block(message_block)
    except SMTPException as e:
        logger.warning('send_mass_email_message_from_template: There was an error sending email: ' + str(e)) 
        error_message = str(e)
    
    logger.info(f'send_mass_email_message_from_template: End mail send {datetime.now()}, mail count {mail_count}, error message: {error_message}')

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
    '''
    send email blocks using asyncio
    '''
    mail_count = 0

    task_list = []
    for message_block in message_block_list:
        if len(message_block) > 0:
            task_list.append(send_email_block(message_block))

    mail_count = await asyncio.gather(*task_list)
    
    return sum(mail_count)

def send_email_blocks_pool(message_block_list):
    '''
    send email blocks using using multiprocessing pool
    '''

    logger = logging.getLogger(__name__)

    message_block_list_trimmed = []

    for message_block in message_block_list:
        if len(message_block) > 0:
            message_block_list_trimmed.append(message_block)

    mail_count = []

    if len(message_block_list_trimmed) == 1:
        mail_count = send_email_messages(message_block_list_trimmed[0])

        logger.info(f'send_email_blocks_pool single mail {mail_count}')

        return mail_count
    else:
        with Pool(len(message_block_list_trimmed)) as p:
            mail_count = p.map(send_email_messages, message_block_list_trimmed)
    
        logger.info(f'send_email_blocks_pool {mail_count}')

        return sum(mail_count)

@async_to_sync
async def send_email_blocks_threads(message_block_list):
    '''
    send email blocks in separate threads
    '''

    mail_count = 0

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = []

        for message_block in message_block_list:
            if len(message_block) > 0:
                futures.append(executor.submit(send_email_block, message_block=message_block))

        for future in concurrent.futures.as_completed(futures):
            mail_count += await future.result()
    
    return mail_count

def send_email_block(message_block):
    '''
    send single email block using mass mail
    '''
    #test code
    #await asyncio.sleep(3)

    return send_mass_mail(message_block, fail_silently=False) 

def send_email_messages(messages):
    '''
    send a list of email messages using send_messages
    messages : EmailMessage
    '''
    with mail.get_connection(fail_silently=False) as connection:
    #connection = mail.get_connection()
        if settings.SIMULATE_SEND:
            result = len(messages)
        else:
            result = connection.send_messages(messages)

        connection.close()

    return result