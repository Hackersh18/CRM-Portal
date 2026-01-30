import json
import requests
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render, reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .EmailBackend import EmailBackend
from .models import Lead, NotificationCounsellor, NotificationAdmin, Counsellor
from django.core.management import call_command
from io import StringIO

# Create your views here.


def login_page(request):
    if request.user.is_authenticated:
        if request.user.user_type == '1':
            return redirect(reverse("admin_home"))
        elif request.user.user_type == '2':
            return redirect(reverse("counsellor_home"))
    return render(request, 'main_app/login.html')


def doLogin(request, **kwargs):
    if request.method != 'POST':
        return HttpResponse("<h4>Denied</h4>")
    else:
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        # Use EmailBackend directly since Django authenticate is not working
        from .EmailBackend import EmailBackend
        backend = EmailBackend()
        user = backend.authenticate(request, username=email, password=password)
        
        if user != None:
            login(request, user)
            
            if user.user_type == '1':
                return redirect(reverse("admin_home"))
            elif user.user_type == '2':
                return redirect(reverse("counsellor_home"))
            else:
                messages.error(request, "Invalid user type")
                return redirect("/")
        else:
            messages.error(request, "Invalid details")
            return redirect("/")


def logout_user(request):
    if request.user != None:
        logout(request)
    return redirect("/")


def showFirebaseJS(request):
    data = """
    // Give the service worker access to Firebase Messaging.
// Note that you can only use Firebase Messaging here, other Firebase libraries
// are not available in the service worker.
importScripts('https://www.gstatic.com/firebasejs/7.22.1/firebase-app.js');
importScripts('https://www.gstatic.com/firebasejs/7.22.1/firebase-messaging.js');

// Initialize the Firebase app in the service worker by passing in
// your app's Firebase config object.
// https://firebase.google.com/docs/web/setup#config-object
firebase.initializeApp({
    apiKey: "AIzaSyBarDWWHTfTMSrtc5Lj3Cdw5dEvjAkFwtM",
    authDomain: "sms-with-django.firebaseapp.com",
    databaseURL: "https://sms-with-django.firebaseio.com",
    projectId: "sms-with-django",
    storageBucket: "sms-with-django.appspot.com",
    messagingSenderId: "945324593139",
    appId: "1:945324593139:web:03fa99a8854bbd38420c86",
    measurementId: "G-2F2RXTL9GT"
});

// Retrieve an instance of Firebase Messaging so that it can handle background
// messages.
const messaging = firebase.messaging();
messaging.setBackgroundMessageHandler(function (payload) {
    const notification = JSON.parse(payload);
    const notificationOption = {
        body: notification.body,
        icon: notification.icon
    }
    return self.registration.showNotification(payload.notification.title, notificationOption);
});
    """
    return HttpResponse(data, content_type='application/javascript')


def counsellor_view_notification(request):
    counsellor = get_object_or_404(Counsellor, admin=request.user)
    # Mark all as read
    NotificationCounsellor.objects.filter(counsellor=counsellor, is_read=False).update(is_read=True)
    notifications = NotificationCounsellor.objects.filter(counsellor=counsellor)
    context = {
        'notifications': notifications,
        'page_title': "View Notifications"
    }
    return render(request, "counsellor_template/counsellor_view_notification.html", context)


def admin_view_notification(request):
    # Mark all as read
    NotificationAdmin.objects.filter(is_read=False).update(is_read=True)
    notifications = NotificationAdmin.objects.all()
    context = {
        'notifications': notifications,
        'page_title': "View Notifications"
    }
    return render(request, "admin_template/admin_view_notification.html", context)


@require_POST
def delete_counsellor_notification(request, notification_id):
    notification = get_object_or_404(NotificationCounsellor, id=notification_id, counsellor__admin=request.user)
    notification.delete()
    messages.success(request, "Notification deleted.")
    return redirect('counsellor_view_notification')

@require_POST
def delete_admin_notification(request, notification_id):
    notification = get_object_or_404(NotificationAdmin, id=notification_id)
    notification.delete()
    messages.success(request, "Notification deleted.")
    return redirect('admin_view_notification')


def test_login(request):
    """Test view to debug login issues"""
    if request.user.is_authenticated:
        return HttpResponse(f"""
        <h1>Login Test</h1>
        <p>User: {request.user.email}</p>
        <p>User Type: {request.user.user_type}</p>
        <p>Is Staff: {request.user.is_staff}</p>
        <p>Is Superuser: {request.user.is_superuser}</p>
        <p><a href="/admin/home/">Go to Admin Home</a></p>
        <p><a href="/logout_user/">Logout</a></p>
        """)
    else:
        return HttpResponse("Not logged in")


def delete_counsellor_notification(request, notification_id):
    """Delete counsellor notification"""
    if request.user.is_authenticated and request.user.user_type == '2':
        notification = get_object_or_404(NotificationCounsellor, id=notification_id, counsellor__admin=request.user)
        try:
            notification.delete()
            messages.success(request, "Notification deleted successfully!")
        except Exception as e:
            messages.error(request, f"Could not delete notification: {str(e)}")
        return redirect(reverse('counsellor_view_notifications'))
    else:
        messages.error(request, "Access denied!")
        return redirect(reverse('login_page'))


