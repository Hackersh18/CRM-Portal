import json
from datetime import datetime, timedelta
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.shortcuts import (HttpResponseRedirect, get_object_or_404,
                              redirect, render)
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Count, Sum, Q
from django.utils import timezone

from .forms import *
from .models import *
import os
import requests
import re


def counsellor_home(request):
    """Counsellor Dashboard"""
    counsellor = get_object_or_404(Counsellor, admin=request.user)
    
    # My Leads Statistics
    my_leads = Lead.objects.filter(assigned_counsellor=counsellor)
    total_leads = my_leads.count()
    new_leads = my_leads.filter(status='NEW').count()
    contacted_leads = my_leads.filter(status='CONTACTED').count()
    qualified_leads = my_leads.filter(status='QUALIFIED').count()
    closed_won = my_leads.filter(status='CLOSED_WON').count()
    
    # My Business Statistics
    my_businesses = Business.objects.filter(counsellor=counsellor)
    total_business_value = my_businesses.filter(status='ACTIVE').aggregate(
        total=Sum('value'))['total'] or 0
    pending_businesses = my_businesses.filter(status='PENDING').count()
    active_businesses = my_businesses.filter(status='ACTIVE').count()
    
    # Recent Activities
    recent_activities = LeadActivity.objects.filter(
        counsellor=counsellor
    ).select_related('lead').order_by('-completed_date')[:10]
    
    # Upcoming Follow-ups
    upcoming_followups = Lead.objects.filter(
        assigned_counsellor=counsellor,
        next_follow_up__isnull=False,
        next_follow_up__gte=timezone.now()
    ).order_by('next_follow_up')[:5]
    
    # Lead Status Distribution for Charts
    lead_status_data = {
        'NEW': new_leads,
        'CONTACTED': contacted_leads,
        'QUALIFIED': qualified_leads,
        'CLOSED_WON': closed_won,
    }
    
    # Monthly Performance
    current_month = timezone.now().replace(day=1)
    monthly_leads = my_leads.filter(created_at__gte=current_month).count()
    monthly_business = my_businesses.filter(
        created_at__gte=current_month, status='ACTIVE'
    ).aggregate(total=Sum('value'))['total'] or 0
    
    context = {
        'page_title': "Counsellor Dashboard",
        'counsellor': counsellor,
        'total_leads': total_leads,
        'new_leads': new_leads,
        'contacted_leads': contacted_leads,
        'qualified_leads': qualified_leads,
        'closed_won': closed_won,
        'total_business_value': total_business_value,
        'pending_businesses': pending_businesses,
        'active_businesses': active_businesses,
        'recent_activities': recent_activities,
        'upcoming_followups': upcoming_followups,
        'lead_status_data': lead_status_data,
        'monthly_leads': monthly_leads,
        'monthly_business': monthly_business,
    }
    return render(request, 'counsellor_template/home_content.html', context)


def my_leads(request):
    """View assigned leads"""
    counsellor = get_object_or_404(Counsellor, admin=request.user)
    leads = Lead.objects.filter(assigned_counsellor=counsellor).select_related('source')
    
    # Filter by status if provided
    status_filter = request.GET.get('status')
    if status_filter:
        leads = leads.filter(status=status_filter)
    
    context = {
        'leads': leads,
        'page_title': 'My Leads'
    }
    return render(request, 'counsellor_template/my_leads.html', context)


def lead_detail(request, lead_id):
    """View lead details and activities"""
    counsellor = get_object_or_404(Counsellor, admin=request.user)
    lead = get_object_or_404(Lead, id=lead_id, assigned_counsellor=counsellor)
    activities = LeadActivity.objects.filter(lead=lead, counsellor=counsellor).order_by('-completed_date')
    
    context = {
        'lead': lead,
        'activities': activities,
        'page_title': f'Lead: {lead.first_name} {lead.last_name}'
    }
    return render(request, 'counsellor_template/lead_detail.html', context)


