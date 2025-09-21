from django import forms
from django.forms.widgets import DateInput, TextInput, DateTimeInput
from .models import *


class FormSettings(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(FormSettings, self).__init__(*args, **kwargs)
        # Here make some changes such as:
        for field in self.visible_fields():
            field.field.widget.attrs['class'] = 'form-control'


class CustomUserForm(FormSettings):
    email = forms.EmailField(required=True)
    gender = forms.ChoiceField(choices=[('M', 'Male'), ('F', 'Female')])
    first_name = forms.CharField(required=True)
    last_name = forms.CharField(required=True)
    address = forms.CharField(widget=forms.Textarea)
    phone = forms.CharField(max_length=15, required=False)
    password = forms.CharField(widget=forms.PasswordInput)
    widget = {
        'password': forms.PasswordInput(),
    }
    profile_pic = forms.ImageField(required=False)

    def __init__(self, *args, **kwargs):
        super(CustomUserForm, self).__init__(*args, **kwargs)

        if kwargs.get('instance'):
            # For CustomUser instances, use the instance directly
            instance = kwargs.get('instance')
            if hasattr(instance, 'admin'):
                # This is a Counsellor or Admin instance, get the CustomUser
                instance = instance.admin
            self.fields['password'].required = False
            for field in CustomUserForm.Meta.fields:
                if hasattr(instance, field):
                    self.fields[field].initial = getattr(instance, field)
            if self.instance.pk is not None:
                self.fields['password'].widget.attrs['placeholder'] = "Fill this only if you wish to update password"

    def save(self, commit=True):
        """Ensure passwords are hashed on create/update.

        - On create: require password and hash it
        - On update: hash only if a new password was provided; otherwise keep existing
        """
        instance = super(CustomUserForm, self).save(commit=False)
        password = self.cleaned_data.get('password')

        # When creating a new user, password is required by the form; hash it
        if not instance.pk and password:
            from django.contrib.auth.hashers import make_password
            instance.password = make_password(password)

        # When updating existing user, hash only if password field was changed/provided
        if instance.pk:
            if password:
                from django.contrib.auth.hashers import make_password
                instance.password = make_password(password)

        if commit:
            instance.save()
        return instance

    def clean_email(self, *args, **kwargs):
        formEmail = self.cleaned_data['email'].lower()
        if self.instance.pk is None:  # Insert
            if CustomUser.objects.filter(email=formEmail).exists():
                raise forms.ValidationError(
                    "The given email is already registered")
        else:  # Update
            # For CustomUser instances, use the instance directly
            if hasattr(self.instance, 'admin'):
                # This is a Counsellor or Admin instance, get the CustomUser
                dbEmail = self.instance.admin.email.lower()
            else:
                # This is a CustomUser instance
                dbEmail = self.instance.email.lower()
            
            if dbEmail != formEmail:  # There has been changes
                if CustomUser.objects.filter(email=formEmail).exists():
                    raise forms.ValidationError("The given email is already registered")

        return formEmail

    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'email', 'gender', 'phone', 'password', 'profile_pic', 'address']


class CounsellorForm(CustomUserForm):
    employee_id = forms.CharField(max_length=20, required=True)
    department = forms.CharField(max_length=100, required=False)
    
    def __init__(self, *args, **kwargs):
        super(CounsellorForm, self).__init__(*args, **kwargs)

    class Meta(CustomUserForm.Meta):
        model = CustomUser
        fields = CustomUserForm.Meta.fields + ['employee_id', 'department']


class AdminForm(CustomUserForm):
    def __init__(self, *args, **kwargs):
        super(AdminForm, self).__init__(*args, **kwargs)

    class Meta(CustomUserForm.Meta):
        model = Admin
        fields = CustomUserForm.Meta.fields


class LeadSourceForm(FormSettings):
    def __init__(self, *args, **kwargs):
        super(LeadSourceForm, self).__init__(*args, **kwargs)

    class Meta:
        model = LeadSource
        fields = ['name', 'description', 'is_active']


