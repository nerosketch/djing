from django import forms
from docsapp.models import DocumentTemplateModel


class DocumentTemplateModelForm(forms.ModelForm):
    class Meta:
        model = DocumentTemplateModel
        fields = '__all__'
