'''
send email view
'''
from datetime import datetime

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework import permissions

import logging

from django.conf import settings

from main.globals import send_mass_email_message_from_template
from main.globals import make_tz_aware_utc

from main.serializers import MassEmailSerializer
from main.models import MassEmail

class GetEmailView(APIView):
    '''
    return a list of all email within range
    '''
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, start_date, end_date):
        '''
       return a list of all email within range
        '''
        logger = logging.getLogger(__name__)
        logger.info(f"Get email between: {start_date} and {end_date}")

        try:
            d_start_date = datetime.strptime(start_date,"%Y-%m-%d")
            d_end_date = datetime.strptime(end_date,"%Y-%m-%d")

            d_start_date = make_tz_aware_utc(d_start_date, 0, 0, 0)
            d_end_date = make_tz_aware_utc(d_end_date, 23, 59, 59)

        except Exception  as exce:
            return Response({"detail": f"Invalid Dates: {start_date} {end_date}, Format: YYYY-MM-DD"},
                             status=status.HTTP_400_BAD_REQUEST)
        
        mass_emails = MassEmail.objects.filter(timestamp__gte = d_start_date)\
                                       .filter(timestamp__lte = d_end_date)

        serializer = MassEmailSerializer(mass_emails, many=True)

        return Response(serializer.data)

def take_and_send_incoming_email(user, data, use_test_subject):
    '''
    take incoming email and send it
    '''

    result = send_mass_email_message_from_template(user,
                                           data["user_list"],
                                           data["message_subject"],
                                           data["message_text"],
                                           data.get("message_text_html", None),
                                           data["memo"],
                                           use_test_subject)

    return result