def add_lead_activity(request, lead_id):
    """Add activity for a lead"""
    counsellor = get_object_or_404(Counsellor, admin=request.user)
    lead = get_object_or_404(Lead, id=lead_id, assigned_counsellor=counsellor)
    form = LeadActivityForm(request.POST or None)
    
    context = {
        'form': form,
        'lead': lead,
        'page_title': 'Add Activity'
    }
    
    if request.method == 'POST':
        if form.is_valid():
            try:
                activity = form.save(commit=False)
                activity.lead = lead
                activity.counsellor = counsellor
                activity.save()
                
                # Update lead status and last contact date
                lead.last_contact_date = timezone.now()
                lead.save()
                
                messages.success(request, "Activity added successfully!")
                return redirect(reverse('lead_detail', kwargs={'lead_id': lead_id}))
            except Exception as e:
                messages.error(request, f"Could not add activity: {str(e)}")
        else:
            messages.error(request, "Please fill the form properly!")
    
    return render(request, 'counsellor_template/add_lead_activity.html', context)


def update_lead_status(request, lead_id):
    """Update lead status"""
    counsellor = get_object_or_404(Counsellor, admin=request.user)
    lead = get_object_or_404(Lead, id=lead_id, assigned_counsellor=counsellor)
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in dict(Lead.LEAD_STATUS):
            lead.status = new_status
            lead.save()
            messages.success(request, f"Lead status updated to {new_status}")
        else:
            messages.error(request, "Invalid status")
    
    return redirect(reverse('lead_detail', kwargs={'lead_id': lead_id}))


def create_business(request, lead_id):
    """Create business from lead"""
    counsellor = get_object_or_404(Counsellor, admin=request.user)
    lead = get_object_or_404(Lead, id=lead_id, assigned_counsellor=counsellor)
    form = BusinessForm(request.POST or None)
    
    context = {
        'form': form,
        'lead': lead,
        'page_title': 'Create Business'
    }
    
    if request.method == 'POST':
        if form.is_valid():
            try:
                business = form.save(commit=False)
                business.lead = lead
                business.counsellor = counsellor
                business.save()
                
                # Update lead status to CLOSED_WON
                lead.status = 'CLOSED_WON'
                lead.actual_value = business.value
                lead.save()
                
                messages.success(request, f"Business created successfully! Business ID: {business.business_id}")
                return redirect(reverse('my_businesses'))
            except Exception as e:
                messages.error(request, f"Could not create business: {str(e)}")
        else:
            messages.error(request, "Please fill the form properly!")
    
    return render(request, 'counsellor_template/create_business.html', context)


def my_businesses(request):
    """View my businesses"""
    counsellor = get_object_or_404(Counsellor, admin=request.user)
    businesses = Business.objects.filter(counsellor=counsellor).select_related('lead')
    
    # Filter by status if provided
    status_filter = request.GET.get('status')
    if status_filter:
        businesses = businesses.filter(status=status_filter)
    
    context = {
        'businesses': businesses,
        'page_title': 'My Businesses'
    }
    return render(request, 'counsellor_template/my_businesses.html', context)


def business_detail(request, business_id):
    """View business details"""
    counsellor = get_object_or_404(Counsellor, admin=request.user)
    business = get_object_or_404(Business, id=business_id, counsellor=counsellor)
    
    context = {
        'business': business,
        'page_title': f'Business: {business.title}'
    }
    return render(request, 'counsellor_template/business_detail.html', context)


def update_business_status(request, business_id):
    """Update business status"""
    counsellor = get_object_or_404(Counsellor, admin=request.user)
    business = get_object_or_404(Business, id=business_id, counsellor=counsellor)
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in dict(Business.BUSINESS_STATUS):
            business.status = new_status
            business.save()
            messages.success(request, f"Business status updated to {new_status}")
        else:
            messages.error(request, "Invalid status")
    
    return redirect(reverse('business_detail', kwargs={'business_id': business_id}))


