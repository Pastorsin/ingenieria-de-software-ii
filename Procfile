release: python3 manage.py makemigrations accounts
release: python3 manage.py migrate
web: gunicorn is2.wsgi --log-file -