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
from django.http import HttpResponse
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
