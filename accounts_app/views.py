# -*- coding: utf-8 -*-
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth import authenticate, login, logout
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import NoReverseMatch
from django.shortcuts import render, redirect, get_object_or_404, resolve_url
from django.contrib.auth.models import Group, Permission
from django.contrib import messages
from django.utils.translation import ugettext as _
from abonapp.models import AbonGroup

from photo_app.models import Photo
from .models import UserProfile
import mydefs


@login_required
@mydefs.only_admins
def home(request):
    return redirect('acc_app:profile')


def to_signin(request):
    nextl = request.GET.get('next')
    nextl = '' if nextl == 'None' or nextl is None or nextl.isspace() else nextl

    try:
        if request.POST:
            auser = authenticate(username=request.POST.get('login'), password=request.POST.get('password'))
            if auser:
                login(request, auser)
                if nextl == 'None' or nextl is None or nextl == '':
                    if request.user.is_staff:
                        return redirect('acc_app:profile')

                    return redirect('client_side:home')

                return redirect(nextl)

            return render(request, 'accounts/login.html', {
                'next': nextl,
                'errmsg': _('Wrong login or password, please try again')
            })
        return render(request, 'accounts/login.html', {
            'next': nextl
        })
    except NoReverseMatch:
        return redirect('acc_app:profile')


def sign_out(request):
    logout(request)
    return redirect('acc_app:login')


@login_required
@mydefs.only_admins
def profile_show(request, uid=0):
    uid = mydefs.safe_int(uid)

    if uid == 0:
        return redirect('acc_app:other_profile', uid=request.user.id)

    usr = get_object_or_404(UserProfile, id=uid)
    if request.method == 'POST':
        usr.username = request.POST.get('username')
        usr.fio = request.POST.get('fio')
        usr.telephone = request.POST.get('telephone')
        usr.is_active = request.POST.get('stat')
        usr.is_admin = request.POST.get('is_admin')
        usr.save()
        return redirect('acc_app:other_profile', uid=uid)

    return render(request, 'accounts/index.html', {
        'uid': uid,
        'userprofile': usr
    })


@login_required
@mydefs.only_admins
def chgroup(request, uid):
    uid = mydefs.safe_int(uid)
    if uid == 0:
        usr = request.user
    else:
        usr = get_object_or_404(UserProfile, id=uid)
    if request.method == 'POST':
        ag = request.POST.getlist('ag')
        usr.abon_groups.clear()
        usr.abon_groups.add(*[int(d) for d in ag])
        usr.save()
    abongroups = AbonGroup.objects.all()
    return render(request, 'accounts/profile_chgroup.html', {
        'uid': uid,
        'userprofile': usr,
        'abongroups': abongroups
    })


@login_required
@mydefs.only_admins
def ch_ava(request):
    if request.method == 'POST':
        user = request.user
        if user.avatar:
            user.avatar.delete()
        photo = Photo()
        photo.image = request.FILES.get('avatar')
        photo.save()
        user.avatar = photo
        user.save(update_fields=['avatar'])
        request.user = user

    return render(request, 'accounts/settings/ch_info.html', {
        'user': request.user
    })


@login_required
@mydefs.only_admins
def ch_info(request):
    if request.method == 'POST':
        user = request.user
        user.username = request.POST.get('username')
        user.fio = request.POST.get('fio')
        user.email = request.POST.get('email')
        user.telephone = request.POST.get('telephone')

        psw = request.POST.get('oldpasswd')
        if psw != '' and psw is not None:
            if user.check_password(psw):
                newpasswd = request.POST.get('newpasswd')
                if newpasswd != '' and newpasswd is not None:
                    user.set_password(newpasswd)
                    user.save()
                    request.user = user
                    logout(request)
                    return redirect('acc_app:other_profile', uid=user.pk)
                else:
                    messages.error(request, _('New password is empty, fill it'))
            else:
                messages.error(request, _('Wrong password'))
        else:
            messages.warning(request, _('Empty password, fill it'))

    return render(request, 'accounts/settings/ch_info.html', {
        'user': request.user
    })


@login_required
@permission_required('acc_app.add_userprofile')
def create_profile(request):
    if request.method == 'POST':
        username = request.POST.get('username')

        user = UserProfile()
        user.username = username
        user.fio = request.POST.get('fio')
        user.email = request.POST.get('email')
        user.telephone = request.POST.get('telephone')
        user.is_admin = True

        passwd = request.POST.get('passwd')
        conpasswd = request.POST.get('conpasswd')
        if not passwd:
            messages.error(request, _('You forget specify a password for the new account'))

        if not conpasswd:
            messages.error(request, _('You forget to repeat a password for the new account'))

        if passwd == conpasswd:
            user_qs = UserProfile.objects.filter(username=username)[:1]
            if user_qs.count() == 0:
                user.set_password(passwd)
                user.save()
                return redirect('acc_app:accounts_list')
            else:
                messages.error(request, _('Subscriber with this name already exist'))
        else:
            messages.error(request, _('Passwords does not match, try again'))
        return render(request, 'accounts/create_acc.html', {
            'newuser': user
        })
    return render(request, 'accounts/create_acc.html')


@login_required
@mydefs.only_admins
def delete_profile(request, uid):
    if uid != request.user.id:
        if not request.user.has_perm('acc_app.delete_userprofile'):
            raise PermissionDenied
    prf = get_object_or_404(UserProfile, id=uid)
    prf.delete()
    return redirect('acc_app:accounts_list')


@login_required
@mydefs.only_admins
def acc_list(request):
    users = UserProfile.objects.filter(is_admin=True)
    users = mydefs.pag_mn(request, users)
    return render(request, 'accounts/acc_list.html', {
        'users': users
    })


@login_required
@mydefs.only_admins
def perms(request, uid):
    profile = get_object_or_404(UserProfile, id=uid)
    own_permissions = UserProfile.get_all_permissions(profile)
    return render(request, 'accounts/settings/permissions.html', {
        'uid': uid,
        'own_permissions': own_permissions
    })


@login_required
@mydefs.only_admins
def groups(request):
    grps = Group.objects.all()
    grps = mydefs.pag_mn(request, grps)
    return render(request, 'accounts/group_list.html', {
        'groups': grps
    })


@login_required
@mydefs.only_admins
def group(request, uid):
    uid = mydefs.safe_int(uid)
    grp = get_object_or_404(Group, id=uid)

    if request.method == 'POST':
        group_rights = filter(lambda x: x[0] == 'group_rights', request.POST.lists())[0][1]
        grp.permissions.clear()
        for grr in group_rights:
            rid = mydefs.safe_int(grr)
            grp.permissions.add(rid)
        grp.save()
        return redirect('acc_app:profile_group_link', id=uid)

    grp_rights = grp.permissions.all()
    all_rights = Permission.objects.exclude(group=grp)

    return render(request, 'accounts/group.html', {
        'group': grp,
        'all_rights': all_rights,
        'grp_rights': grp_rights
    })


@login_required
@mydefs.only_admins
def appoint_task(req, uid):
    uid = mydefs.safe_int(uid)
    url = resolve_url('taskapp:add')
    return redirect("%s?rp=%d" % (url, uid))
