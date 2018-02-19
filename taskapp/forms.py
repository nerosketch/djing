from django.utils.translation import ugettext as _
from django import forms
from .models import Task, ExtraComment, _delta_add_days
from accounts_app.models import UserProfile


class TaskFrm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(TaskFrm, self).__init__(*args, **kwargs)
        self.fields['recipients'].queryset = UserProfile.objects.filter(is_admin=True)

    class Meta:
        model = Task
        exclude = ['time_of_create', 'author', 'device']
        widgets = {
            'descr': forms.TextInput(attrs={
                'placeholder': _('Short description'),
                'autofocus': ''
            }),
            'recipients': forms.SelectMultiple(attrs={
                'size': 10
            }),
            'out_date': forms.DateInput(attrs={'class': 'form-control'}),
            'abon': forms.Select(attrs={'class': 'form-control'})
        }
        initials = {
            'out_date': _delta_add_days()
        }


class ExtraCommentForm(forms.ModelForm):

    def make_save(self, author, task):
        comment = super(ExtraCommentForm, self).save(commit=False)
        comment.author = author
        comment.task = task
        return comment.save()

    def save(self, commit=True):
        raise Exception('You must use ExtraCommentForm.make_save() method')

    class Meta:
        model = ExtraComment
        fields = ['text']
