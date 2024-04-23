echo "*** Startup.sh ***"
echo "Run Migrations:"
python manage.py migrate
echo "Start gunicorn:"
gunicorn --bind=0.0.0.0 --timeout 1200 --workers=2 --max-requests 500 --max-requests-jitter 10 --limit-request-field_size 64000 _esi_mass_emailer.wsgi
