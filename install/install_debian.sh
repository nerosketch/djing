#!/bin/bash

PATH=/bin:/usr/local/bin:/usr/bin:/usr/local/sbin:/usr/sbin:/sbin

apt -y update
apt -y upgrade

sleep 1
apt -y install mariadb-server libmariadb-dev libmariadbclient-dev \
    mariadb-client python3-dev python3-pip python3-pil python3-venv uwsgi \
    nginx uwsgi-plugin-python3 libsnmp-dev git gettext libcurl4-openssl-dev \
    libssl-dev expect redis-server

sleep 3

mkdir -p /var/www
cd /var/www

mysql -u root -e "create database djing_db charset utf8 collate utf8_general_ci;"
mysql -u root -e "create user 'djinguser'@'localhost' identified by 'password';"
mysql -u root -e "grant all privileges on djing_db.* to 'djinguser'@'localhost';"
mysql -u root -e "flush privileges;"

git clone --depth=1 https://github.com/nerosketch/djing.git
cd djing
python3 -m venv venv
source ./venv/bin/activate
pip3 install --upgrade pip
export PYCURL_SSL_LIBRARY=openssl
pip3 install -r requirements.txt
cp djing/local_settings.py.example djing/local_settings.py
chmod +x ./manage.py
./manage.py migrate
./manage.py compilemessages -l ru
echo "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.create_superuser('+79781234567', 'admin', 'admin')" | ./manage.py shell
deactivate

cp install/robots.txt robots.txt
cp install/djing.ini /etc/uwsgi/apps-available/djing.ini
ln -s /etc/uwsgi/apps-available/djing.ini /etc/uwsgi/apps-enabled/djing.ini
cp install/nginx_server.conf /etc/nginx/sites-available/djing.conf
ln -s /etc/nginx/sites-available/djing.conf /etc/nginx/sites-enabled/djing.conf

chown -R www-data:www-data /var/www/djing

# dirs
find . -type d \( -path ./venv -o -path ./src -o -path ./.git \) -prune -o -type d -exec chmod 750 {} \;
# files
find . -type d \( -path ./venv -o -path ./src -o -path ./.git \) -prune -o -type f -exec chmod 640 {} \;
# exec scripts
chmod 750 dhcp_lever.py manage.py periodic.py devapp/expect_scripts/dlink_DGS1100_reboot.exp
chmod 400 djing/settings.py

rm /etc/nginx/sites-enabled/default
systemctl restart uwsgi
systemctl restart nginx


cp ./systemd_units/djing_celery.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable djing_celery.service
systemctl start djing_celery.service


echo -e "\n\nOpen your Djing on http://`hostname -i`/
Initial login and password admin admin\n"
