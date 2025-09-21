"""CRM System URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path
from django.contrib.auth import views as auth_views

from . import admin_views, counsellor_views, views

urlpatterns = [
    # Authentication URLs
    path("", views.login_page, name='login_page'),
    path("doLogin/", views.doLogin, name='user_login'),
    path("logout_user/", views.logout_user, name='user_logout'),
    path("firebase-messaging-sw.js", views.showFirebaseJS, name='showFirebaseJS'),
    
    # Password Reset URLs
    path('password_reset/', auth_views.PasswordResetView.as_view(), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),
    
    # Admin URLs
    path("admin/home/", admin_views.admin_home, name='admin_home'),
    path("admin/profile/", admin_views.admin_view_profile, name='admin_view_profile'),
    path("admin/notifications/", admin_views.admin_view_notifications, name='admin_view_notifications'),
    
    # Counsellor Management
    path("counsellor/add/", admin_views.add_counsellor, name='add_counsellor'),
    path("counsellor/manage/", admin_views.manage_counsellors, name='manage_counsellors'),
    path("counsellor/edit/<int:counsellor_id>/", admin_views.edit_counsellor, name='edit_counsellor'),
    path("counsellor/delete/<int:counsellor_id>/", admin_views.delete_counsellor, name='delete_counsellor'),
    path("counsellor/performance/", admin_views.counsellor_performance, name='counsellor_performance'),
    
    # Lead Management
    path("leads/manage/", admin_views.manage_leads, name='manage_leads'),
    path("leads/add/", admin_views.add_lead, name='add_lead'),
    path("leads/view/<int:lead_id>/", admin_views.admin_view_lead, name='admin_view_lead'),
    path("leads/ai-workflow/<int:lead_id>/", admin_views.admin_run_ai_workflow, name='admin_run_ai_workflow'),
    path("leads/ai-assign/<int:lead_id>/", admin_views.ai_assign_counsellor, name='ai_assign_counsellor'),
    path("leads/bulk-ai-assign/", admin_views.bulk_ai_assign_counsellors, name='bulk_ai_assign_counsellors'),
    path("leads/manual-route/<int:lead_id>/", admin_views.manual_route_student, name='manual_route_student'),
    path("leads/edit/<int:lead_id>/", admin_views.edit_lead, name='edit_lead'),
    path("leads/delete/<int:lead_id>/", admin_views.delete_lead, name='delete_lead'),
    path("leads/import/", admin_views.import_leads, name='import_leads'),
    path("leads/import/template/<str:file_type>/", admin_views.download_import_template, name='download_import_template'),
    path("leads/assign/", admin_views.assign_leads_to_counsellors, name='assign_leads_to_counsellors'),
    path("leads/transfer/<int:lead_id>/", admin_views.transfer_lead, name='transfer_lead'),
    
    # Lead Sources
    path("lead-sources/manage/", admin_views.manage_lead_sources, name='manage_lead_sources'),
    path("lead-sources/add/", admin_views.add_lead_source, name='add_lead_source'),
    path("lead-sources/edit/<int:source_id>/", admin_views.edit_lead_source, name='edit_lead_source'),
    path("lead-sources/delete/<int:source_id>/", admin_views.delete_lead_source, name='delete_lead_source'),
    
    # Business Management
    path("businesses/manage/", admin_views.manage_businesses, name='manage_businesses'),
    
    # Notifications
    path("notifications/send/", admin_views.send_counsellor_notification, name='send_counsellor_notification'),
    
    # Analytics
    path("analytics/leads/", admin_views.get_lead_analytics, name='get_lead_analytics'),
    
    # Counsellor URLs
    path('counsellor/home/', counsellor_views.counsellor_home, name='counsellor_home'),
    path('counsellor/profile/', counsellor_views.counsellor_view_profile, name='counsellor_view_profile'),
    path('counsellor/notifications/', counsellor_views.counsellor_view_notifications, name='counsellor_view_notifications'),
    path('counsellor/fcmtoken/', counsellor_views.counsellor_fcmtoken, name='counsellor_fcmtoken'),
    
    # Counsellor Lead Management
    path('counsellor/leads/', counsellor_views.my_leads, name='my_leads'),
    path('counsellor/leads/<int:lead_id>/', counsellor_views.lead_detail, name='lead_detail'),
    path('counsellor/leads/<int:lead_id>/activity/add/', counsellor_views.add_lead_activity, name='add_lead_activity'),
    path('counsellor/leads/<int:lead_id>/status/update/', counsellor_views.update_lead_status, name='update_lead_status'),
    path('counsellor/leads/<int:lead_id>/business/create/', counsellor_views.create_business, name='create_business'),
    path('counsellor/leads/<int:lead_id>/transfer/request/', counsellor_views.request_lead_transfer, name='request_lead_transfer'),
    path('counsellor/leads/<int:lead_id>/follow-up/schedule/', counsellor_views.schedule_follow_up, name='schedule_follow_up'),
    path('counsellor/leads/<int:lead_id>/conversion/evaluate/', counsellor_views.evaluate_conversion_score, name='evaluate_conversion_score'),
    path('counsellor/leads/<int:lead_id>/mark-lost/', counsellor_views.mark_lead_lost, name='mark_lead_lost'),
    
    # Counsellor Business Management
    path('counsellor/businesses/', counsellor_views.my_businesses, name='my_businesses'),
    path('counsellor/businesses/<int:business_id>/', counsellor_views.business_detail, name='business_detail'),
    path('counsellor/businesses/<int:business_id>/status/update/', counsellor_views.update_business_status, name='update_business_status'),
    
    # Counsellor Activities
    path('counsellor/activities/', counsellor_views.my_activities, name='my_activities'),
    
    # Counsellor Analytics
    path('counsellor/analytics/', counsellor_views.get_my_analytics, name='get_my_analytics'),
    
    # Notification Management
    path('counsellor/notification/delete/<int:notification_id>/', views.delete_counsellor_notification, name='delete_counsellor_notification'),
    path('admin/notification/delete/<int:notification_id>/', views.delete_admin_notification, name='delete_admin_notification'),
    
    # Test URL
    path('test-login/', views.test_login, name='test_login'),
    
    # Temporary deployment URL (remove after use)
    path('run-migrations/', views.run_migrations, name='run_migrations'),
]
