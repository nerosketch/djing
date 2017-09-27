# -*- coding: utf-8 -*-
from guardian.forms import UserObjectPermissionsForm
from guardian.shortcuts import assign_perm, remove_perm


class MyUserObjectPermissionsForm(UserObjectPermissionsForm):

    def save_obj_perms(self):
        """
        Saves selected object permissions by creating new ones and removing
        those which were not selected but already exists.

        Should be called *after* form is validated.
        """
        perms = set(self.cleaned_data[self.get_obj_perms_field_name()])
        model_perms = set([c[0] for c in self.get_obj_perms_field_choices()])
        init_perms = set(self.get_obj_perms_field_initial())

        to_remove = (model_perms - perms) & init_perms
        for perm in to_remove:
            remove_perm(perm, self.user, self.obj)

        for perm in perms - init_perms:
            assign_perm(perm, self.user, self.obj)
