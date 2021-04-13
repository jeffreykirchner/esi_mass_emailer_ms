python manage.py migrate
daphne -b 0.0.0.0 ESIMassEmailer.asgi:application
