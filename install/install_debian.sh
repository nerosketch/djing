#!/bin/bash

PATH=/bin:/usr/local/bin:/usr/bin:/usr/local/sbin:/usr/sbin:/sbin

apt-get -y update

sleep 1
apt-get -y upgrade

sleep 1
apt-get -y install mariadb-server libmariadb-dev mariadb-client python3-dev python3-pip python3-pil python3-venv uwsgi nginx uwsgi-plugin-python3 libsnmp-dev git gettext libcurl4-openssl-dev libssl-dev expect

sleep 3

mkdir -p /var/www
cd /var/www

git clone https://github.com/nerosketch/djing.git -b devel djing
cd djing
python3 -m venv venv
source ./venv/bin/activate
pip3 install --upgrade pip
export PYCURL_SSL_LIBRARY=openssl
pip3 install -r requirements.txt
cp djing/local_settings.py.example djing/settings.py
deactivate

chown -R www-data:www-data /var/www
