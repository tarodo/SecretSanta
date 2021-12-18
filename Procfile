release: python manage.py migrate
web: gunicorn SecretSanta.wsgi --log-file=-
worker: python manage.py bot