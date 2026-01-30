from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import UserManager
from django.dispatch import receiver
from django.db.models.signals import post_save
from django.db import models
from django.contrib.auth.models import AbstractUser
from datetime import datetime, timedelta
import uuid
import logging


class CustomUserManager(UserManager):
    def _create_user(self, email, password, **extra_fields):
        email = self.normalize_email(email)
        user = CustomUser(email=email, **extra_fields)
        user.password = make_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        assert extra_fields["is_staff"]
        assert extra_fields["is_superuser"]
        return self._create_user(email, password, **extra_fields)


class CustomUser(AbstractUser):
    USER_TYPE = ((1, "Admin"), (2, "Counsellor"))
    GENDER = [("M", "Male"), ("F", "Female")]
    
    username = None  # Removed username, using email instead
    email = models.EmailField(unique=True)
    user_type = models.CharField(default=1, choices=USER_TYPE, max_length=1, db_index=True)
    gender = models.CharField(max_length=1, choices=GENDER)
    profile_pic = models.ImageField(upload_to='profile_pics/', null=True, blank=True)
    address = models.TextField()
    phone = models.CharField(max_length=15, blank=True)
    fcm_token = models.TextField(default="")  # For firebase notifications
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []
    objects = CustomUserManager()

    def __str__(self):
        return self.first_name + " " + self.last_name


class Admin(models.Model):
    admin = models.OneToOneField(CustomUser, on_delete=models.CASCADE)

    def __str__(self):
        return self.admin.first_name + " " + self.admin.last_name


class Counsellor(models.Model):
    admin = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    employee_id = models.CharField(max_length=20, unique=True)
    department = models.CharField(max_length=100, blank=True)
    joining_date = models.DateField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    performance_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)
    total_leads_assigned = models.IntegerField(default=0)
    total_business_generated = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)

    def __str__(self):
        return f"{self.admin.first_name} {self.admin.last_name} ({self.employee_id})"


class LeadSource(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Lead(models.Model):
    LEAD_STATUS = (
        ('NEW', 'New'),
        ('CONTACTED', 'Contacted'),
        ('QUALIFIED', 'Qualified'),
        ('PROPOSAL_SENT', 'Proposal Sent'),
        ('NEGOTIATION', 'Negotiation'),
        ('CLOSED_WON', 'Closed Won'),
        ('CLOSED_LOST', 'Closed Lost'),
        ('TRANSFERRED', 'Transferred')
    )
    
    PRIORITY = (
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
        ('URGENT', 'Urgent')
    )

    lead_id = models.CharField(max_length=20, unique=True, default=uuid.uuid4)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=15)
    school_name = models.CharField(max_length=200, blank=True, verbose_name="School Name")
    position = models.CharField(max_length=100, blank=True)
    GRADUATION_CHOICES = (
        ('YES', 'Yes'),
        ('NO', 'No'),
    )
    
    # Map to existing database columns
    graduation_status = models.CharField(max_length=3, choices=GRADUATION_CHOICES, default='NO', verbose_name="Graduation Status")
    graduation_course = models.CharField(max_length=200, blank=True, default='Not Specified', verbose_name="Graduation Course")
    graduation_year = models.IntegerField(null=True, blank=True, verbose_name="Graduation Year")
    graduation_college = models.CharField(max_length=200, blank=True, default='Not Specified', verbose_name="Graduation College", db_column='college_name')  # Maps to college_name in DB
    course_interested = models.CharField(max_length=200, blank=True, verbose_name="Course Interested In")
    is_graduated = models.CharField(max_length=3, choices=GRADUATION_CHOICES, default='NO', verbose_name="Is Graduated")  # Maps to existing is_graduated field
    
    # Keep industry field for backward compatibility but make it hidden
    industry = models.CharField(max_length=100, blank=True, verbose_name="Industry (Legacy)")
    source = models.ForeignKey(LeadSource, on_delete=models.PROTECT)
    status = models.CharField(max_length=20, choices=LEAD_STATUS, default='NEW', db_index=True)
    priority = models.CharField(max_length=10, choices=PRIORITY, default='MEDIUM', db_index=True)
    assigned_counsellor = models.ForeignKey(Counsellor, on_delete=models.SET_NULL, null=True, blank=True)
    previous_counsellor = models.ForeignKey(Counsellor, on_delete=models.SET_NULL, null=True, blank=True, related_name='previous_leads')
    expected_value = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    actual_value = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    notes = models.TextField(blank=True)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=30, blank=True)
    website = models.URLField(blank=True)
    linkedin = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_contact_date = models.DateTimeField(null=True, blank=True, db_index=True)
    next_follow_up = models.DateTimeField(null=True, blank=True, db_index=True)
    # AI-evaluated probability of conversion (0-100)
    conversion_score = models.IntegerField(null=True, blank=True)
    # AI enrichment and routing
    enriched_job_title = models.CharField(max_length=150, blank=True)
    enrichment_notes = models.TextField(blank=True)
    routed_to = models.CharField(max_length=100, blank=True)
    routing_reason = models.TextField(blank=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.school_name}"

    def save(self, *args, **kwargs):
        if not self.lead_id:
            # Generate shorter lead_id: L-YYMMDD-XXXX (max 12 chars)
            self.lead_id = f"L-{datetime.now().strftime('%y%m%d')}-{uuid.uuid4().hex[:4].upper()}"
        
        # Set is_graduated based on graduation_status
        if self.graduation_status == 'YES':
            self.is_graduated = 'YES'
        else:
            self.is_graduated = 'NO'
            
        super().save(*args, **kwargs)


