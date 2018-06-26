from django import template

register = template.Library()


@register.simple_tag
def url_page_replace(request, field, value):
    dict_ = request.GET.copy()
    dict_[field] = value
    return dict_.urlencode()


@register.simple_tag
def url_order_by(request, **kwargs):
    dict_ = request.GET.copy()
    for k, v in kwargs.items():
        dict_[k] = v
    direction = dict_.get('dir')
    if direction is None:
        direction = dict_.get('default_direction', 'up')
    if direction == 'down':
        direction = 'up'
    elif direction == 'up':
        direction = 'down'
    else:
        direction = ''
    dict_['dir'] = direction
    return dict_.urlencode()
