### Сбор информации трафика по netflow

Установим flow-tools

Fedora:

> dnf install -y flow-tools flow-tools-devel

Затем надо собрать утилиту для преобразования flow в запрос для mysql.
Возьмём её из github:
```
cd /var/www/djing/agent/netflow/
git clone https://github.com/nerosketch/djing_flow.git djing_flow_git
cd djing_flow_git/
make
mv djing_flow ../
cd ..
rm -rf djing_flow_git
```

Инструкцию по использованию можно найти на странице [djing_flow](https://github.com/nerosketch/djing_flow).
Посмотреть пример работы можно с помощью файла дампа трафика flow-tools. Соберём такой дамп с помощью **flow-capture**.
> \# flow-capture -p /run/flow.pid -w /tmp/djing_flow -n1 -N0 0/0/6343

Запустится сбор трафика. Чтоб узнать больше почитайте инструкции по использованию flow-tools. Настройте netflow sensor на
ваш сервер. Для того чтоб сбросить дамп трафика на диск отправте сигнал **-HUP** процессу flow-capture. В */tmp/djing_flow*
вы найдёте этот самый файл дампа трафика. И тут уже можно посмотреть как работает утилита **djing_flow**:
> \$ ./djing_flow < /tmp/djing_flow_dump.tmp

На выходе вы получите запрос для mysql. Можно перенаправить его по конвееру в mysql, рабочий пример
перенаправления этогй утилиты вы можете увидеть в файле
*agent/netflow/netflow_handler.sh*.
