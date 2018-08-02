# -*- coding:utf-8 -*-
import os
from PIL import Image
from django.db import models
from django.contrib.auth.models import BaseUserManager, AbstractBaseUser, PermissionsMixin
from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from group_app.models import Group


class MyUserManager(BaseUserManager):
    def create_user(self, telephone, username, password=None):
        """
        Creates and saves a User with the given email, date of
        birth and password.
        """
        if not telephone:
            raise ValueError(_('Users must have an telephone number'))

        user = self.model(
            telephone=telephone,
            username=username,
        )

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, telephone, username, password):
        """
        Creates and saves a superuser with the given email, date of
        birth and password.
        """
        user = self.create_user(telephone,
                                password=password,
                                username=username
                                )
        user.is_admin = True
        user.is_superuser = True
        user.save(using=self._db)
        return user


class BaseAccount(AbstractBaseUser, PermissionsMixin):
    username = models.CharField(
        _('profile username'),
        max_length=127,
        unique=True,
        validators=(RegexValidator(r'^\w{1,127}$'),)
    )
    fio = models.CharField(_('fio'), max_length=256)
    birth_day = models.DateField(_('birth day'), auto_now_add=True)
    is_active = models.BooleanField(_('Is active'), default=True)
    is_admin = models.BooleanField(default=False)
    telephone = models.CharField(
        max_length=16,
        verbose_name=_('Telephone'),
        blank=True,
        validators=(RegexValidator(
            getattr(settings, 'TELEPHONE_REGEXP', r'^(\+[7,8,9,3]\d{10,11})?$')
        ),)
    )

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ('telephone',)

    def get_full_name(self):
        return self.fio if self.fio else self.username

    def get_short_name(self):
        return self.username or self.telephone

    # Use UserManager to get the create_user method, etc.
    objects = MyUserManager()

    @property
    def is_staff(self):
        " Is the user a member of staff?"
        # Simplest possible answer: All admins are staff
        return self.is_admin

    def __str__(self):
        return self.get_full_name()

    class Meta:
        db_table = 'base_accounts'
        ordering = ('username',)


class UserProfileManager(MyUserManager):
    def get_profiles_by_group(self, group_id):
        return self.filter(responsibility_groups__id__in=(group_id,), is_admin=True, is_active=True)


class UserProfile(BaseAccount):
    avatar = models.ImageField(_('Avatar'), upload_to=os.path.join('user', 'avatar'), null=True, default=None)
    email = models.EmailField(default='')
    responsibility_groups = models.ManyToManyField(Group, blank=True, verbose_name=_('Responsibility groups'))

    objects = UserProfileManager()

    def get_big_ava(self):
        if self.avatar and os.path.isfile(self.avatar.path):
            return self.avatar.url
        else:
            return getattr(settings, 'DEFAULT_PICTURE', '/static/img/user_ava.gif')

    def get_min_ava(self):
        return self.get_big_ava()

    class Meta:
        permissions = (
            ('can_view_userprofile', _('Can view staff profile')),
        )
        verbose_name = _('Staff account profile')
        verbose_name_plural = _('Staff account profiles')
        ordering = ('fio',)

    def _thumbnail_avatar(self):
        if self.avatar and os.path.isfile(self.avatar.path):
            im = Image.open(self.avatar)
            im.thumbnail((200, 121), Image.ANTIALIAS)
            im.save(self.avatar.path)

    def save(self, *args, **kwargs):
        r = super().save(*args, **kwargs)
        self._thumbnail_avatar()
        return r