def request_lead_transfer(request, lead_id):
    """Request lead transfer to another counsellor"""
    counsellor = get_object_or_404(Counsellor, admin=request.user)
    lead = get_object_or_404(Lead, id=lead_id, assigned_counsellor=counsellor)
    form = LeadTransferForm(request.POST or None)
    
    context = {
        'form': form,
        'lead': lead,
        'page_title': 'Request Lead Transfer'
    }
    
    if request.method == 'POST':
        if form.is_valid():
            try:
                transfer = form.save(commit=False)
                transfer.lead = lead
                transfer.from_counsellor = counsellor
                transfer.save()
                
                messages.success(request, "Transfer request submitted successfully!")
                return redirect(reverse('my_leads'))
            except Exception as e:
                messages.error(request, f"Could not submit transfer request: {str(e)}")
        else:
            messages.error(request, "Please fill the form properly!")
    
    return render(request, 'counsellor_template/request_lead_transfer.html', context)


def my_activities(request):
    """View my activities"""
    counsellor = get_object_or_404(Counsellor, admin=request.user)
    activities = LeadActivity.objects.filter(counsellor=counsellor).select_related('lead').order_by('-completed_date')
    
    # Filter by activity type if provided
    activity_type = request.GET.get('activity_type')
    if activity_type:
        activities = activities.filter(activity_type=activity_type)
    
    context = {
        'activities': activities,
        'page_title': 'My Activities'
    }
    return render(request, 'counsellor_template/my_activities.html', context)


def counsellor_view_profile(request):
    """Counsellor profile view"""
    counsellor = get_object_or_404(Counsellor, admin=request.user)
    
    # Performance statistics
    total_leads = counsellor.lead_set.count()
    total_business = counsellor.business_set.filter(status='ACTIVE').aggregate(
        total=Sum('value'))['total'] or 0
    try:
        conversion_rate = (counsellor.business_set.count() / total_leads * 100) if total_leads > 0 else 0
    except ZeroDivisionError:
        conversion_rate = 0
    
    context = {
        'counsellor': counsellor,
        'total_leads': total_leads,
        'total_business': total_business,
        'conversion_rate': conversion_rate,
        'page_title': 'My Profile'
    }
    return render(request, 'counsellor_template/counsellor_view_profile.html', context)


def counsellor_view_notifications(request):
    """View counsellor notifications"""
    counsellor = get_object_or_404(Counsellor, admin=request.user)
    notifications = NotificationCounsellor.objects.filter(counsellor=counsellor).order_by('-created_at')
    
    # Mark notifications as read
    if request.method == 'POST':
        notifications.update(is_read=True)
        messages.success(request, "All notifications marked as read!")
    
    context = {
        'notifications': notifications,
        'page_title': 'Notifications'
    }
    return render(request, 'counsellor_template/counsellor_view_notifications.html', context)


def counsellor_fcmtoken(request):
    """Update FCM token for notifications"""
    if request.method == 'POST':
        token = request.POST.get('token')
        if token:
            request.user.fcm_token = token
            request.user.save()
            return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'})


def get_my_analytics(request):
    """AJAX endpoint for counsellor analytics"""
    if request.method == 'GET':
        try:
            counsellor = get_object_or_404(Counsellor, admin=request.user)
            
            # Lead status distribution
            status_data = counsellor.lead_set.values('status').annotate(
                count=Count('id')
            ).values('status', 'count')
            
            # Monthly activity trend
            current_month = timezone.now().replace(day=1)
            monthly_activities = []
            for i in range(6):
                month_start = current_month - timedelta(days=30*i)
                month_end = month_start + timedelta(days=30)
                month_activities = counsellor.leadactivity_set.filter(
                    completed_date__gte=month_start,
                    completed_date__lt=month_end
                ).count()
                monthly_activities.append({
                    'month': month_start.strftime('%B'),
                    'activities': month_activities
                })
            
            return JsonResponse({
                'status_data': list(status_data),
                'monthly_activities': monthly_activities
            })
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    
    return JsonResponse({'error': 'Invalid request'}, status=400)


def schedule_follow_up(request, lead_id):
    """Schedule follow-up for a lead"""
    counsellor = get_object_or_404(Counsellor, admin=request.user)
    lead = get_object_or_404(Lead, id=lead_id, assigned_counsellor=counsellor)
    
    if request.method == 'POST':
        follow_up_date = request.POST.get('follow_up_date')
        if follow_up_date:
            try:
                lead.next_follow_up = datetime.fromisoformat(follow_up_date.replace('Z', '+00:00'))
                lead.save()
                messages.success(request, "Follow-up scheduled successfully!")
            except Exception as e:
                messages.error(request, f"Could not schedule follow-up: {str(e)}")
        else:
            messages.error(request, "Please provide a valid date")
    
    return redirect(reverse('lead_detail', kwargs={'lead_id': lead_id}))


