"""
Ponto de entrada WSGI para servidores de produção.

Gunicorn (recomendado):
    gunicorn wsgi:application -w 2 -b 0.0.0.0:8000

uWSGI:
    uwsgi --http 0.0.0.0:8000 --module wsgi:application

Passenger (cPanel):
    Aponte o arquivo de startup para este wsgi.py
"""
from app import create_app

application = create_app()
