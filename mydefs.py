# -*- coding: utf-8 -*-
from json import dumps
import socket
import struct
from collections import Iterator
import os
from django.http import HttpResponse, Http404
from django.shortcuts import redirect
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.db import models
from djing.settings import PAGINATION_ITEMS_PER_PAGE


ip_addr_regex = r'^(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'


def ip2int(addr):
    try:
        return struct.unpack("!I", socket.inet_aton(addr))[0]
    except:
        return 0


def int2ip(addr):
    try:
        return socket.inet_ntoa(struct.pack("!I", addr))
    except:
        return ''


def safe_float(fl):
    try:
        return 0.0 if fl is None or fl == '' else float(fl)
    except ValueError:
        return 0.0


def safe_int(i):
    try:
        return 0 if i is None or i == '' else int(i)
    except ValueError:
        return 0


def res_success(request, redirect_to='/'):
    if request.is_ajax():
        return HttpResponse(dumps({'errnum': 0}))
    else:
        return redirect(redirect_to)


def res_error(request, text):
    if request.is_ajax():
        return HttpResponse(dumps({'errnum': 1, 'errtext': text}))
    else:
        raise Http404(text)


# Pagination
def pag_mn(request, objs, count_per_page=PAGINATION_ITEMS_PER_PAGE):
    page = request.GET.get('p')
    pgn = Paginator(objs, count_per_page)
    try:
        objs = pgn.page(page)
    except PageNotAnInteger:
        objs = pgn.page(1)
    except EmptyPage:
        objs = pgn.page(pgn.num_pages)
    return objs


class MyGenericIPAddressField(models.GenericIPAddressField):
    description = "Int32 notation ip address"

    def __init__(self, protocol='IPv4', *args, **kwargs):
        super(MyGenericIPAddressField, self).__init__(protocol=protocol, *args, **kwargs)
        self.max_length = 8

    def get_prep_value(self, value):
        # strIp to Int
        value = super(models.GenericIPAddressField, self).get_prep_value(value)
        return ip2int(value)

    def to_python(self, addr):
        return addr

    def get_internal_type(self):
        return 'PositiveIntegerField'

    @staticmethod
    def from_db_value(value, expression, connection, context):
        return int2ip(value)


# Предназначен для Django CHOICES чтоб можно было передавать классы вместо просто описания поля,
# классы передавать для того чтоб по значению кода из базы понять какой класс нужно взять для нужной функциональности.
# Например по коду в базе вам нужно определять как считать тариф абонента, что реализовано в возвращаемом классе.
class MyChoicesAdapter(Iterator):
    chs = tuple()
    current_index = 0
    _max_index = 0

    # На вход принимает кортеж кортежей, вложенный из 2х элементов: кода и класса, как: TARIFF_CHOICES
    def __init__(self, choices):
        self._max_index = len(choices)
        self.chs = choices

    def next(self):
        if self.current_index >= self._max_index:
            raise StopIteration
        else:
            e = self.chs
            ci = self.current_index
            res = e[ci][0], e[ci][1].description()
            self.current_index += 1
            return res


# Для сортировки таблиц
# через get должно быть передано order_by=<поле в бд> а в dir=<up|down> направление сортировки
# возвращает новое направление сортировки и поле для сортировки с направлением
def order_helper(request):
    dir = request.GET.get('dir')
    dfx = ''
    if dir == 'down':
        dir = 'up'
        dfx = '-'
    else:
        dir = 'down'

    orby = request.GET.get('order_by')
    if orby:
        return dir, dfx + orby
    else:
        return dir, orby


# Декоратор проверяет аккаунт, чтоб не пускать клиентов в страницы администрации
def only_admins(fn):
    def wrapped(request, *args, **kwargs):
        if request.user.is_admin:
            return fn(request, *args, **kwargs)
        else:
            return redirect('client_side:home')

    return wrapped


def ping(hostname):
    response = os.system("`which ping` -c 1 " + hostname)
    return True if response == 0 else False