def evaluate_conversion_score(request, lead_id):
    """Call AI API to assign an admission likelihood score (0-100) based on student profile."""
    counsellor = get_object_or_404(Counsellor, admin=request.user)
    lead = get_object_or_404(Lead, id=lead_id, assigned_counsellor=counsellor)

    prompt = (
        "You are an expert college admissions evaluator. Analyze this student's profile and predict their likelihood of successful enrollment.\n\n"
        "EVALUATION CRITERIA:\n"
        "1. Academic Background (30%): School reputation, graduation status, academic achievements\n"
        "2. Course Interest Alignment (25%): Clarity of course choice, relevance to background\n"
        "3. Engagement Level (20%): Lead status, priority, response to communications\n"
        "4. Financial Capability (15%): Expected value, payment history if any\n"
        "5. Profile Completeness (10%): Information quality, contact details, follow-up responsiveness\n\n"
        "SCORING GUIDELINES:\n"
        "- 90-100: Exceptional candidate, high-value, clear goals, strong background\n"
        "- 80-89: Very good candidate, likely to enroll, good academic profile\n"
        "- 70-79: Good candidate, moderate likelihood, some concerns\n"
        "- 60-69: Average candidate, uncertain enrollment, needs nurturing\n"
        "- 50-59: Below average, low likelihood, significant concerns\n"
        "- 0-49: Poor candidate, very unlikely to enroll\n\n"
        "STUDENT PROFILE:\n"
        f"Name: {lead.first_name} {lead.last_name}\n"
        f"12th School: {lead.school_name or 'Not provided'}\n"
        f"Graduation Status: {lead.graduation_status or 'Not provided'}\n"
        f"Graduation Course: {lead.graduation_course or 'Not provided'}\n"
        f"Graduation College: {lead.graduation_college or 'Not provided'}\n"
        f"Course Interested: {lead.course_interested or 'Not specified'}\n"
        f"Lead Status: {lead.status or 'Not set'}\n"
        f"Priority: {lead.priority or 'Not set'}\n"
        f"Expected Value: ${lead.expected_value or 0}\n"
        f"Notes: {lead.notes or 'No notes'}\n\n"
        "Based on the above criteria, provide ONLY an integer score from 0-100 representing the admission likelihood:"
    )

    score = None
    error_message = None

    try:
        openai_key = os.environ.get('OPENAI_API_KEY')
        if openai_key:
            # Simple call to OpenAI's responses API (fallback to a basic prompt-completion style)
            headers = {
                'Authorization': f'Bearer {openai_key}',
                'Content-Type': 'application/json'
            }
            body = {
                'model': 'gpt-4o-mini',
                'input': f"You are a college admissions scoring function. Read the student details and output ONLY an integer 0-100 for admission likelihood.\n\n{prompt}"
            }
            resp = requests.post('https://api.openai.com/v1/responses', headers=headers, json=body, timeout=20)
            if resp.status_code == 200:
                data = resp.json()
                text = (data.get('output_text') or '').strip()
                # Extract first integer 0-100
                import re
                m = re.search(r"\b(100|\d{1,2})\b", text)
                if m:
                    score = int(m.group(1))
        
        # Fallback heuristic if no key or failed to parse (college-focused)
        if score is None:
            # College-focused heuristic: base on priority, status, and academic factors
            base = {
                'NEW': 25,
                'CONTACTED': 40,
                'QUALIFIED': 55,
                'PROPOSAL_SENT': 70,
                'NEGOTIATION': 80,
                'CLOSED_WON': 95,
                'CLOSED_LOST': 5,
                'TRANSFERRED': 35,
            }.get(lead.status, 35)
            priority_bonus = {
                'LOW': -5,
                'MEDIUM': 0,
                'HIGH': 5,
                'URGENT': 10,
            }.get(lead.priority, 0)
            
            # Additional bonuses for college context
            academic_bonus = 0
            if lead.graduation_status == 'YES':
                academic_bonus += 10  # Graduates are more likely to enroll
            if lead.course_interested:
                academic_bonus += 5   # Clear course interest is positive
            if lead.school_name:
                academic_bonus += 5   # Having school info shows engagement
                
            score = max(0, min(100, base + priority_bonus + academic_bonus))
    except Exception as e:
        error_message = str(e)

    if score is not None:
        lead.conversion_score = score
        lead.save()
        messages.success(request, f"Admission likelihood score updated: {score}")
    else:
        messages.error(request, f"Could not evaluate admission score: {error_message or 'Unknown error'}")

    return redirect(reverse('lead_detail', kwargs={'lead_id': lead_id}))


