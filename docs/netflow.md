### Сбор информации трафика по netflow

Установите flow-tools, мы будем использовать его в качестве коллектора.

Затем надо собрать утилиту для преобразования flow в запрос для mysql.
Если не хотите собирать то есть собранный бинарь в папке */var/www/djing/agent/netflow/djing_flow.tar.gz*.
Распакуйте его или соберите из github:
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
> \# flow-capture -p /run/flow.pid -w /tmp/djing_flow -n1 -N0 0/0/1234

Запустится сбор трафика. Чтоб узнать больше почитайте инструкции по использованию flow-tools. Настройте netflow sensor на
ваш сервер. Для того чтоб сбросить дамп трафика на диск отправте сигнал **-HUP** процессу flow-capture. В */tmp/djing_flow*
вы найдёте этот самый файл дампа трафика. И тут уже можно посмотреть как работает утилита **djing_flow**:
> \$ ./djing_flow < /tmp/*.tmp

На выходе вы получите запрос для mysql. Можно перенаправить его по конвееру в mysql.
