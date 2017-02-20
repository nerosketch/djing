"""
Based on http://www.djangosnippets.org/snippets/595/
by sopelkin
"""

from django.forms import widgets

from django_messages.utils import get_user_model, get_username_field

User = get_user_model()


class CommaSeparatedUserInput(widgets.Input):
    input_type = 'text'

    def render(self, name, value, attrs=None):
        if value is None:
            value = ''
        elif isinstance(value, (list, tuple)):
            value = (', '.join([getattr(user, get_username_field()) for user in value]))
        return super(CommaSeparatedUserInput, self).render(name, value, attrs)
