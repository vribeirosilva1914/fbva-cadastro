"""
Ponto de entrada WSGI para servidores de produção.

Gunicorn (recomendado):
    gunicorn wsgi:application -w 2 -b 0.0.0.0:8000

uWSGI:
    uwsgi --http 0.0.0.0:8000 --module wsgi:application

Passenger (cPanel):
    Aponte o arquivo de startup para este wsgi.py
"""
from werkzeug.middleware.proxy_fix import ProxyFix
from app import create_app

application = create_app()
# Render (e qualquer proxy reverso) passa headers X-Forwarded-*.
# Sem ProxyFix, Flask vê scheme=http e host errado, o que pode impedir
# que cookies Secure sejam enviados corretamente.
application.wsgi_app = ProxyFix(application.wsgi_app, x_for=1, x_proto=1, x_host=1)
