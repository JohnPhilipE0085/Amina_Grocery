from functools import wraps
from django.shortcuts import redirect

def staff_login_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('admin_login')  
        if not request.user.is_staff:
            return redirect('admin_login')
        return view_func(request, *args, **kwargs)
    return _wrapped_view
