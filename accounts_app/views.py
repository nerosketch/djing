# -*- coding: utf-8 -*-
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import NoReverseMatch
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils.translation import ugettext as _
from abonapp.models import AbonGroup

from photo_app.models import Photo
from .models import UserProfile
import mydefs
from guardian.decorators import permission_required_or_403 as permission_required
from guardian.shortcuts import get_objects_for_user, assign_perm, remove_perm


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
    if request.user != usr and not request.user.has_perm('accounts_app.can_view_userprofile', usr):
        raise PermissionDenied
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
    if usr != request.user and not request.user.has_perm('accounts_app.change_userprofile', usr):
        raise PermissionDenied
    if request.method == 'POST':
        ag = request.POST.getlist('ag')
        usr.abon_groups.clear()
        usr.abon_groups.add(*[int(d) for d in ag])
        usr.save()
    abongroups = AbonGroup.objects.only('pk', 'title')
    return render(request, 'accounts/profile_chgroup.html', {
        'uid': uid,
        'userprofile': usr,
        'abongroups': abongroups
    })


@login_required
@mydefs.only_admins
def ch_ava(request):
    if request.method == 'POST':
        phname = request.FILES.get('avatar')
        if phname is None:
            messages.error(request, _('Please select an image'))
        else:
            user = request.user
            if user.avatar:
                user.avatar.delete()
            photo = Photo()
            photo.image = phname
            photo.save()
            user.avatar = photo
            user.save(update_fields=['avatar'])
            request.user = user
            messages.success(request, _('Avatar successfully changed'))

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
@permission_required('accounts_app.add_userprofile')
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
    prf = get_object_or_404(UserProfile, id=uid)
    if uid != request.user.id:
        if not request.user.has_perm('acc_app.delete_userprofile', prf):
            raise PermissionDenied
    prf.delete()
    messages.success(request, _('Profile has been deleted'))
    return redirect('acc_app:accounts_list')


@login_required
@mydefs.only_admins
def acc_list(request):
    users = UserProfile.objects.filter(is_admin=True).exclude(pk=request.user.pk)
    users = get_objects_for_user(request.user, 'accounts_app.can_view_userprofile', users)
    users = mydefs.pag_mn(request, users)
    return render(request, 'accounts/acc_list.html', {
        'users': users
    })


@login_required
def perms(request, uid):
    if not request.user.is_superuser:
        raise PermissionDenied
    userprofile = get_object_or_404(UserProfile, id=uid)
    klasses = (
        'abonapp.AbonGroup', 'abonapp.Abon', 'accounts_app.UserProfile',
        'abonapp.AbonTariff', 'abonapp.AbonStreet', 'devapp.Device',
        'abonapp.PassportInfo', 'abonapp.AdditionalTelephone'
    )
    return render(request, 'accounts/perms/objects_types.html', {
        'userprofile': userprofile,
        'klasses': klasses
    })


@login_required
def perms_klasses(request, uid, klass_name):
    if not request.user.is_superuser:
        raise PermissionDenied
    from django.apps import apps
    userprofile = get_object_or_404(UserProfile, pk=uid)
    app_label, model_name = klass_name.split('.', 1)
    klass = apps.get_model(app_label, model_name)

    objects = klass.objects.all()
    objects = mydefs.pag_mn(request, objects)

    return render(request, 'accounts/perms/objects_of_type.html', {
        'userprofile': userprofile,
        'klass': klass_name,
        'klass_name': klass._meta.verbose_name,
        'objects': objects
    })

@login_required
def perms_edit(request, uid, klass_name, obj_id):
    if not request.user.is_superuser:
        raise PermissionDenied
    from django.apps import apps
    from .forms import MyUserObjectPermissionsForm
    userprofile = get_object_or_404(UserProfile, pk=uid)
    app_label, model_name = klass_name.split('.', 1)
    klass = apps.get_model(app_label, model_name)
    obj = get_object_or_404(klass, pk=obj_id)

    frm = MyUserObjectPermissionsForm(userprofile, obj, request.POST or None)
    if request.method == 'POST' and frm.is_valid():
        frm.save_obj_perms()
        messages.success(request, _('Permissions has successfully updated'))

    return render(request, 'accounts/perms/perms_edit.html', {
        'userprofile': userprofile,
        'obj': obj,
        'form': frm,
        'klass': klass_name,
        'klass_name': klass._meta.verbose_name
    })


@login_required
def set_abon_groups_permission(request, uid):
    # Only superuser can change object permissions
    if not request.user.is_superuser:
        raise PermissionDenied
    userprofile = get_object_or_404(UserProfile, pk=uid)

    picked_groups = get_objects_for_user(userprofile, 'abonapp.can_view_abongroup', accept_global_perms=False)
    picked_groups = picked_groups.values_list('pk', flat=True)

    if request.method == 'POST':
        checked_groups = [int(ag) for ag in request.POST.getlist('ag', default=0)]
        for abon_group in AbonGroup.objects.all():
            if abon_group.pk in checked_groups and abon_group.pk not in picked_groups:
                assign_perm('abonapp.can_view_abongroup', userprofile, obj=abon_group)
            elif abon_group.pk not in checked_groups and abon_group.pk in picked_groups:
                remove_perm('abonapp.can_view_abongroup', userprofile, obj=abon_group)
        return redirect('acc_app:set_abon_groups_permission', uid)
    abongroups = AbonGroup.objects.only('pk', 'title')

    return render(request, 'accounts/set_abon_groups_permission.html', {
        'uid': uid,
        'userprofile': userprofile,
        'abongroups': abongroups,
        'picked_groups_ids': picked_groups
    })
