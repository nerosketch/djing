from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404

from forms import PoolForm
from models import IpPoolItem
import mydefs


@login_required
@mydefs.only_admins
def home(request):
    pools = IpPoolItem.objects.get_pools()
    print pools

    if pools:
        pools = map(lambda ip: (mydefs.int2ip(ip[0]), mydefs.int2ip(ip[1]), ip[2]), pools)
        pools = mydefs.pag_mn(request, pools)

    return render(request, 'ip_pool/index.html', {
        'pools': pools
    })


@login_required
@mydefs.only_admins
def ips(request):
    ip_start = request.GET.get('ips')
    ip_end   = request.GET.get('ipe')

    pool_ips = IpPoolItem.objects.filter(ip__gte=ip_start)
    pool_ips = pool_ips.filter(ip__lte=ip_end)

    pool_ips = mydefs.pag_mn(request, pool_ips)

    return render(request, 'ip_pool/ips.html', {
        'pool_ips': pool_ips,
        'ips': ip_start,
        'ipe': ip_end
    })


@login_required
@mydefs.only_admins
def del_pool(request):
    ip_start = request.GET.get('ips')
    ip_end   = request.GET.get('ipe')

    pool_ips = IpPoolItem.objects.filter(ip__gte=ip_start)
    pool_ips = pool_ips.filter(ip__lte=ip_end)
    pool_ips = pool_ips.filter()

    pool_ips.delete()

    return mydefs.res_success(request, 'pool_home_link')


@login_required
@mydefs.only_admins
def add_pool(request):
    if request.method == 'POST':
        frm = PoolForm(request.POST)
        if frm.is_valid():
            cd = frm.cleaned_data
            IpPoolItem.objects.add_pool(cd['start_ip'], cd['end_ip'])
            return redirect('pool_home_link')
        else:
            warntext = u'Form is not valid'
    else:
        frm = PoolForm()
        warntext = ''
    return render(request, 'ip_pool/add_pool.html', {
        'form': frm,
        'warntext': warntext
    })


@login_required
@mydefs.only_admins
def delip(request):
    ipid = request.GET.get('id')
    get_object_or_404(IpPoolItem, id=ipid).delete()
    return mydefs.res_success(request, 'pool_home_link')
