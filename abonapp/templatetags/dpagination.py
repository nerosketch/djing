from django import template

register = template.Library()


@register.simple_tag
def url_page_replace(request, field, value):
    dict_ = request.GET.copy()
    dict_[field] = value
    return dict_.urlencode()


@register.simple_tag
def url_replace(request, *args, **kwargs):
    dict_ = request.GET.copy()
    for k, v in kwargs.items():
        dict_[k] = v
    return dict_.urlencode()
