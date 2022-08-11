
from smtplib import SMTPException
from rest_framework import status
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import *
from datetime import datetime
from multiprocessing import Pool

import logging

from django.conf import settings

import main

def send_mass_email_message_from_template_sendgrid(user, user_list, subject, message_plain, message_html, memo, use_test_account):
    '''
    send mass EmailMessage to user list filling in variables with sendgrid
        user_list : {email:email, variables:[{name:text},{name:text}] }
        subject : string subject line of email
        message : string message template to be sent
        memo : string about message's purpose
        use_test_accout : send all email to test accout
    '''

    logger = logging.getLogger(__name__)
    logger.info(f"send_mass_email_message_from_template_sendgrid: Count:{len(user_list)}")

    #no emails to send
    if len(user_list) == 0:
        logger.warning("send_mass_email_message_from_template_sendgrid: User list empty")
        return {'text' : {"mail_count" : 0, "error_message" : 'User list empty'},
                'code' : status.HTTP_400_BAD_REQUEST}

    parameters = main.models.Parameters.objects.first()

    test_account_email = settings.EMAIL_TEST_ACCOUNT       #email address sent to during debug

    #store message
    mass_email = main.models.MassEmail()
    mass_email.app = user
    mass_email.message_subject = subject
    mass_email.message_text = message_html
    mass_email.user_list = user_list
    mass_email.memo = memo

    mass_email.save()

    logger.info(f'send_mass_email_message_from_template_sendgrid: Debug:{settings.DEBUG}, Test Account:{test_account_email}')

    #send emails
    mail_count = 0
    error_message = ""

    logger.info(f'send_mass_email_message_from_template_sendgrid: Start mail send {datetime.now()}, ID: {mass_email.id}')

    try:

        message = Mail()

        message.from_email = From(
            email=settings.EMAIL_HOST_USER,
            name=settings.EMAIL_HOST_USER_NAME,
        )

        message.subject = Subject(subject)

        message.content = [
            Content(
                mime_type="text/html",
                content=message_html
            )
        ]

        for u in user_list:

            personalization = Personalization()

            if use_test_account:
                personalization.add_email(To(test_account_email))
            else:
                personalization.add_email(To(u["email"]))

            for v in u["variables"]:
                substitution = Substitution(f'[{v["name"]}]', str(v["text"]))
                personalization.add_substitution(substitution)
                
            message.add_personalization(personalization)

        
        sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
        response = sg.send(message)

        if response.status_code == 202:
            mail_count = len(user_list)
            logger.info(f'send_mass_email_message_from_template_sendgrid: Status Code {response.status_code}')
            logger.info(f'send_mass_email_message_from_template_sendgrid: Body {response.body}')
            logger.info(f'send_mass_email_message_from_template_sendgrid: Headers {response.headers}')
        else:
            logger.error(f'send_mass_email_message_from_template_sendgrid: Status Code {response.status_code}')
            logger.error(f'send_mass_email_message_from_template_sendgrid: Body {response.body}')
            logger.error(f'send_mass_email_message_from_template_sendgrid: Headers {response.headers}')

    except SMTPException as e:
        logger.warning('send_mass_email_message_from_template_sendgrid: There was an error sending email: ' + str(e)) 
        error_message = str(e)
    
    logger.info(f'send_mass_email_message_from_template_sendgrid: End mail send {datetime.now()}, mail count {mail_count}, error message: {error_message}, ID: {mass_email.id}')

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