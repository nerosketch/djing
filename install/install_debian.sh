/usr/bin/bash -

PATH=/usr/local/bin:/usr/bin:/usr/local/sbin:/usr/sbin

apt update
apt upgrade
apt-get install postgresql python3-dev python3-pip python3-pil uwsgi nginx uwsgi-plugin-python3 libsnmp-dev git gettext libcurl4-openssl-dev libssl-dev

chown -R www-data:www-data /var/www

cd /var/www

git clone https://github.com/nerosketch/djing.git -b devel djing