def run_agentic_workflow(request, lead_id):
    """Agentic AI workflow for college admissions: enrich → score → route (with reasoning)."""
    counsellor = get_object_or_404(Counsellor, admin=request.user)
    lead = get_object_or_404(Lead, id=lead_id, assigned_counsellor=counsellor)

    openai_key = os.environ.get('OPENAI_API_KEY')
    headers = {'Authorization': f'Bearer {openai_key}', 'Content-Type': 'application/json'} if openai_key else None

    # Agent 1: Enrich student profile (academic background and interests)
    try:
        enrichment_prompt = (
            "You are an expert college admissions data enricher. Analyze the student's educational background and create a comprehensive academic profile.\n\n"
            "TASK: Create an academic profile summary and enrichment notes based on the student's educational background.\n\n"
            "STUDENT DATA:\n"
            f"Name: {lead.first_name} {lead.last_name}\n"
            f"12th School: {lead.school_name or 'Not provided'}\n"
            f"Graduation Status: {lead.graduation_status or 'Not provided'}\n"
            f"Graduation Course: {lead.graduation_course or 'Not provided'}\n"
            f"Graduation Year: {lead.graduation_year or 'Not provided'}\n"
            f"Graduation College: {lead.graduation_college or 'Not provided'}\n"
            f"Course Interested: {lead.course_interested or 'Not specified'}\n"
            f"Notes: {lead.notes or 'No additional notes'}\n\n"
            "ANALYSIS GUIDELINES:\n"
            "1. Academic Profile: Summarize educational background, achievements, and academic level\n"
            "2. Enrichment Notes: Identify strengths, potential concerns, and academic trajectory\n"
            "3. Consider school reputation, course relevance, and academic progression\n"
            "4. Note any gaps or inconsistencies in the academic journey\n\n"
            "RESPONSE FORMAT (JSON):\n"
            "{\n"
            '  "academic_profile": "Brief summary of academic background and level",\n'
            '  "enrichment_notes": "Key insights about academic strengths and considerations"\n'
            "}\n\n"
            "Provide the academic profile analysis:"
        )
        academic_profile = None
        enrichment_notes = None
        if headers:
            body = {'model': 'gpt-4o-mini', 'input': enrichment_prompt}
            r = requests.post('https://api.openai.com/v1/responses', headers=headers, json=body, timeout=20)
            if r.status_code == 200:
                txt = (r.json().get('output_text') or '').strip()
                m = re.search(r'academic_profile\s*[:\"]\s*([^\n\"]+)', txt, re.I)
                n = re.search(r'enrichment_notes\s*[:\"]\s*([^\n]+)', txt, re.I)
                if m:
                    academic_profile = m.group(1).strip()[:150]
                if n:
                    enrichment_notes = n.group(1).strip()
        if not academic_profile:
            # Heuristic fallback for academic profile
            if lead.graduation_status == 'YES':
                academic_profile = f"Graduate in {lead.graduation_course or 'General'} from {lead.graduation_college or 'College'}"
            else:
                academic_profile = f"12th Pass from {lead.school_name or 'School'}"
        if not enrichment_notes:
            enrichment_notes = 'Academic profile enriched based on educational background and interests.'
        lead.enriched_job_title = academic_profile  # Reusing this field for academic profile
        lead.enrichment_notes = enrichment_notes
        lead.save()
    except Exception as e:
        messages.warning(request, f"Academic enrichment failed; using fallback. {str(e)}")

    # Agent 2: Score admission likelihood (college-focused scoring)
    try:
        prompt = (
            "You are an expert college admissions evaluator. Analyze this student's profile and predict their likelihood of successful enrollment.\n\n"
            "EVALUATION CRITERIA:\n"
            "1. Academic Background (30%): School reputation, graduation status, academic achievements\n"
            "2. Course Interest Alignment (25%): Clarity of course choice, relevance to background\n"
            "3. Engagement Level (20%): Lead status, priority, response to communications\n"
            "4. Financial Capability (15%): Expected value, payment history if any\n"
            "5. Profile Completeness (10%): Information quality, contact details, follow-up responsiveness\n\n"
            "SCORING GUIDELINES:\n"
            "- 90-100: Exceptional candidate, high-value, clear goals, strong background\n"
            "- 80-89: Very good candidate, likely to enroll, good academic profile\n"
            "- 70-79: Good candidate, moderate likelihood, some concerns\n"
            "- 60-69: Average candidate, uncertain enrollment, needs nurturing\n"
            "- 50-59: Below average, low likelihood, significant concerns\n"
            "- 0-49: Poor candidate, very unlikely to enroll\n\n"
            "STUDENT PROFILE:\n"
            f"Name: {lead.first_name} {lead.last_name}\n"
            f"12th School: {lead.school_name or 'Not provided'}\n"
            f"Academic Profile: {lead.enriched_job_title or 'Not enriched'}\n"
            f"Graduation Status: {lead.graduation_status or 'Not provided'}\n"
            f"Graduation Course: {lead.graduation_course or 'Not provided'}\n"
            f"Graduation College: {lead.graduation_college or 'Not provided'}\n"
            f"Course Interested: {lead.course_interested or 'Not specified'}\n"
            f"Lead Status: {lead.status or 'Not set'}\n"
            f"Priority: {lead.priority or 'Not set'}\n"
            f"Expected Value: ${lead.expected_value or 0}\n"
            f"Notes: {lead.notes or 'No notes'}\n\n"
            "Based on the above criteria, provide ONLY an integer score from 0-100 representing the admission likelihood:"
        )
        score = None
        if headers:
            body = {'model': 'gpt-4o-mini', 'input': f"{prompt}"}
            r = requests.post('https://api.openai.com/v1/responses', headers=headers, json=body, timeout=20)
            if r.status_code == 200:
                txt = (r.json().get('output_text') or '').strip()
                m = re.search(r"\b(100|\d{1,2})\b", txt)
                if m:
                    score = int(m.group(1))
        if score is None:
            # College-focused heuristic scoring
            base = {
                'NEW': 25, 'CONTACTED': 40, 'QUALIFIED': 55,
                'PROPOSAL_SENT': 70, 'NEGOTIATION': 80,
                'CLOSED_WON': 95, 'CLOSED_LOST': 5, 'TRANSFERRED': 35,
            }.get(lead.status, 35)
            priority_bonus = {'LOW': -5, 'MEDIUM': 0, 'HIGH': 5, 'URGENT': 10}.get(lead.priority, 0)
            
            # Additional bonuses for college context
            if lead.graduation_status == 'YES':
                base += 10  # Graduates are more likely to enroll
            if lead.course_interested:
                base += 5   # Clear course interest is positive
            if lead.school_name:
                base += 5   # Having school info shows engagement
                
            score = max(0, min(100, base + priority_bonus))
        lead.conversion_score = score
        lead.save()
    except Exception as e:
        messages.warning(request, f"Admission scoring failed; used fallback. {str(e)}")

    # Agent 3: Route to appropriate academic counselor/department
    try:
        route_prompt = (
            "You are an expert college admissions routing AI. Analyze this student's profile and route them to the most appropriate academic department/counselor.\n\n"
            "ROUTING OPTIONS:\n"
            "- undergraduate_counselor: For 12th pass students seeking bachelor's degrees, general courses, or undecided majors\n"
            "- graduate_counselor: For graduates seeking master's, MBA, PhD, or advanced degrees\n"
            "- specialized_department: For high-value students in competitive fields (Engineering, Medicine, Law, Architecture, IIT/JEE prep)\n"
            "- senior_counselor: For high-priority cases, complex requirements, or students needing specialized attention\n\n"
            "ROUTING CRITERIA:\n"
            "1. Graduation Status: YES = graduate_counselor, NO = undergraduate_counselor (unless high-value)\n"
            "2. Course Complexity: Engineering/Medicine/Law = specialized_department\n"
            "3. Admission Score: 80+ = senior_counselor, 60-79 = specialized_department\n"
            "4. Expected Value: High value = senior_counselor or specialized_department\n"
            "5. Academic Profile: Advanced background = graduate_counselor\n\n"
            "STUDENT PROFILE:\n"
            f"Name: {lead.first_name} {lead.last_name}\n"
            f"12th School: {lead.school_name or 'Not provided'}\n"
            f"Graduation Status: {lead.graduation_status or 'Not provided'}\n"
            f"Graduation Course: {lead.graduation_course or 'Not provided'}\n"
            f"Graduation College: {lead.graduation_college or 'Not provided'}\n"
            f"Course Interested: {lead.course_interested or 'Not specified'}\n"
            f"Academic Profile: {lead.enriched_job_title or 'Not enriched'}\n"
            f"Admission Likelihood Score: {lead.conversion_score or 0}/100\n"
            f"Expected Value: ${lead.expected_value or 0}\n"
            f"Priority: {lead.priority or 'Not set'}\n"
            f"Status: {lead.status or 'Not set'}\n\n"
            "RESPONSE FORMAT:\n"
            "route=<option>\n"
            "reason=<brief explanation of routing decision>\n\n"
            "Analyze the profile and provide the most appropriate routing decision:"
        )
        routed_to = None
        routing_reason = None
        if headers:
            body = {'model': 'gpt-4o-mini', 'input': route_prompt}
            r = requests.post('https://api.openai.com/v1/responses', headers=headers, json=body, timeout=20)
            if r.status_code == 200:
                txt = (r.json().get('output_text') or '').lower()
                m = re.search(r'route\s*=\s*(undergraduate_counselor|graduate_counselor|specialized_department|senior_counselor)', txt)
                n = re.search(r'reason\s*=\s*(.+)', txt)
                if m:
                    routed_to = m.group(1)
                if n:
                    routing_reason = n.group(1).strip()
        if not routed_to:
            # College-focused heuristic routing
            score = lead.conversion_score or 0
            course = (lead.course_interested or '').lower()
            graduation_status = lead.graduation_status or 'NO'
            
            # Route based on graduation status and course complexity
            if graduation_status == 'YES':
                if any(word in course for word in ['mba', 'masters', 'phd', 'postgraduate', 'pg']):
                    routed_to = 'graduate_counselor'
                elif any(word in course for word in ['engineering', 'medicine', 'law', 'architecture']):
                    routed_to = 'specialized_department'
                else:
                    routed_to = 'graduate_counselor'
            else:
                if score >= 75 or any(word in course for word in ['engineering', 'medicine', 'law']):
                    routed_to = 'specialized_department'
                elif score >= 60:
                    routed_to = 'senior_counselor'
                else:
                    routed_to = 'undergraduate_counselor'
                    
        if not routing_reason:
            routing_reason = f"Assigned to {routed_to.replace('_', ' ')} based on admission score {lead.conversion_score}, course interest '{lead.course_interested}', and graduation status '{lead.graduation_status}'."
        lead.routed_to = routed_to
        lead.routing_reason = routing_reason[:1000]
        lead.save()
        # Execute the actual routing actions
        routing_success = execute_academic_routing(lead, routed_to, routing_reason)
        
        if routing_success:
            messages.success(request, f"Academic workflow complete. Routed to {routed_to.replace('_',' ')} and status updated.")
        else:
            messages.warning(request, f"Academic workflow completed but routing actions failed. Routed to {routed_to.replace('_',' ')}.")
    except Exception as e:
        messages.error(request, f"Academic routing failed: {str(e)}")

    return redirect(reverse('lead_detail', kwargs={'lead_id': lead_id}))


