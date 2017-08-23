# -*- coding:utf-8 -*-
from django.db import models
from django.contrib.auth.models import BaseUserManager, AbstractBaseUser, PermissionsMixin
from django.core.validators import RegexValidator
from django.utils.translation import ugettext as _
from django.conf import settings
from photo_app.models import Photo


DEFAULT_PICTURE = getattr(settings, 'DEFAULT_PICTURE', '/static/images/default-avatar.png')
TELEPHONE_REGEXP = getattr(settings, 'TELEPHONE_REGEXP', r'^\+[7,8,9,3]\d{10,11}$')


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


class UserProfile(AbstractBaseUser, PermissionsMixin):
    username = models.CharField(max_length=127, unique=True)
    fio = models.CharField(max_length=256)
    birth_day = models.DateField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)
    telephone = models.CharField(
        max_length=16,
        verbose_name=_('Telephone'),
        #unique=True,
        validators=[RegexValidator(TELEPHONE_REGEXP)]
    )
    avatar = models.ForeignKey(Photo, null=True, blank=True, on_delete=models.SET_NULL)
    email = models.EmailField(default='admin@example.ru')

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['telephone']

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

    def get_big_ava(self):
        if self.avatar:
            return self.avatar.big()
        else:
            return DEFAULT_PICTURE

    def get_min_ava(self):
        if self.avatar:
            return self.avatar.min()
        else:
            return DEFAULT_PICTURE

    def __str__(self):
        return self.get_full_name()
