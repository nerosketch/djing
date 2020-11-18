from django.shortcuts import resolve_url
from django.utils.translation import gettext_lazy as _
from django.core.validators import FileExtensionValidator
from django.db import models

from abonapp.models import Abon


class DocumentTemplateModel(models.Model):
    title = models.CharField(_('Title'), max_length=80, unique=True)
    doc_template = models.FileField(
        _('File docx template'), upload_to='word_docs',
        validators=[FileExtensionValidator(allowed_extensions=('docx',))]
    )

    def get_absolute_url(self):
        return resolve_url('docsapp:doc_edit', pk=self.pk)

    def __str__(self):
        return self.title

    class Meta:
        db_table = 'documents'
        ordering = ('title',)