def execute_academic_routing(lead, routed_to, routing_reason):
    """
    Execute the actual routing actions based on the AI routing decision
    """
    from .models import NotificationCounsellor, NotificationAdmin
    
    try:
        # Get the current counsellor's admin for notifications
        current_admin = lead.assigned_counsellor.admin if lead.assigned_counsellor else None
        
        if routed_to == 'undergraduate_counselor':
            # Route to undergraduate counseling team
            # Update lead status and add routing note
            lead.status = 'QUALIFIED'  # Move to qualified status
            lead.priority = 'MEDIUM'   # Set appropriate priority
            if not lead.notes:
                lead.notes = f"Routed to Undergraduate Counseling: {routing_reason}"
            else:
                lead.notes += f"\n\nRouted to Undergraduate Counseling: {routing_reason}"
            lead.save()
            
            # Create notification for admin
            if current_admin:
                NotificationAdmin.objects.create(
                    admin=current_admin,
                    message=f"Student {lead.first_name} {lead.last_name} routed to Undergraduate Counseling for {lead.course_interested}"
                )
            
        elif routed_to == 'graduate_counselor':
            # Route to graduate counseling team
            lead.status = 'QUALIFIED'
            lead.priority = 'HIGH'  # Graduate students typically higher priority
            if not lead.notes:
                lead.notes = f"Routed to Graduate Counseling: {routing_reason}"
            else:
                lead.notes += f"\n\nRouted to Graduate Counseling: {routing_reason}"
            lead.save()
            
            # Create notification for admin
            if current_admin:
                NotificationAdmin.objects.create(
                    admin=current_admin,
                    message=f"Graduate student {lead.first_name} {lead.last_name} routed to Graduate Counseling for {lead.course_interested}"
                )
                
        elif routed_to == 'specialized_department':
            # Route to specialized academic department
            lead.status = 'PROPOSAL_SENT'  # Move to proposal stage
            lead.priority = 'HIGH'  # Specialized departments get high priority
            if not lead.notes:
                lead.notes = f"Routed to Specialized Department: {routing_reason}"
            else:
                lead.notes += f"\n\nRouted to Specialized Department: {routing_reason}"
            lead.save()
            
            # Create notification for admin
            if current_admin:
                NotificationAdmin.objects.create(
                    admin=current_admin,
                    message=f"Student {lead.first_name} {lead.last_name} routed to Specialized Department for {lead.course_interested} - High Priority"
                )
                
        elif routed_to == 'senior_counselor':
            # Route to senior counselor
            lead.status = 'NEGOTIATION'  # Move to negotiation stage
            lead.priority = 'URGENT'  # Senior counselor handles urgent cases
            if not lead.notes:
                lead.notes = f"Routed to Senior Counselor: {routing_reason}"
            else:
                lead.notes += f"\n\nRouted to Senior Counselor: {routing_reason}"
            lead.save()
            
            # Create notification for admin
            if current_admin:
                NotificationAdmin.objects.create(
                    admin=current_admin,
                    message=f"Student {lead.first_name} {lead.last_name} routed to Senior Counselor for {lead.course_interested} - Urgent Priority"
                )
        
        # Create a lead activity record for the routing action
        from .models import LeadActivity
        LeadActivity.objects.create(
            lead=lead,
            activity_type='ROUTED',
            description=f"AI routed student to {routed_to.replace('_', ' ').title()}: {routing_reason}",
            counsellor=lead.assigned_counsellor
        )
        
        return True
        
    except Exception as e:
        print(f"Error in execute_academic_routing: {e}")
        return False


def mark_lead_lost(request, lead_id):
    """Mark lead as lost"""
    counsellor = get_object_or_404(Counsellor, admin=request.user)
    lead = get_object_or_404(Lead, id=lead_id, assigned_counsellor=counsellor)
    
    if request.method == 'POST':
        reason = request.POST.get('reason', '')
        lead.status = 'CLOSED_LOST'
        lead.notes += f"\n\nLost Reason: {reason}"
        lead.save()
        messages.success(request, "Lead marked as lost")
    
    return redirect(reverse('lead_detail', kwargs={'lead_id': lead_id}))
