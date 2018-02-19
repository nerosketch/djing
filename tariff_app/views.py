# -*- coding: utf-8 -*-
from django.contrib.auth.decorators import login_required
from django.contrib.gis.shortcuts import render_to_text
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext as _
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.views.generic import ListView
from django.conf import settings
from guardian.decorators import permission_required_or_403 as permission_required

from djing.global_base_views import OrderingMixin
from .models import Tariff, PeriodicPay
import mydefs
from . import forms


class BaseServiceListView(ListView):
    http_method_names = ['get']
    paginate_by = getattr(settings, 'PAGINATION_ITEMS_PER_PAGE', 10)


@method_decorator([login_required, mydefs.only_admins], name='dispatch')
class TariffsListView(BaseServiceListView, OrderingMixin):
    """
    Show Services(Tariffs) list
    """
    template_name = 'tariff_app/tarifs.html'
    context_object_name = 'tariflist'
    model = Tariff


@login_required
def edit_tarif(request, tarif_id=0):
    tarif_id = mydefs.safe_int(tarif_id)

    if tarif_id == 0:
        if not request.user.has_perm('tariff_app.add_tariff'):
            raise PermissionDenied
        tarif = None
    else:
        if not request.user.has_perm('tariff_app.change_tariff'):
            raise PermissionDenied
        tarif = get_object_or_404(Tariff, pk=tarif_id)

    if request.method == 'POST':
        frm = forms.TariffForm(request.POST, instance=tarif)
        if frm.is_valid():
            frm.save()
            messages.success(request, _('Service has been saved'))
            return redirect('tarifs:edit', tarif_id=tarif_id)
        else:
            messages.warning(request, _('Some fields were filled incorrect, please try again'))
    else:
        frm = forms.TariffForm(instance=tarif)

    return render(request, 'tariff_app/editTarif.html', {
        'form': frm,
        'tarif_id': tarif_id
    })


@login_required
@permission_required('tariff_app.delete_tariff')
def del_tarif(request, tid):
    if request.method == 'POST':
        if request.POST.get('confirm') == 'yes':
            get_object_or_404(Tariff, id=tid).delete()
            messages.success(request, _('Service has been deleted'))
        else:
            messages.error(request, _('Not have a confirmations of delete'))
        return mydefs.res_success(request, 'tarifs:home')
    return render_to_text('tariff_app/modal_del_warning.html', {'tid': tid}, request=request)


@method_decorator(login_required, name='dispatch')
@method_decorator(permission_required('tariff_app.can_view_periodic_pay'), name='dispatch')
class PeriodicPaysListView(BaseServiceListView):
    context_object_name = 'pays'
    model = PeriodicPay
    template_name = 'tariff_app/periodic_pays/list.html'


@login_required
def periodic_pay(request, pay_id=0):
    if pay_id != 0:
        pay_inst = get_object_or_404(PeriodicPay, pk=pay_id)
        if not request.user.has_perm('tariff_app.change_periodicpay'):
            raise PermissionDenied
    else:
        pay_inst = None
        if not request.user.has_perm('tariff_app.add_periodicpay'):
            raise PermissionDenied
    if request.method == 'POST':
        frm = forms.PeriodicPayForm(request.POST, instance=pay_inst)
        if frm.is_valid():
            new_periodic_pay = frm.save()
            if pay_inst is None:
                comment = _('New periodic pay successfully created')
            else:
                comment = _('Periodic pay has been changed')
            messages.success(request, comment)
            return redirect('tarifs:periodic_pay_edit', new_periodic_pay.pk)
        else:
            messages.error(request, _('Some fields were filled incorrect, please try again'))
    else:
        frm = forms.PeriodicPayForm(instance=pay_inst)

    return render(request, 'tariff_app/periodic_pays/add_edit.html', {
        'pay_instance': pay_inst,
        'form': frm
    })
