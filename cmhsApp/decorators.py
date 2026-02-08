from django.shortcuts import redirect
from django.contrib import messages

from django.shortcuts import redirect
from django.contrib import messages


def premium_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')


        if request.user.role != 'patient':
            return view_func(request, *args, **kwargs)

        if not request.user.is_premium:
            messages.warning(request, "This is a Premium feature. Please upgrade to access.")
            return redirect('pricing_page')
        return view_func(request, *args, **kwargs)

    return wrapper