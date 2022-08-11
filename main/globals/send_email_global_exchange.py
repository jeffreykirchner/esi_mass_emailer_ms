
from smtplib import SMTPException
from rest_framework import status

from datetime import datetime
from multiprocessing import Pool

import logging

from django.conf import settings

from django.core import mail
from django.core.mail import EmailMultiAlternatives

import main

def send_mass_email_message_from_template(user, user_list, subject, message_plain, message_html, memo, use_test_account):
    '''
    send mass EmailMessage to user list filling in variables with exchange
        user_list : {email:email, variables:[{name:text},{name:text}] }
        subject : string subject line of email
        message : string message template to be sent
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

    parameters = main.models.Parameters.objects.first()

    from_email = get_from_email()   
    test_account_email = settings.EMAIL_TEST_ACCOUNT       #email address sent to during debug

    #store message
    mass_email = main.models.MassEmail()
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
                new_message_body_plain = new_message_body_plain.replace(f'[{variable["name"]}]', str(variable["text"]))

                if message_html:
                    new_message_body_html = new_message_body_html.replace(f'[{variable["name"]}]', str(variable["text"]))

            #fill in subject parameters
            new_message = EmailMultiAlternatives()            
            new_message.from_email = from_email
            new_message.subject = subject
            new_message.body = new_message_body_plain
            
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
    except TypeError as type_error:
        logger.warning(f"send_mass_email_from_template: {type_error} was not found in {user}")
        return {'text' : {"mail_count" : 0, "error_message" : f'Invalid email variables were not found in {user}'},
                'code' : status.HTTP_400_BAD_REQUEST}
    
    #send emails
    mail_count = 0
    error_message = ""

    logger.info(f'send_mass_email_message_from_template: Start mail send {datetime.now()}, ID: {mass_email.id}')

    try:

        mail_count = send_email_blocks_pool(message_block_list)    

    except SMTPException as e:
        logger.warning('send_mass_email_message_from_template: There was an error sending email: ' + str(e)) 
        error_message = str(e)
    
    logger.info(f'send_mass_email_message_from_template: End mail send {datetime.now()}, mail count {mail_count}, error message: {error_message}, ID: {mass_email.id}')

    mass_email.email_result = {"mail_count" : mail_count, "error_message" : error_message}
    mass_email.save()

    if mass_email.email_result["error_message"] == "":
        return {'text' : mass_email.email_result, 'code' : status.HTTP_201_CREATED}
    else:
        return {'text' : mass_email.email_result, 'code' : status.HTTP_400_BAD_REQUEST}

#return the from address
def get_from_email():    
    return f'"{settings.EMAIL_HOST_USER_NAME}" <{settings.EMAIL_HOST_USER }>'

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