class LeadForm(FormSettings):
    def __init__(self, *args, **kwargs):
        super(LeadForm, self).__init__(*args, **kwargs)
        # Hide the old industry field
        self.fields['industry'].widget = forms.HiddenInput()
        # Hide the is_graduated field (will be set automatically)
        self.fields['is_graduated'].widget = forms.HiddenInput()
        # Set up graduation year field
        self.fields['graduation_year'].widget = forms.NumberInput(attrs={'min': '1950', 'max': '2030'})
        # Make graduation fields optional
        self.fields['graduation_course'].required = False
        self.fields['graduation_college'].required = False
        self.fields['is_graduated'].required = False

    class Meta:
        model = Lead
        fields = [
            'first_name', 'last_name', 'email', 'phone', 'school_name', 'position', 
            'graduation_status', 'graduation_course', 'graduation_year', 'graduation_college',
            'course_interested', 'is_graduated', 'industry', 'source', 'status', 'priority', 'assigned_counsellor',
            'expected_value', 'notes', 'address', 'city', 'state', 'country', 
            'postal_code', 'website', 'linkedin', 'next_follow_up'
        ]
        widgets = {
            'next_follow_up': DateTimeInput(attrs={'type': 'datetime-local'}),
        }


class LeadActivityForm(FormSettings):
    def __init__(self, *args, **kwargs):
        super(LeadActivityForm, self).__init__(*args, **kwargs)

    class Meta:
        model = LeadActivity
        fields = [
            'activity_type', 'subject', 'description', 'outcome', 'next_action',
            'scheduled_date', 'duration', 'is_completed'
        ]
        widgets = {
            'scheduled_date': DateTimeInput(attrs={'type': 'datetime-local'}),
        }


class BusinessForm(FormSettings):
    def __init__(self, *args, **kwargs):
        super(BusinessForm, self).__init__(*args, **kwargs)

    class Meta:
        model = Business
        fields = [
            'title', 'description', 'value', 'status', 'start_date', 'end_date',
            'payment_terms', 'notes'
        ]
        widgets = {
            'start_date': DateInput(attrs={'type': 'date'}),
            'end_date': DateInput(attrs={'type': 'date'}),
        }


class LeadTransferForm(FormSettings):
    def __init__(self, *args, **kwargs):
        super(LeadTransferForm, self).__init__(*args, **kwargs)

    class Meta:
        model = LeadTransfer
        fields = ['to_counsellor', 'reason']


class CounsellorEditForm(CustomUserForm):
    employee_id = forms.CharField(max_length=20, required=True)
    department = forms.CharField(max_length=100, required=False)
    is_active = forms.BooleanField(required=False)
    
    def __init__(self, *args, **kwargs):
        # Extract counsellor instance if provided
        counsellor_instance = kwargs.pop('counsellor_instance', None)
        super(CounsellorEditForm, self).__init__(*args, **kwargs)
        
        # If we have a counsellor instance, populate the counsellor-specific fields
        if counsellor_instance:
            self.fields['employee_id'].initial = counsellor_instance.employee_id
            self.fields['department'].initial = counsellor_instance.department
            self.fields['is_active'].initial = counsellor_instance.is_active

    class Meta(CustomUserForm.Meta):
        model = CustomUser
        fields = CustomUserForm.Meta.fields


class LeadImportForm(forms.Form):
    file = forms.FileField(
        label='Select a file',
        help_text='Upload Excel (.xlsx) or CSV (.csv) file',
        widget=forms.FileInput(attrs={'accept': '.xlsx,.csv'})
    )
    source = forms.ModelChoiceField(
        queryset=LeadSource.objects.filter(is_active=True),
        required=True,
        label='Lead Source'
    )
    assigned_counsellor = forms.ModelChoiceField(
        queryset=Counsellor.objects.filter(is_active=True),
        required=False,
        label='Assign to Counsellor (Optional)'
    )


class NotificationCounsellorForm(FormSettings):
    def __init__(self, *args, **kwargs):
        super(NotificationCounsellorForm, self).__init__(*args, **kwargs)

    class Meta:
        model = NotificationCounsellor
        fields = ['counsellor', 'message']


class NotificationAdminForm(FormSettings):
    def __init__(self, *args, **kwargs):
        super(NotificationAdminForm, self).__init__(*args, **kwargs)

    class Meta:
        model = NotificationAdmin
        fields = ['message']


class CounsellorPerformanceForm(FormSettings):
    def __init__(self, *args, **kwargs):
        super(CounsellorPerformanceForm, self).__init__(*args, **kwargs)

    class Meta:
        model = CounsellorPerformance
        fields = [
            'counsellor', 'month', 'total_leads_assigned', 'total_leads_contacted',
            'total_leads_qualified', 'total_business_generated', 'conversion_rate',
            'average_response_time'
        ]
        widgets = {
            'month': DateInput(attrs={'type': 'date'}),
        }
