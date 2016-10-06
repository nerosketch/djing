# -*- coding:utf-8 -*-
from sys import stdout
from db import load_from_db
from firewall import FirewallManager
from time import sleep
from sslTransmitter import TransmitServer
from agent.models import Abonent, Tariff


def filter_user_by_id(users, uid):
    #users = filter(lambda usr: isinstance(usr, Abonent), users)
    users = filter(lambda usr: usr.uid == uid, users)
    if len(users) > 0:
        return users[0]


def filter_tariff_by_id(tariffs, tid):
    #tariffs = filter(lambda trf: isinstance(trf, Tariff), tariffs)
    tariffs = filter(lambda trf: trf.tid == tid, tariffs)
    if len(tariffs) > 0:
        return tariffs[0]


def create_abon(tariffs, users, event, frw):
    print('SIGNAL: Create abon')
    trf = filter_tariff_by_id(tariffs, int(event.dt['tarif_id']))
    abon = Abonent(
        int(event.id),
        int(event.dt['ip']),
        trf
    )
    users.append(abon)
    frw.open_inet_door(abon)


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

            # создаём абонента
            elif toa == 1:
                create_abon(tariffs, users, event, frw)

            # Сигнал о том что инфа об абоненте изменилась, надо перечитать
            elif toa == 2:
                print('SIGNAL: Change abon')
                usr = filter_user_by_id(users, event.id)
                if usr:
                    usr.deserialize(event.dt, tariffs)
                    ##############################
                    # НАДО УБЕДИТЬСЯ ЧТО ИЗМЕНЕНИЯ ЗАТРОНУТ ЭЛЕМЕНТ usr В ГЛОБАЛЬНОМ СПИСКЕ
                    ##############################
                    # если абонент активен, и куплен и активирован тариф то можно и в инет
                    if usr.is_active and usr.tariff is not None:
                        frw.close_inet_door(usr)
                        frw.open_inet_door(usr)

                    # DEBUG убеждаемся в изменениях
                    usr_dbg = filter_user_by_id(users, event.id)
                    assert usr.uid == usr_dbg.uid
                    assert usr.ip == usr_dbg.ip
                else:
                    create_abon(tariffs, users, event, frw)

            # Удаляем абонента
            elif toa == 3:
                print('SIGNAL: Delete abon')
                usr = filter_user_by_id(users, event.id)
                frw.close_inet_door(usr)
                users.remove(usr)

            # Создаём тариф
            elif toa == 4:
                print('SIGNAL: Create tariff')
                trf = Tariff(
                    int(event.dt['tid']),
                    float(event.dt['speedIn']),
                    float(event.dt['speedOut'])
                )
                tariffs.append(trf)
                frw.make_tariff(trf)

            # Обновить тарифф
            elif toa == 5:
                print('SIGNAL: Change tariff')
                trf = filter_tariff_by_id(tariffs, int(event.dt['tarif_id']))
                trf.deserialize(event.dt)
                frw.destroy_tariff(trf)
                frw.make_tariff(trf)

            # Удалить тарифф
            elif toa == 6:
                print('SIGNAL: Delete tariff')
                ban_users = filter(lambda usr: usr.tariff.tid == usr.tariff.tid, users)
                for usr in ban_users:
                    frw.close_inet_door(usr)
                trf = filter_tariff_by_id(tariffs, int(event.dt['tarif_id']))
                tariffs.remove(trf)

            elif toa == 7:
                # Сигнал на перезагрузку
                # Выходим из main, выше она в цикле запустится ещё раз
                return

        # Очищаем очередь событий
        ts.clear()

        # ждём время между итерациями проверки 10 сек...
        sleep(10)
        stdout.write('.')
        stdout.flush()