def delete_admin_notification(request, notification_id):
    """Delete admin notification"""
    if request.user.is_authenticated and request.user.user_type == '1':
        notification = get_object_or_404(NotificationAdmin, id=notification_id)
        try:
            notification.delete()
            messages.success(request, "Notification deleted successfully!")
        except Exception as e:
            messages.error(request, f"Could not delete notification: {str(e)}")
        return redirect(reverse('admin_view_notifications'))
    else:
        messages.error(request, "Access denied!")
        return redirect(reverse('login_page'))


def run_migrations(request):
    """Temporary view to run migrations after deployment (remove after use)"""
    if not request.user.is_superuser:
        return HttpResponse("Access denied", status=403)
    
    try:
        output = StringIO()
        call_command('migrate', stdout=output)
        result = output.getvalue()
        
        return HttpResponse(f"<h1>Migrations completed</h1><pre>{result}</pre>")
    except Exception as e:
        return HttpResponse(f"<h1>Migration failed</h1><pre>{str(e)}</pre>")


def custom_password_reset_confirm(request, uidb64=None, token=None):
    """
    Custom password reset confirm view that ensures database is only updated
    after successful validation and password confirmation.
    
    Security features:
    - Database transaction for atomicity
    - Password strength validation
    - Security logging
    - Rate limiting protection
    - Token validation
    """
    from django.contrib.auth.tokens import default_token_generator
    from django.contrib.auth import get_user_model
    from django.utils.http import urlsafe_base64_decode
    from django.contrib.auth.forms import SetPasswordForm
    from django.contrib.auth.hashers import make_password
    from django.db import transaction
    from django.core.cache import cache
    import logging
    
    User = get_user_model()
    logger = logging.getLogger(__name__)
    
    # Rate limiting: Check if too many attempts from this IP
    client_ip = request.META.get('REMOTE_ADDR', 'unknown')
    cache_key = f"password_reset_attempts_{client_ip}"
    attempts = cache.get(cache_key, 0)
    
    if attempts >= 5:  # Max 5 attempts per IP per hour
        messages.error(request, "Too many password reset attempts. Please try again later.")
        logger.warning(f"Rate limit exceeded for password reset from IP: {client_ip}")
        return render(request, 'registration/password_reset_confirm.html', {
            'form': None,
            'validlink': False
        })
    
    # Validate the token and user
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
        logger.warning(f"Invalid password reset token attempt from IP: {client_ip}")
    
    # Check if the token is valid
    if user is not None and default_token_generator.check_token(user, token):
        validlink = True
    else:
        validlink = False
        if user is not None:
            logger.warning(f"Invalid password reset token for user {user.email} from IP: {client_ip}")
    
    if request.method == 'POST' and validlink:
        # Increment rate limiting counter
        cache.set(cache_key, attempts + 1, 3600)  # 1 hour
        
        form = SetPasswordForm(user, request.POST)
        if form.is_valid():
            # Use database transaction to ensure atomicity
            with transaction.atomic():
                try:
                    # Get the new password from the form
                    new_password = form.cleaned_data['new_password1']
                    
                    # Enhanced password strength validation
                    if len(new_password) < 8:
                        messages.error(request, "Password must be at least 8 characters long.")
                        return render(request, 'registration/password_reset_confirm.html', {
                            'form': form,
                            'validlink': validlink
                        })
                    
                    # Check for common weak passwords
                    weak_passwords = ['password', '12345678', 'qwerty123', 'admin123', 'password123']
                    if new_password.lower() in weak_passwords:
                        messages.error(request, "This password is too common. Please choose a stronger password.")
                        return render(request, 'registration/password_reset_confirm.html', {
                            'form': form,
                            'validlink': validlink
                        })
                    
                    # Update the password in the database
                    user.set_password(new_password)
                    user.save()
                    
                    # Clear rate limiting on successful reset
                    cache.delete(cache_key)
                    
                    # Log the password reset for security audit
                    logger.info(f"Password reset successful for user: {user.email} from IP: {client_ip}")
                    
                    messages.success(request, "Your password has been reset successfully!")
                    return redirect('password_reset_complete')
                    
                except Exception as e:
                    # Rollback transaction on error
                    transaction.rollback()
                    messages.error(request, "An error occurred while resetting your password. Please try again.")
                    logger.error(f"Password reset failed for user {user.email} from IP {client_ip}: {str(e)}")
                    return render(request, 'registration/password_reset_confirm.html', {
                        'form': form,
                        'validlink': validlink
                    })
        else:
            # Form validation failed
            logger.warning(f"Password reset form validation failed for user {user.email} from IP: {client_ip}")
    else:
        if validlink:
            form = SetPasswordForm(user)
        else:
            form = None
    
    return render(request, 'registration/password_reset_confirm.html', {
        'form': form,
        'validlink': validlink
    })
