## Установка:
Работа предполагается на python3.
Я предпочитаю запускать wsgi сервер на связке uWSGI + Nginx, так что ставить будем соответствующие пакеты.

##### На Fedora25 нужные пакеты можно установить так:

Для начала подготовим систему, очистим и обновим пакеты. Процесс обновления долгий, так что можно пойти заварить себе чай :)
```
# dnf clean all
# dnf -y update
```

Затем установим зависимости
```
# dnf -y install python3 python3-devel python3-pip python3-pillow mariadb uwsgi nginx redis net-snmp net-snmp-libs net-snmp-utils net-snmp-devel net-snmp-python git redhat-rpm-config
```

Условимся что путь к папке с проектом находится по адресу: */var/www/djing*.
Дальше создадим каталок для web, затем обновляем pip и ставим проект через pip:
```
# mkdir /vaw/www
# cd /var/www
# pip3 install --upgrade pip
# git clone https://github.com/nerosketch/djing.git
# pip3 install -r djing/requirements.txt
```

Скопируем конфиги из примеров в реальные:
```
cd /var/www/djing
cp djing/settings_example.py djing/settings.py
cp agent/settings.py.example agent/settings.py
```

Затем отредактируйте конфиги для своих нужд.

Для удобства я создаю пользователя и группу http:http, и всё что связано с web-сервером запускаю от имени http.
```
groupadd -r http
useradd -l -M -r -d /dev/null -g http -s /sbin/nologin http
chown -R http:http /var/www
chown -R http:http /etc/nginx
chown -R http:http /etc/uwsgi.*
```

### Настройка WEB Сервера
Конфиг Nginx на моём рабочем сервере выглядит так:

    user http;
    worker_processes auto;
    pid /run/nginx.pid;
    events {
        worker_connections 1024;
    }
    http {
        sendfile on;
        upstream djing { server unix:///run/uwsgi/djing.sock; }
        
        server {
            listen 80;
            server_name  <ваш-домен>.com;
            root         /var/www/djing;
            charset      utf-8;
            
            # укажите где лежит ваш раздел с медиа для сайта
            location /media  {
                alias /var/www/djing/media;
            }
            
            # местоположение статики           
            location /static {
                alias /var/www/djing/static;
            }
            
            # тут надо указать путь куда у вас установился Django + путь к статике админки
            # путь к Django тут: /usr/lib/python3.5/site-packages/django
            # путь к статике соответственно: contrib/admin/static/admin
            location /static/admin {
                alias /usr/lib/python3.5/site-packages/django/contrib/admin/static/admin;
            }
            
            # на корневом url / реагируем с помощью сокета проекта
            # у нас он называется "djing": upstream djing { server ...
            location / {
                uwsgi_pass djing;
                include uwsgi_params;
            }
        }
    }

Это минимальный конфиг Nginx для работы. Проверте файл /run/uwsgi/djing.sock на доступность пользователю http для чтения.

Далее настраиваем uWSGI. Мой конфиг для uWSGI в режиме emperor:

    [uwsgi]
    uid = http
    gid = http
    pidfile = /run/uwsgi/uwsgi.pid
    emperor = /etc/uwsgi.d
    stats = /run/uwsgi/stats.sock
    chmod-socket = 660
    emperor-tyrant = true
    cap = setgid,setuid

У меня конфиг лежит по адресу /etc/uwsgi.ini


### Настраиваем демоны
Если ваша система работает с поддержкой *systemd* то в каталоге *systemd_units* проекта вы найдёте юниты для systemd.
Скопируйте их в каталог юнитов systemd, у меня это путь */etc/systemd/system*.
__Настоятельно рекомендую заглянуть внутрь этих юнитов__. Проверте пути исполняемых файлов, права и прочее.

А теперь включим и запустим нужные демоны
```
# systemctl daemon-reload
# systemctl enable djing_queue.service
# systemctl start djing_queue.service
# systemctl enable djing_rotate.timer
# systemctl start djing_rotate.timer
# systemctl enable djing_telebot.service
# systemctl start djing_telebot.service
```
Перед включением юнита *djing_telebot.service* создайте Telegram бота и впишите в файл *djing/settings.py* в переменную *TELEGRAM_BOT_TOKEN* токен вашего бота.
С помощью этого бота вы будете получать различные сообщения из биллинга. Подробнее в инструкции к [модулю оповещений](./bot.md).
