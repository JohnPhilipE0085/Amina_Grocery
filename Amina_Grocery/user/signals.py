from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver

@receiver(user_logged_in)
def store_user_in_session(sender, request, user, **kwargs):
    request.session['username'] = user.username
    request.session['email'] = user.email
