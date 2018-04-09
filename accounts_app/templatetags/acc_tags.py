from django import template
from django.db.models import Model
from django.apps import apps
from six import string_types, class_types

register = template.Library()


@register.simple_tag
def klass_name(klass):
    if type(klass) is class_types and issubclass(klass, Model):
        kl = klass
    elif isinstance(klass, string_types):
        app_label, model_name = klass.split('.', 1)
        kl = apps.get_model(app_label, model_name)
    else:
        return 'Type not detected'
    return kl._meta.verbose_name
