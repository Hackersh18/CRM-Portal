from .models import NotificationCounsellor, NotificationAdmin

def notification_count(request):
    count = 0
    if request.user.is_authenticated:
        if hasattr(request.user, 'counsellor'):
            count = NotificationCounsellor.objects.filter(counsellor=request.user.counsellor, is_read=False).count()
        elif hasattr(request.user, 'admin'):
            count = NotificationAdmin.objects.filter(is_read=False).count()
    return {'notification_count': count}
