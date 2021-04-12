'''
send email view
'''
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework import permissions

import logging

from django.conf import settings

from main.globals import send_mass_email_from_template

class SendEmailView(APIView):
    '''
    return a list of all payments or take a list for payment
    '''
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        '''
        handle incoming send mass email
        '''
        logger = logging.getLogger(__name__)
        logger.info(request.data)

        result = take_and_send_incoming_email(request.user, request.data, settings.DEBUG)

        return Response(result['text'], status=result['code'])

def take_and_send_incoming_email(user, data, use_test_subject):
    '''
    take incoming email and send it
    '''

    result = send_mass_email_from_template(user, data["user_list"], data["message_subject"], data["message_text"], use_test_subject)

    return result