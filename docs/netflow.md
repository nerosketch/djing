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
Посмотреть пример работы можно так:

