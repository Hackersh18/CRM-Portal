from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import *

# Register your models here.

class UserModel(UserAdmin):
    ordering = ('email',)
    list_display = ('email', 'first_name', 'last_name', 'user_type', 'is_active')
    list_filter = ('user_type', 'is_active')
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('email',)
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'phone', 'gender', 'profile_pic', 'address')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
        ('User Type', {'fields': ('user_type',)}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'user_type', 'password1', 'password2'),
        }),
    )

class CounsellorAdmin(admin.ModelAdmin):
    list_display = ('employee_id', 'admin', 'department', 'performance_rating', 'total_leads_assigned', 'total_business_generated', 'is_active')
    list_filter = ('department', 'is_active', 'performance_rating')
    search_fields = ('employee_id', 'admin__first_name', 'admin__last_name', 'admin__email')
    ordering = ('employee_id',)

class LeadSourceAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'created_at')
    search_fields = ('name', 'description')
    ordering = ('name',)

class LeadAdmin(admin.ModelAdmin):
    list_display = ('lead_id', 'first_name', 'last_name', 'email', 'phone', 'school_name', 'source', 'status', 'priority', 'assigned_counsellor', 'expected_value', 'created_at')
    list_filter = ('status', 'priority', 'source', 'assigned_counsellor', 'created_at')
    search_fields = ('lead_id', 'first_name', 'last_name', 'email', 'phone', 'school_name')
    ordering = ('-created_at',)
    readonly_fields = ('lead_id', 'created_at')
    actions = ['view_lead_details']
    
    def view_lead_details(self, request, queryset):
        """Custom admin action to view lead details"""
        if queryset.count() == 1:
            lead = queryset.first()
            from django.shortcuts import redirect
            from django.urls import reverse
            return redirect('admin_view_lead', lead_id=lead.id)
        else:
            self.message_user(request, "Please select exactly one lead to view.", level='ERROR')
    view_lead_details.short_description = "View selected lead details"

class LeadActivityAdmin(admin.ModelAdmin):
    list_display = ('lead', 'counsellor', 'activity_type', 'subject', 'outcome', 'scheduled_date', 'completed_date')
    list_filter = ('activity_type', 'outcome', 'scheduled_date', 'completed_date')
    search_fields = ('lead__first_name', 'lead__last_name', 'counsellor__admin__first_name', 'subject')
    ordering = ('-scheduled_date',)

class BusinessAdmin(admin.ModelAdmin):
    list_display = ('business_id', 'lead', 'counsellor', 'title', 'value', 'status', 'start_date', 'end_date')
    list_filter = ('status', 'start_date', 'end_date')
    search_fields = ('business_id', 'title', 'lead__first_name', 'lead__last_name')
    ordering = ('-start_date',)
    readonly_fields = ('business_id',)

class LeadTransferAdmin(admin.ModelAdmin):
    list_display = ('lead', 'from_counsellor', 'to_counsellor', 'reason', 'admin_approved', 'approved_by', 'approved_at')
    list_filter = ('admin_approved', 'approved_at')
    search_fields = ('lead__first_name', 'lead__last_name', 'from_counsellor__admin__first_name', 'to_counsellor__admin__first_name')
    ordering = ('-approved_at',)

class CounsellorPerformanceAdmin(admin.ModelAdmin):
    list_display = ('counsellor', 'month', 'total_leads_assigned', 'total_leads_contacted', 'total_leads_qualified', 'total_business_generated', 'conversion_rate')
    list_filter = ('month', 'conversion_rate')
    search_fields = ('counsellor__admin__first_name', 'counsellor__admin__last_name')
    ordering = ('-month',)

class NotificationCounsellorAdmin(admin.ModelAdmin):
    list_display = ('counsellor', 'message', 'created_at', 'is_read')
    list_filter = ('is_read', 'created_at')
    search_fields = ('counsellor__admin__first_name', 'counsellor__admin__last_name', 'message')
    ordering = ('-created_at',)

class NotificationAdminAdmin(admin.ModelAdmin):
    list_display = ('message', 'created_at', 'is_read')
    list_filter = ('is_read', 'created_at')
    search_fields = ('message',)
    ordering = ('-created_at',)

# Register models
admin.site.register(CustomUser, UserModel)
admin.site.register(Counsellor, CounsellorAdmin)
admin.site.register(LeadSource, LeadSourceAdmin)
admin.site.register(Lead, LeadAdmin)
admin.site.register(LeadActivity, LeadActivityAdmin)
admin.site.register(Business, BusinessAdmin)
admin.site.register(LeadTransfer, LeadTransferAdmin)
admin.site.register(CounsellorPerformance, CounsellorPerformanceAdmin)
admin.site.register(NotificationCounsellor, NotificationCounsellorAdmin)
admin.site.register(NotificationAdmin, NotificationAdminAdmin)
