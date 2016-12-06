# -*- coding: utf-8 -*-
from django.contrib.auth.decorators import login_required  # , permission_required
from django.contrib.auth import authenticate, login, logout
from django.core.urlresolvers import NoReverseMatch
from django.shortcuts import render, redirect, get_object_or_404, resolve_url
from django.template.context_processors import csrf
from django.http import Http404
from django.contrib.auth.models import Group, Permission

from photo_app.models import Photo
from models import UserProfile
import mydefs


@login_required
@mydefs.only_admins
def home(request):
    return redirect('profile')


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
                        return redirect('profile')

                    return redirect('client_home')

                return redirect(nextl)

            return render(request, 'accounts/login.html', {
                'next': nextl,
                'errmsg': u'Неправильный логин или пароль, попробуйте ещё раз'
            })
        return render(request, 'accounts/login.html', {
            'next': nextl
        })
    except NoReverseMatch:
        raise Http404(u"Destination page does not exist")


def sign_out(request):
    logout(request)
    return redirect('login_link')


@login_required
@mydefs.only_admins
def profile_show(request, id=0):
    id = mydefs.safe_int(id)

    if id == 0:
        usr = request.user
    else:
        usr = get_object_or_404(UserProfile, id=id)

    if request.method == 'POST':
        usr.username = request.POST.get('username')
        usr.fio = request.POST.get('fio')
        usr.telephone = request.POST.get('telephone')
        usr.is_active = request.POST.get('stat')
        usr.is_admin = request.POST.get('is_admin')
        usr.save()
        return redirect('other_profile', id=id)

    return render(request, 'accounts/index.html', {
        'uid': id,
        'userprofile': usr
    })


@login_required
@mydefs.only_admins
def chgroup(request, uid):
    usr = get_object_or_404(UserProfile, id=uid)
    usergroups = usr.groups.all()
    othergroups = filter(lambda g: g not in usergroups, Group.objects.all())
    # Group.objects.exclude(user__in=usergroups)

    return render(request, 'accounts/profile_chgroup.html', {
        'uid': uid,
        'userprofile': usr,
        'allgroups': othergroups,
        'usergroups': usergroups
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
        user.save()
        request.user = user

    return render(request, 'accounts/settings/ch_info.html', {
        'user': request.user
    })


@login_required
@mydefs.only_admins
def ch_info(request):
    warntext = ''
    if request.method == 'POST':
        user = request.user
        user.username = request.POST.get('username')
        user.fio = request.POST.get('fio')
        user.email = request.POST.get('email')
        user.telephone = request.POST.get('telephone')

        psw = request.POST.get('oldpasswd')
        if psw != '':
            if user.check_password(psw):
                newpasswd = request.POST.get('newpasswd')
                user.set_password(newpasswd)
            else:
                warntext = u'Неправильный пароль'
        user.save()
        request.user = user

    return render(request, 'accounts/settings/ch_info.html', {
        'user': request.user,
        'warntext': warntext
    })


@login_required
@mydefs.only_admins
##@permission_required('accounts_app.add_userprofile')
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
            return render(request, 'accounts/create_acc.html', {
                'warntext': u'Забыли указать пароль для нового аккаунта',
                'csrf_token': csrf(request)['csrf_token'],
                'newuser': user
            })
        if not conpasswd:
            return render(request, 'accounts/create_acc.html', {
                'warntext': u'Забыли повторить пароль для нового аккаунта',
                'csrf_token': csrf(request)['csrf_token'],
                'newuser': user
            })

        if passwd == conpasswd:
            user_qs = UserProfile.objects.filter(username=username)[:1]
            if user_qs.count() == 0:
                user.set_password(passwd)
                user.save()
                return redirect('accounts_list')
            else:
                return render(request, 'accounts/create_acc.html', {
                    'warntext': u'Пользователь с таким именем уже есть',
                    'csrf_token': csrf(request)['csrf_token'],
                    'newuser': user
                })
        else:
            return render(request, 'accounts/create_acc.html', {
                'warntext': u'Пароли не совпадают, попробуйте ещё раз',
                'csrf_token': csrf(request)['csrf_token'],
                'newuser': user
            })
    return render(request, 'accounts/create_acc.html', {'csrf_token': csrf(request)['csrf_token'], })


@login_required
@mydefs.only_admins
# @permission_required('accounts_app.del_userprofile')
def delete_profile(request, uid):
    prf = get_object_or_404(UserProfile, id=uid)
    prf.delete()
    return redirect('accounts_list')


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
# @permission_required('accounts_app.change_userprofile')
def perms(request, id):
    ingroups = filter(lambda x: x[0] == 'ingroups', request.POST.lists())[0][1]
    id = mydefs.safe_int(id)

    profile = get_object_or_404(UserProfile, id=id)
    profile.groups.clear()

    for group_id in ingroups:
        gid = mydefs.safe_int(group_id)
        profile.groups.add(gid)
    profile.save()

    return redirect('other_profile', id)


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
# @permission_required('auth.change_group')
def group(request, id):
    id = mydefs.safe_int(id)
    grp = get_object_or_404(Group, id=id)

    if request.method == 'POST':
        group_rights = filter(lambda x: x[0] == 'group_rights', request.POST.lists())[0][1]
        grp.permissions.clear()
        for grr in group_rights:
            rid = mydefs.safe_int(grr)
            grp.permissions.add(rid)
        grp.save()
        return redirect('profile_group_link', id=id)

    grp_rights = grp.permissions.all()
    all_rights = Permission.objects.exclude(group=grp)

    #prms = Permission.objects.all()
    #for pr in prms:
    #    print u"%s   |   %s" % (pr.name, pr.codename)

    return render(request, 'accounts/group.html', {
        'csrf_token': csrf(request)['csrf_token'],
        'group': grp,
        'all_rights': all_rights,
        'grp_rights': grp_rights
    })


@login_required
@mydefs.only_admins
def appoint_task(req, uid):
    uid = mydefs.safe_int(uid)
    url = resolve_url('task_add')
    return redirect("%s?rp=%d" % (url, uid))
