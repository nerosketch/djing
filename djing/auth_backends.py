from django.contrib.auth.backends import ModelBackend
<<<<<<< HEAD
from accounts_app.models import BaseAccount, UserProfile
from abonapp.models import Abon


class CustomAuthBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None:
            username = kwargs.get(BaseAccount.USERNAME_FIELD)
        print('username', username)
        try:
            user = BaseAccount._default_manager.get_by_natural_key(username)
            print('user', user)
            if user.check_password(password):
                if user.is_admin:
                    print('is adm')
                    auser = UserProfile.objects.get_by_natural_key(username)
                else:
                    print('no adm')
                    auser = Abon.objects.get_by_natural_key(username)
                if self.user_can_authenticate(auser):
                    print('can auth')
                    return auser
                print('no can auth')
            else:
                print('wrong password')
        except BaseAccount.DoesNotExist:
            print('does not exist')
            # Run the default password hasher once to reduce the timing
            # difference between an existing and a non-existing user (#20760).
            BaseAccount().set_password(password)

    def get_user(self, user_id):
        try:
            user = BaseAccount._default_manager.get(pk=user_id)
            if user.is_admin:
                user = UserProfile._default_manager.get(pk=user_id)
            else:
                user = Abon._default_manager.get(pk=user_id)
        except BaseAccount.DoesNotExist:
            return None
        return user if self.user_can_authenticate(user) else None
=======
from .models import BaseAccount, UserProfile



class CustomAuthBackend(ModelBackend):

    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None:
            username = kwargs.get(UserModel.USERNAME_FIELD)
        try:
            user = UserModel._default_manager.get_by_natural_key(username)
        except UserModel.DoesNotExist:
            # Run the default password hasher once to reduce the timing
            # difference between an existing and a non-existing user (#20760).
            UserModel().set_password(password)
        else:
            if user.check_password(password) and self.user_can_authenticate(user):
                return user
>>>>>>> bcdd33ea0fadafe7b09f2c748b231ecf5386e8f9
