from django.shortcuts import redirect


def home(request):
    return redirect('profile')


def finance_report(request):
    pass
