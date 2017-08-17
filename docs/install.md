## Установка(не завершил описание):
Работа предполагается на python3.
Я предпочитаю запускать wsgi сервер на связке uWSGI + Nginx, так что ставить будем соответствующие пакеты.

На ArchLinux нужые пакеты можно установить так:
```
# pacman -Sy mariadb-clients python3 python-pip nginx uwsgi redis
```
На Fedora нужые пакеты можно установить так:
```
# dnf install 
```
Дальше ставим всё для python через pip:
```
# pip install git+https://github.com/nerosketch/djing.git
```

### Настройка WEB Сервера
Условимся что путь к папке с проектом находится по адресу: </var/www/djing>

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


### Настраиваем системные утилиты
Если ваша система работает с поддержкой *systemd* то в каталоге *systemd_units* проекта вы найдёте юниты для systemd.
Скопируйте их в каталог юнитов systemd, у меня это путь */etc/systemd/system*.

А теперь запустим 