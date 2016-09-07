# -*- coding:utf-8 -*-
from sys import stdout
from db import load_from_db
from firewall import FirewallManager
from time import sleep
from sslTransmitter import TransmitServer
from agent.models import Abonent, Tariff


def filter_user_by_id(users, uid):
    users = filter(lambda usr: isinstance(usr, Abonent), users)
    users = filter(lambda usr: usr.uid == uid, users)
    if len(users) > 0:
        return users[0]
    else:
        return


def main(debug=False):
    users, tariffs = load_from_db()
    frw = FirewallManager()
    frw.reset()

    # Инициализация абонентов
    if debug:
        print("Инициализация...")
    # Открываем доступ в инет тем кто активен и у кого подключён тариф
    for usr in filter(lambda usr: usr.is_active, users):

        # Доступ в интернет происходит по наличию подключённого тарифа
        # если тарифа нет, то и инета нет
        if usr.tariff:
            # Открываем доступ в инет
            frw.open_inet_door(usr)
            if debug: print "Разрешён доступ в инет для:", usr.ip_str()

    # Слушем в отдельном процессе сеть на предмет событий
    ts = TransmitServer('127.0.0.1', 2134)
    ts.start()

    if debug:
        print("Загружено %d абонентов" % len(users))

    while True:

        # Загружаем события для абонентов из сети (список объектов EventNAS из models)
        events = ts.get_data()
        # Проходим по появившимся событиям
        for event in events:
            #event.toa, event.id, event.dt

            # Смотрим тип события
            toa = int(event.toa)
            if toa == 0: continue

            # Включаем абонента
            elif toa == 1:
                usr = filter_user_by_id(users, event.id)
                # Открываем доступ в инет
                frw.open_inet_door(usr)

            # Выключаем абонента
            elif toa == 2:
                usr = filter_user_by_id(users, event.id)
                # Выключаем интернет
                frw.close_inet_door(usr)

            # Сообщение на заглушку
            elif toa == 3:
                usr = filter_user_by_id(users, event.id)
                # Ставим заглушку
                frw.set_cap(usr)
                # Выключаем интернет
                frw.close_inet_door(usr)

            # Открываем доступ в инет
            elif toa == 4:
                usr = filter_user_by_id(users, event.id)
                frw.close_inet_door(usr)
                frw.open_inet_door(usr)

            # Закрываем доступ в инет
            elif toa == 5:
                usr = filter_user_by_id(users, event.id)
                frw.close_inet_door(usr)

            elif toa == 6:
                # Сигнал на перезагрузку
                # Выходим из main, выше она в цикле запустится ещё раз
                return

            elif toa == 7:
                # Сигнал о том что инфа об абоненте изменилась, надо перечитать
                usr = filter_user_by_id(users, event.id)
                usr.deserialize(event.dt, tariffs)
                # если абонент активен, и куплен и активирован тариф то можно и в инет
                if usr.is_active and usr.tariff is not None:
                    frw.close_inet_door(usr)
                    frw.open_inet_door(usr)

            elif toa == 8:
                # Сигнал об изменении данных в тарифе
                tariff = filter(lambda trf: trf.tid == event.id, tariffs)
                if len(tariff) > 0:
                    tariff = tariff[0]
                    tariff.deserialize(event.dt)

                    # Пересоздаём тариф
                    frw.destroy_tariff(tariff)
                    frw.make_tariff(tariff)
                else:
                    print('WARNING: не найден тариф для которого возбуждён сигнал на изменение данных, пробуем перезагрузиться')
                    return

        # Очищаем очередь событий
        ts.clear()

        # ждём время между итерациями проверки 10 сек...
        sleep(10)
        stdout.write('.')
        stdout.flush()
