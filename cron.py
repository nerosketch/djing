#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import django


if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "djing.settings")
    django.setup()
    from abonapp.models import Abon
    from agent import Transmitter

    tm = Transmitter()

    # получим инфу о записях в NAS
    queues = [queue for queue in tm.read_users_iter()]

    users = Abon.objects.all()
    for user in users:

        # если нет ip то и нет смысла лезть в NAS
        if user.ip_address is None:
            continue

        # а есть-ли у абонента доступ к услуге
        if not user.is_access():
            continue

        # строим структуру агента
        ab = user.build_agent_struct()
        if ab is None:
            # если не построилась структура агента, значит нет ip
            # а если нет ip то и синхронизировать абонента без ip нельзя
            continue

        # ищем абонента в списке инфы из nas
        abons = [{'abon': queue.abon, 'mikro_id': queue.sid} for queue in queues if queue.abon.uid == user.pk]
        abons_len = len(abons)
        if abons_len < 1:
            # абонент не найден в nas, добавим
            tm.add_user(ab)
            continue
        elif abons_len > 1:
            # удаляем срез из nas, всё кроме 1й записи
            tm.remove_user_range(
                [mkid['mikro_id'] for mkid in abons[1:]]
            )
        # один абонент
        # сравним совпадает-ли инфа об абоненте в базе и в nas
        if ab == abons[0]['abon']:
            # если всё совпадает, то менять нечего
            continue
        else:
            print('Change abon:', user.get_full_name())
            # иначе обновляем абонента
            tm.update_user(ab, abons[0]['mikro_id'])
            # если не активен то приостановим услугу
            if user.is_active:
                tm.start_user(abons[0]['mikro_id'])
            else:
                tm.pause_user(abons[0]['mikro_id'])
