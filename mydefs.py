# -*- coding: utf-8 -*-
from datetime import timedelta
from json import dumps
import socket
import struct
from collections import Iterator
import os
from functools import wraps
from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.shortcuts import redirect
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.db import models
from django.conf import settings


PAGINATION_ITEMS_PER_PAGE = getattr(settings, 'PAGINATION_ITEMS_PER_PAGE', 10)
DEBUG = getattr(settings, 'DEBUG', False)

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

    def __init__(self, protocol='ipv4', *args, **kwargs):
        super(MyGenericIPAddressField, self).__init__(protocol=protocol, *args, **kwargs)
        self.max_length = 8

    def get_prep_value(self, value):
        # strIp to Int
        value = super(MyGenericIPAddressField, self).get_prep_value(value)
        return ip2int(value)

    def to_python(self, value):
        return value

    def get_internal_type(self):
        return 'PositiveIntegerField'

    @staticmethod
    def from_db_value(value, expression, connection, context):
        return int2ip(value) if value != 0 else None

    def int_ip(self):
        return ip2int(self)


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

    def __next__(self):
        if self.current_index >= self._max_index:
            raise StopIteration
        else:
            e = self.chs
            ci = self.current_index
            res = e[ci][0], e[ci][1].description()
            self.current_index += 1
            return res


# Декоратор проверяет аккаунт, чтоб не пускать клиентов в страницы администрации
def only_admins(fn):
    @wraps(fn)
    def wrapped(request, *args, **kwargs):
        if request.user.is_admin:
            return fn(request, *args, **kwargs)
        else:
            return redirect('client_side:home')

    return wrapped


def ping(hostname, count=1):
    response = os.system("`which ping` -4Anq -c%d -W1 %s > /dev/null" % (count, hostname))
    return True if response == 0 else False


# Русифицированный вывод timedelta
class RuTimedelta(timedelta):

    def __new__(cls, tm):
        if isinstance(tm, timedelta):
            return timedelta.__new__(
                cls,
                days=tm.days,
                seconds=tm.seconds,
                microseconds=tm.microseconds
            )

    def __str__(self):
        #hours, remainder = divmod(self.seconds, 3600)
        #minutes, seconds = divmod(remainder, 60)
        #text_date = "%d:%d" % (
        #    hours,
        #    minutes
        #)
        if self.days > 1:
            ru_days = 'дней'
            if 5 > self.days > 1:
                ru_days = 'дня'
            elif self.days == 1:
                ru_days = 'день'
            #text_date = '%d %s %s' % (self.days, ru_days, text_date)
            text_date = '%d %s' % (self.days, ru_days)
        else:
            text_date = ''
        return text_date


def require_ssl(view):
    """
    Decorator that requires an SSL connection. If the current connection is not SSL, we redirect to the SSL version of
    the page.
    from: https://gist.github.com/ckinsey/9709984
    """
    @wraps(view)
    def wrapper(request, *args, **kwargs):
        if not DEBUG and not request.is_secure():
            target_url = "https://" + request.META['HTTP_HOST'] + request.path_info
            return HttpResponseRedirect(target_url)
        return view(request, *args, **kwargs)
    return wrapper


class MultipleException(Exception):

    def __init__(self, err_list):
        if not isinstance(err_list, list):
            raise TypeError
        self.err_list = err_list


class LogicError(Exception):
    pass


def singleton(class_):
    instances = {}
    def getinstance(*args, **kwargs):
        if class_ not in instances:
            instances[class_] = class_(*args, **kwargs)
        return instances[class_]
    return getinstance
