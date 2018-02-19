from datetime import datetime
from django import template

register = template.Library()


@register.simple_tag
def is_today(time):
    if type(time) is not datetime:
        raise TypeError
    now = datetime.now()
    return now.day == time.day


@register.simple_tag
def is_yesterday(time):
    if type(time) is not datetime:
        raise TypeError
    now = datetime.now()
    return now.day - 1 == time.day
