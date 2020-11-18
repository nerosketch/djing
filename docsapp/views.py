from io import BytesIO

from django.contrib import messages
from django.utils.datetime_safe import datetime
from django.utils.translation import gettext_lazy as _
from django.views.generic import UpdateView, DeleteView, CreateView, DetailView, ListView
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.core.exceptions import ValidationError
from django.http import HttpResponse
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse_lazy
from docxtpl import DocxTemplate
from docx.opc.constants import CONTENT_TYPE
from jinja2.exceptions import UndefinedError, TemplateSyntaxError

from abonapp.models import Abon
from djing.global_base_views import OrderedFilteredList
from djing.lib.mixins import LoginAdminMixin, LoginAdminPermissionMixin
from docsapp.models import DocumentTemplateModel
from docsapp.forms import DocumentTemplateModelForm


class DocumentsListView(LoginAdminMixin, OrderedFilteredList):
    model = DocumentTemplateModel


class SimpleListView(LoginAdminMixin, ListView):
    template_name = 'docsapp/simple_list.html'
    model = DocumentTemplateModel

    def get_context_data(self, **kwargs):
        kwargs.update({
            'account_name': self.kwargs.get('account_name')
        })
        return super().get_context_data(**kwargs)


class DocumentUpdateView(LoginAdminPermissionMixin, UpdateView):
    permission_required = 'docsapp.change_documenttemplatemodel'
    model = DocumentTemplateModel
    form_class = DocumentTemplateModelForm


class DocumentDeleteView(LoginAdminPermissionMixin, DeleteView):
    permission_required = 'docsapp.delete_documenttemplatemodel'
    model = DocumentTemplateModel
    success_url = reverse_lazy('docsapp:docs_list')


class DocumentCreateView(LoginAdminMixin, PermissionRequiredMixin, CreateView):
    model = DocumentTemplateModel
    form_class = DocumentTemplateModelForm
    permission_required = 'docsapp.add_documenttemplatemodel'


class RenderDocument(LoginAdminPermissionMixin, DetailView):
    model = DocumentTemplateModel
    permission_required = 'docsapp.view_documenttemplatemodel'
    context_object_name = 'document'
    extra_context = {
        'date': datetime.now()
    }

    def get(self, request, *args, **kwargs):
        obj = self.get_object()
        self.object = obj
        acc = get_object_or_404(Abon, username=self.kwargs.get('uname'))

        try:
            doc = DocxTemplate(
                obj.doc_template.path
            )
            context = self.get_context_data(object=obj)
            context.update(self.get_context_account(acc))
            doc.render(context)

            destination_document_file = BytesIO()
            doc.get_docx().save(destination_document_file)
            resp = HttpResponse(
                destination_document_file.getvalue(),
                content_type=CONTENT_TYPE.WML_DOCUMENT
            )
            resp['Content-Disposition'] = 'attachment; filename="document.docx"'
            return resp
        except (UndefinedError, ValidationError, TemplateSyntaxError) as e:
            messages.error(request, str(e))
        return redirect('docsapp:docs_list')

    def get_context_account(self, account):
        if not isinstance(account, Abon):
            raise ValidationError(message=_('Account required and must be Abon'))
        bp = '_' * 20
        return {
            'account': account,
            'passport': getattr(account, 'passportinfo', {
                'series': bp,
                'number': bp,
                'distributor': bp,
                'date_of_acceptance': bp
            })
        }