class LeadActivity(models.Model):
    ACTIVITY_TYPE = (
        ('CALL', 'Phone Call'),
        ('EMAIL', 'Email'),
        ('MEETING', 'Meeting'),
        ('PROPOSAL', 'Proposal Sent'),
        ('FOLLOW_UP', 'Follow Up'),
        ('TRANSFER', 'Lead Transfer'),
        ('NOTE', 'Note')
    )

    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name='activities')
    counsellor = models.ForeignKey(Counsellor, on_delete=models.CASCADE)
    activity_type = models.CharField(max_length=20, choices=ACTIVITY_TYPE, db_index=True)
    subject = models.CharField(max_length=200)
    description = models.TextField()
    outcome = models.CharField(max_length=200, blank=True)
    next_action = models.CharField(max_length=200, blank=True)
    scheduled_date = models.DateTimeField(null=True, blank=True, db_index=True)
    completed_date = models.DateTimeField(auto_now_add=True, db_index=True)
    duration = models.IntegerField(default=0)  # in minutes
    is_completed = models.BooleanField(default=True, db_index=True)

    def __str__(self):
        return f"{self.lead.first_name} - {self.activity_type} - {self.subject}"


class Business(models.Model):
    BUSINESS_STATUS = (
        ('PENDING', 'Pending'),
        ('ACTIVE', 'Active'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled')
    )

    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name='businesses')
    counsellor = models.ForeignKey(Counsellor, on_delete=models.CASCADE)
    business_id = models.CharField(max_length=20, unique=True, default=uuid.uuid4)
    title = models.CharField(max_length=200)
    description = models.TextField()
    value = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=20, choices=BUSINESS_STATUS, default='PENDING', db_index=True)
    start_date = models.DateField(db_index=True)
    end_date = models.DateField(null=True, blank=True)
    payment_terms = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} - {self.lead.first_name} {self.lead.last_name}"

    def save(self, *args, **kwargs):
        if not self.business_id:
            self.business_id = f"BUS-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)


class NotificationCounsellor(models.Model):
    counsellor = models.ForeignKey(Counsellor, on_delete=models.CASCADE)
    message = models.TextField()
    is_read = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.counsellor.admin.first_name} - {self.message[:50]}"


class NotificationAdmin(models.Model):
    message = models.TextField()
    is_read = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Admin - {self.message[:50]}"


class LeadTransfer(models.Model):
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE)
    from_counsellor = models.ForeignKey(Counsellor, on_delete=models.CASCADE, related_name='transfers_from')
    to_counsellor = models.ForeignKey(Counsellor, on_delete=models.CASCADE, related_name='transfers_to')
    reason = models.TextField()
    admin_approved = models.BooleanField(default=False)
    approved_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    approved_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.lead.first_name} {self.lead.last_name} - {self.from_counsellor} to {self.to_counsellor}"


class CounsellorPerformance(models.Model):
    counsellor = models.ForeignKey(Counsellor, on_delete=models.CASCADE)
    month = models.DateField()  # First day of the month
    total_leads_assigned = models.IntegerField(default=0)
    total_leads_contacted = models.IntegerField(default=0)
    total_leads_qualified = models.IntegerField(default=0)
    total_business_generated = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    conversion_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    average_response_time = models.IntegerField(default=0)  # in hours
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['counsellor', 'month']

    def __str__(self):
        return f"{self.counsellor.admin.first_name} - {self.month.strftime('%B %Y')}"


@receiver(post_save, sender=CustomUser)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        if instance.user_type == '1':
            Admin.objects.create(admin=instance)
        # Note: Counsellor profiles are created manually in the view
        # to avoid conflicts with employee_id requirements


@receiver(post_save, sender=CustomUser)
def save_user_profile(sender, instance, **kwargs):
    try:
        if instance.user_type == '1':
            if hasattr(instance, 'admin'):
                instance.admin.save()
        if instance.user_type == '2':
            if hasattr(instance, 'counsellor'):
                instance.counsellor.save()
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"Error saving user profile: {e}")
