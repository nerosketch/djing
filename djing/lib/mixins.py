from django.contrib.auth.mixins import AccessMixin, LoginRequiredMixin
from guardian.mixins import PermissionRequiredMixin


class OnlyAdminsMixin(AccessMixin):
    """Verify that the current user is admin."""
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_admin:
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)


class LoginAdminMixin(LoginRequiredMixin, OnlyAdminsMixin):
    pass


class LoginAdminPermissionMixin(LoginRequiredMixin, OnlyAdminsMixin,
                                PermissionRequiredMixin):
    return_403 = True
