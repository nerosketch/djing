from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect


@login_required
def home(request):
    if request.user.is_staff:
        return redirect('acc_app:setup_info')
    else:
        return redirect('client_side:home')
