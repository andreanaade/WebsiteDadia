release: python manage.py migrate
web: python manage.py collectstatic --no-input; gunicorn dadia.wsgi --log-file -