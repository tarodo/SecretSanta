release: python manage.py migrate
web: gunicorn SecretSanta.wsgi --log-file=-
bot: python manage.py bot