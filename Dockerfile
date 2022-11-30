FROM python:3.9-alpine
LABEL maintainer="nerosketch@gmail.com"

ENV PYTHONUNBUFFERED 1
ENV PYTHONOPTIMIZE 1
ENV PYTHONIOENCODING UTF-8
ENV DJANGO_SETTINGS_MODULE djing.settings
ENV PYCURL_SSL_LIBRARY openssl

RUN ["apk", "add", "net-snmp-dev", "arping", "gettext", "inetutils-telnet", "musl-dev", "libffi-dev", "libpq-dev", "make", "gcc", "curl-dev", "libjpeg-turbo-dev", "zlib-dev", "expect", "python3-dev", "mariadb-dev", "--no-cache"]
RUN ["adduser", "-G", "www-data", "-SDH", "-h", "/var/www/djing2", "www-data"]
RUN mkdir -p /var/www/djing/media && chown -R www-data. /var/www/djing

COPY --chown=www-data:www-data ["requirements.txt", "/var/www/djing"]
RUN ["pip", "install", "--no-cache-dir", "--upgrade", "-r", "/var/www/djing/requirements.txt"]

EXPOSE 8000

VOLUME /var/www/djing/media
VOLUME /var/www/djing/static

COPY --chown=www-data:www-data [".", "/var/www/djing/"]
COPY --chown=www-data:www-data ["djing/local_settings.py.example", "/var/www/djing/djing/local_settings.py"]

WORKDIR /var/www/djing
USER www-data

#RUN ["./manage.py", "collectstatic", "--no-input", "--link"]

CMD ./manage.py migrate && \
    ./manage.py compilemessages && \
    exec gunicorn --bind 0.0.0.0:8000 --workers 15 djing.wsgi:application
