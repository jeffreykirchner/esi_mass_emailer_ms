# pylint: disable=no-member

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import *

from django.conf import settings



# message = Mail(
#     from_email='esirecruiter_test@chapman.edu',
#     to_emails='kirchner@chapman.edu',
#     subject='Sending with Twilio SendGrid is Fun',
#     html_content='<strong>and easy to do anywhere, even with Python</strong>')

message = Mail()

message.from_email = From(
    email=settings.EMAIL_HOST_USER,
    name=settings.EMAIL_HOST_USER_NAME,
)

message.subject = Subject("Example Subject")

message.content = [
    Content(
        mime_type="text/html",
        content="[name],<br><p>Hello from Twilio SendGrid!</p>"
    )
]

personalization1 = Personalization()
personalization1.add_email(To('kirchner@chapman.edu'))
personalization1.add_substitution(Substitution('[name]', 'Jeff'))
message.add_personalization(personalization1)

# personalization1 = Personalization()
# personalization1.add_email(To('jkirchner@gmail.com'))
# personalization1.add_substitution(Substitution('[name]', 'Jeff K'))
# message.add_personalization(personalization1)

try:
    sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
    response = sg.send(message)
    print(f'Status Code: {response.status_code}')
    print(f'Body: {response.body}')
    print(f'Headers: {response.headers}')
except Exception as e:
    
    print(e)