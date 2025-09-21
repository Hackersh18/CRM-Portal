import json
import pandas as pd
from datetime import datetime, timedelta
from django.contrib import messages
from django.core.files.storage import FileSystemStorage
from django.http import HttpResponse, JsonResponse
from django.shortcuts import (HttpResponse, HttpResponseRedirect,
                              get_object_or_404, redirect, render)
from django.templatetags.static import static
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import UpdateView
from django.contrib.auth.hashers import make_password
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum, Avg, Q, Case, When, Value, DecimalField
from django.utils import timezone

from .forms import *
from .models import *


def admin_home(request):
    """Admin Dashboard with comprehensive CRM analytics"""
    
    try:
        # Basic Statistics
        total_counsellors = Counsellor.objects.filter(is_active=True).count()
        total_leads = Lead.objects.count()
        total_business = Business.objects.filter(status='ACTIVE').aggregate(
            total=Sum('value'))['total'] or 0
        
        # Lead Statistics
        new_leads = Lead.objects.filter(status='NEW').count()
        contacted_leads = Lead.objects.filter(status='CONTACTED').count()
        qualified_leads = Lead.objects.filter(status='QUALIFIED').count()
        closed_won = Lead.objects.filter(status='CLOSED_WON').count()
        closed_lost = Lead.objects.filter(status='CLOSED_LOST').count()
        
        # Monthly Performance
        current_month = timezone.now().replace(day=1)
        monthly_leads = Lead.objects.filter(created_at__gte=current_month).count()
        monthly_business = Business.objects.filter(
            created_at__gte=current_month, status='ACTIVE'
        ).aggregate(total=Sum('value'))['total'] or 0
        
        # Lead Source Distribution
        lead_sources = LeadSource.objects.annotate(
            lead_count=Count('lead')
        ).values('name', 'lead_count')
        
        # Counsellor Performance
        counsellor_performance = Counsellor.objects.filter(is_active=True).annotate(
            total_leads=Count('lead'),
            total_business=Sum('business__value'),
            conversion_rate=Case(
                When(total_leads=0, then=Value(0.0)),
                default=Count('business') * 100.0 / Count('lead'),
                output_field=DecimalField()
            )
        ).values('admin__first_name', 'admin__last_name', 'total_leads', 'total_business', 'conversion_rate')
        
        # Recent Activities
        recent_activities = LeadActivity.objects.select_related(
            'lead', 'counsellor__admin'
        ).order_by('-completed_date')[:10]
        
        # Lead Status Distribution for Charts
        lead_status_data = {
            'NEW': new_leads,
            'CONTACTED': contacted_leads,
            'QUALIFIED': qualified_leads,
            'CLOSED_WON': closed_won,
            'CLOSED_LOST': closed_lost
        }
        
        # Monthly Trend Data (Last 6 months)
        monthly_trend = []
        for i in range(6):
            month_start = current_month - timedelta(days=30*i)
            month_end = month_start + timedelta(days=30)
            month_leads = Lead.objects.filter(
                created_at__gte=month_start,
                created_at__lt=month_end
            ).count()
            month_business = Business.objects.filter(
                created_at__gte=month_start,
                created_at__lt=month_end,
                status='ACTIVE'
            ).aggregate(total=Sum('value'))['total'] or 0
            monthly_trend.append({
                'month': month_start.strftime('%B %Y'),
                'leads': month_leads,
                'business': float(month_business)
            })
        
    except Exception as e:
        # Fallback values if there's an error
        total_counsellors = 0
        total_leads = 0
        total_business = 0
        new_leads = 0
        contacted_leads = 0
        qualified_leads = 0
        closed_won = 0
        closed_lost = 0
        monthly_leads = 0
        monthly_business = 0
        lead_sources = []
        counsellor_performance = []
        recent_activities = []
        lead_status_data = {}
        monthly_trend = []
    
    context = {
        'page_title': "CRM Admin Dashboard",
        'total_counsellors': total_counsellors,
        'total_leads': total_leads,
        'total_business': total_business,
        'new_leads': new_leads,
        'contacted_leads': contacted_leads,
        'qualified_leads': qualified_leads,
        'closed_won': closed_won,
        'closed_lost': closed_lost,
        'monthly_leads': monthly_leads,
        'monthly_business': monthly_business,
        'lead_sources': list(lead_sources),
        'counsellor_performance': list(counsellor_performance),
        'recent_activities': recent_activities,
        'lead_status_data': lead_status_data,
        'monthly_trend': monthly_trend,
    }
    return render(request, 'admin_template/home_content.html', context)


def add_counsellor(request):
    """Add new counsellor"""
    form = CounsellorForm(request.POST or None, request.FILES or None)
    context = {'form': form, 'page_title': 'Add Counsellor'}
    if request.method == 'POST':
        if form.is_valid():
            try:
                # Get the form data
                employee_id = form.cleaned_data['employee_id']
                department = form.cleaned_data.get('department', '')
                
                # Create the user first
                user = form.save(commit=False)
                user.user_type = '2'  # Counsellor
                user.save()
                
                # Create the counsellor profile
                Counsellor.objects.create(
                    admin=user,
                    employee_id=employee_id,
                    department=department
                )
                
                messages.success(request, "Counsellor added successfully!")
                return redirect(reverse('manage_counsellors'))
            except Exception as e:
                messages.error(request, f"Could not add counsellor: {str(e)}")
        else:
            messages.error(request, "Please fill the form properly!")
    return render(request, 'admin_template/add_counsellor.html', context)


def manage_counsellors(request):
    """Manage all counsellors"""
    counsellors = Counsellor.objects.select_related('admin').all()
    context = {
        'counsellors': counsellors,
        'page_title': 'Manage Counsellors'
    }
    return render(request, 'admin_template/manage_counsellors.html', context)


def edit_counsellor(request, counsellor_id):
    """Edit counsellor details"""
    counsellor = get_object_or_404(Counsellor, id=counsellor_id)
    form = CounsellorEditForm(
        request.POST or None, 
        request.FILES or None, 
        instance=counsellor.admin,
        counsellor_instance=counsellor
    )
    context = {
        'form': form,
        'counsellor': counsellor,
        'page_title': 'Edit Counsellor'
    }
    if request.method == 'POST':
        if form.is_valid():
            try:
                # Save the CustomUser (admin) fields
                user = form.save()
                
                # Update the Counsellor-specific fields
                counsellor.employee_id = form.cleaned_data['employee_id']
                counsellor.department = form.cleaned_data['department']
                counsellor.is_active = form.cleaned_data['is_active']
                counsellor.save()
                
                messages.success(request, "Counsellor updated successfully!")
                return redirect(reverse('manage_counsellors'))
            except Exception as e:
                messages.error(request, f"Could not update counsellor: {str(e)}")
        else:
            messages.error(request, "Please fill the form properly!")
    return render(request, 'admin_template/edit_counsellor.html', context)


def delete_counsellor(request, counsellor_id):
    """Delete counsellor"""
    counsellor = get_object_or_404(Counsellor, id=counsellor_id)
    try:
        counsellor.admin.delete()
        messages.success(request, "Counsellor deleted successfully!")
    except Exception as e:
        messages.error(request, f"Could not delete counsellor: {str(e)}")
    return redirect(reverse('manage_counsellors'))


def manage_leads(request):
    """Manage all leads"""
    leads = Lead.objects.select_related('source', 'assigned_counsellor__admin').all()
    context = {
        'leads': leads,
        'page_title': 'Manage Leads'
    }
    return render(request, 'admin_template/manage_leads.html', context)


def add_lead(request):
    """Add new lead manually"""
    form = LeadForm(request.POST or None)
    context = {'form': form, 'page_title': 'Add Lead'}
    if request.method == 'POST':
        if form.is_valid():
            try:
                lead = form.save()
                messages.success(request, f"Lead added successfully! Lead ID: {lead.lead_id}")
                return redirect(reverse('manage_leads'))
            except Exception as e:
                messages.error(request, f"Could not add lead: {str(e)}")
        else:
            messages.error(request, "Please fill the form properly!")
    return render(request, 'admin_template/add_lead.html', context)


def edit_lead(request, lead_id):
    """Edit lead details"""
    lead = get_object_or_404(Lead, id=lead_id)
    form = LeadForm(request.POST or None, instance=lead)
    context = {
        'form': form,
        'lead': lead,
        'page_title': 'Edit Lead'
    }
    if request.method == 'POST':
        if form.is_valid():
            try:
                form.save()
                messages.success(request, "Lead updated successfully!")
                return redirect(reverse('manage_leads'))
            except Exception as e:
                messages.error(request, f"Could not update lead: {str(e)}")
        else:
            messages.error(request, "Please fill the form properly!")
    return render(request, 'admin_template/edit_lead.html', context)


def delete_lead(request, lead_id):
    """Delete lead"""
    lead = get_object_or_404(Lead, id=lead_id)
    try:
        lead.delete()
        messages.success(request, "Lead deleted successfully!")
    except Exception as e:
        messages.error(request, f"Could not delete lead: {str(e)}")
    return redirect(reverse('manage_leads'))


def import_leads(request):
    """Import leads from Excel/CSV file with automatic assignment options"""
    form = LeadImportForm(request.POST or None, request.FILES or None)
    context = {'form': form, 'page_title': 'Import Leads'}
    
    if request.method == 'POST':
        if form.is_valid():
            try:
                file = form.cleaned_data['file']
                source = form.cleaned_data['source']
                assigned_counsellor = form.cleaned_data.get('assigned_counsellor')
                auto_assign = request.POST.get('auto_assign', False)
                assignment_method = request.POST.get('assignment_method', 'round_robin')
                
                # Read the file
                if file.name.endswith('.csv'):
                    df = pd.read_csv(file)
                else:
                    df = pd.read_excel(file)
                
                success_count = 0
                error_count = 0
                imported_leads = []
                
                for index, row in df.iterrows():
                    try:
                        # Create lead from row data
                        graduation_status = row.get('graduation_status', 'NO')
                        
                        # Handle graduation fields based on status
                        if graduation_status == 'NO':
                            graduation_course = 'Not Applicable'
                            graduation_college = 'Not Applicable'
                        else:
                            # Handle NaN values from pandas
                            graduation_course = row.get('graduation_course', 'Not Specified')
                            graduation_college = row.get('graduation_college', 'Not Specified')
                            
                            # Convert NaN to None/empty string
                            if pd.isna(graduation_course):
                                graduation_course = 'Not Specified'
                            if pd.isna(graduation_college):
                                graduation_college = 'Not Specified'
                        
                        # Handle graduation_year NaN values
                        graduation_year = row.get('graduation_year', None)
                        if pd.isna(graduation_year):
                            graduation_year = None
                        
                        lead_data = {
                            'first_name': row.get('first_name', ''),
                            'last_name': row.get('last_name', ''),
                            'email': row.get('email', ''),
                            'phone': str(row.get('phone', '')),
                            'school_name': row.get('School Name', ''),  # Map School Name to school_name field
                            'graduation_status': graduation_status,
                            'graduation_course': graduation_course,
                            'graduation_year': graduation_year,
                            'graduation_college': graduation_college,
                            'course_interested': row.get('course_interested', ''),
                            'industry': row.get('industry', ''),  # Keep for backward compatibility
                            'source': source,
                            'assigned_counsellor': assigned_counsellor,
                            'expected_value': row.get('expected_value', 0),
                        }
                        
                        lead = Lead.objects.create(**lead_data)
                        imported_leads.append(lead)
                        success_count += 1
                        
                    except Exception as e:
                        error_count += 1
                        # Log the specific error for debugging
                        print(f"Error importing row {index + 1}: {str(e)}")
                        print(f"Row data: {dict(row)}")
                        continue
                
                # Auto-assign leads if requested
                if auto_assign and imported_leads and not assigned_counsellor:
                    try:
                        active_counsellors = Counsellor.objects.filter(is_active=True)
                        if active_counsellors.exists():
                            unassigned_leads = [lead for lead in imported_leads if not lead.assigned_counsellor]
                            
                            if assignment_method == 'round_robin':
                                _assign_round_robin(unassigned_leads, active_counsellors)
                            elif assignment_method == 'workload_balanced':
                                _assign_workload_balanced(unassigned_leads, active_counsellors)
                            elif assignment_method == 'performance_based':
                                _assign_performance_based(unassigned_leads, active_counsellors)
                            elif assignment_method == 'specialization_based':
                                _assign_specialization_based(unassigned_leads, active_counsellors)
                            
                            messages.success(request, f"Successfully imported {success_count} leads and auto-assigned them using {assignment_method.replace('_', ' ').title()} method. {error_count} errors occurred.")
                        else:
                            messages.warning(request, f"Successfully imported {success_count} leads but no active counsellors found for auto-assignment. {error_count} errors occurred.")
                    except Exception as e:
                        messages.warning(request, f"Successfully imported {success_count} leads but auto-assignment failed: {str(e)}. {error_count} errors occurred.")
                else:
                    if error_count > 0:
                        messages.warning(request, f"Successfully imported {success_count} leads. {error_count} rows had errors and were skipped.")
                    else:
                        messages.success(request, f"Successfully imported {success_count} leads.")
                
                return redirect(reverse('manage_leads'))
                
            except Exception as e:
                messages.error(request, f"Import failed: {str(e)}")
        else:
            messages.error(request, "Please fill the form properly!")
    
    return render(request, 'admin_template/import_leads.html', context)


def assign_leads_to_counsellors(request):
    """Automatically assign unassigned leads to counsellors using multiple strategies"""
    if request.method == 'POST':
        try:
            assignment_method = request.POST.get('assignment_method', 'round_robin')
            unassigned_leads = Lead.objects.filter(assigned_counsellor__isnull=True)
            active_counsellors = Counsellor.objects.filter(is_active=True)
            
            if not active_counsellors.exists():
                messages.error(request, "No active counsellors found!")
                return redirect(reverse('manage_leads'))
            
            if not unassigned_leads.exists():
                messages.info(request, "No unassigned leads found!")
                return redirect(reverse('manage_leads'))
            
            assigned_count = 0
            
            if assignment_method == 'round_robin':
                assigned_count = _assign_round_robin(unassigned_leads, active_counsellors)
            elif assignment_method == 'workload_balanced':
                assigned_count = _assign_workload_balanced(unassigned_leads, active_counsellors)
            elif assignment_method == 'performance_based':
                assigned_count = _assign_performance_based(unassigned_leads, active_counsellors)
            elif assignment_method == 'specialization_based':
                assigned_count = _assign_specialization_based(unassigned_leads, active_counsellors)
            else:
                assigned_count = _assign_round_robin(unassigned_leads, active_counsellors)
            
            messages.success(request, f"Successfully assigned {assigned_count} leads using {assignment_method.replace('_', ' ').title()} method!")
            return redirect(reverse('assign_leads_to_counsellors'))
            
        except Exception as e:
            messages.error(request, f"Assignment failed: {str(e)}")
    
    # GET request - show assignment page with workload summary
    try:
        from datetime import datetime, timedelta
        
        # Get unassigned leads count
        unassigned_count = Lead.objects.filter(assigned_counsellor__isnull=True).count()
        active_counsellors_count = Counsellor.objects.filter(is_active=True).count()
        
        # Calculate average leads per counsellor
        total_assigned_leads = Lead.objects.filter(assigned_counsellor__isnull=False).count()
        avg_leads_per_counsellor = round(total_assigned_leads / active_counsellors_count, 1) if active_counsellors_count > 0 else 0
        
        # Find oldest unassigned lead
        oldest_unassigned = Lead.objects.filter(assigned_counsellor__isnull=True).order_by('created_at').first()
        oldest_unassigned_days = 0
        if oldest_unassigned:
            oldest_unassigned_days = (datetime.now().replace(tzinfo=None) - oldest_unassigned.created_at.replace(tzinfo=None)).days
        
        # Get counsellor workload data
        counsellor_workload = []
        for counsellor in Counsellor.objects.filter(is_active=True):
            lead_count = Lead.objects.filter(assigned_counsellor=counsellor).count()
            
            # Determine capacity and workload status
            if lead_count <= 10:
                capacity = "Low (≤10 leads)"
                workload_status = "LOW"
            elif lead_count <= 25:
                capacity = "Medium (11-25 leads)"
                workload_status = "MEDIUM"
            else:
                capacity = "High (26+ leads)"
                workload_status = "HIGH"
            
            counsellor_workload.append({
                'admin': counsellor.admin,
                'department': counsellor.department,
                'lead_count': lead_count,
                'capacity': capacity,
                'workload_status': workload_status
            })
        
        context = {
            'page_title': 'Assign Leads to Counsellors',
            'unassigned_count': unassigned_count,
            'active_counsellors_count': active_counsellors_count,
            'avg_leads_per_counsellor': avg_leads_per_counsellor,
            'oldest_unassigned_days': oldest_unassigned_days,
            'counsellor_workload': counsellor_workload
        }
        
        return render(request, 'admin_template/assign_leads.html', context)
        
    except Exception as e:
        messages.error(request, f"Error loading assignment page: {str(e)}")
        return redirect(reverse('manage_leads'))


def _assign_round_robin(unassigned_leads, active_counsellors):
    """Round-robin assignment - distribute leads evenly"""
    counsellor_list = list(active_counsellors)
    assigned_count = 0
    
    for i, lead in enumerate(unassigned_leads):
        counsellor = counsellor_list[i % len(counsellor_list)]
        lead.assigned_counsellor = counsellor
        lead.save()
        assigned_count += 1
    
    return assigned_count


def _assign_workload_balanced(unassigned_leads, active_counsellors):
    """Workload-balanced assignment - assign to counsellors with fewer leads"""
    assigned_count = 0
    
    # Get current workload for each counsellor
    counsellor_workload = {}
    for counsellor in active_counsellors:
        lead_count = Lead.objects.filter(assigned_counsellor=counsellor).count()
        counsellor_workload[counsellor.id] = {
            'counsellor': counsellor,
            'lead_count': lead_count
        }
    
    # Sort counsellors by workload (ascending)
    sorted_counsellors = sorted(counsellor_workload.values(), key=lambda x: x['lead_count'])
    
    for lead in unassigned_leads:
        # Assign to counsellor with least workload
        counsellor = sorted_counsellors[0]['counsellor']
        lead.assigned_counsellor = counsellor
        lead.save()
        
        # Update workload count
        sorted_counsellors[0]['lead_count'] += 1
        
        # Re-sort to maintain balance
        sorted_counsellors.sort(key=lambda x: x['lead_count'])
        assigned_count += 1
    
    return assigned_count


def _assign_performance_based(unassigned_leads, active_counsellors):
    """Performance-based assignment - assign to top-performing counsellors"""
    assigned_count = 0
    
    # Calculate performance metrics for each counsellor
    counsellor_performance = {}
    for counsellor in active_counsellors:
        total_leads = Lead.objects.filter(assigned_counsellor=counsellor).count()
        closed_won = Lead.objects.filter(assigned_counsellor=counsellor, status='CLOSED_WON').count()
        try:
            conversion_rate = (closed_won / total_leads * 100) if total_leads > 0 else 0
        except ZeroDivisionError:
            conversion_rate = 0
        
        counsellor_performance[counsellor.id] = {
            'counsellor': counsellor,
            'conversion_rate': conversion_rate,
            'total_leads': total_leads
        }
    
    # Sort by conversion rate (descending) and then by total leads (ascending)
    sorted_counsellors = sorted(
        counsellor_performance.values(),
        key=lambda x: (-x['conversion_rate'], x['total_leads'])
    )
    
    for lead in unassigned_leads:
        # Assign to top-performing counsellor
        counsellor = sorted_counsellors[0]['counsellor']
        lead.assigned_counsellor = counsellor
        lead.save()
        
        # Update lead count
        sorted_counsellors[0]['total_leads'] += 1
        
        # Re-sort to maintain performance-based order
        sorted_counsellors.sort(key=lambda x: (-x['conversion_rate'], x['total_leads']))
        assigned_count += 1
    
    return assigned_count


def _assign_specialization_based(unassigned_leads, active_counsellors):
    """Specialization-based assignment - assign based on counsellor expertise"""
    assigned_count = 0
    
    # Get counsellor specializations (based on department and past performance)
    counsellor_specializations = {}
    for counsellor in active_counsellors:
        # Get counsellor's success rate by industry/source
        industry_success = {}
        source_success = {}
        
        counsellor_leads = Lead.objects.filter(assigned_counsellor=counsellor)
        for lead in counsellor_leads:
            if lead.industry:
                if lead.industry not in industry_success:
                    industry_success[lead.industry] = {'total': 0, 'won': 0}
                industry_success[lead.industry]['total'] += 1
                if lead.status == 'CLOSED_WON':
                    industry_success[lead.industry]['won'] += 1
            
            if lead.source:
                if lead.source.id not in source_success:
                    source_success[lead.source.id] = {'total': 0, 'won': 0}
                source_success[lead.source.id]['total'] += 1
                if lead.status == 'CLOSED_WON':
                    source_success[lead.source.id]['won'] += 1
        
        counsellor_specializations[counsellor.id] = {
            'counsellor': counsellor,
            'industry_success': industry_success,
            'source_success': source_success,
            'current_workload': counsellor_leads.count()
        }
    
    for lead in unassigned_leads:
        best_counsellor = None
        best_score = -1
        
        for counsellor_data in counsellor_specializations.values():
            score = 0
            
            # Graduation Status expertise bonus
            if lead.industry and lead.industry in counsellor_data['industry_success']:
                success_rate = counsellor_data['industry_success'][lead.industry]['won'] / counsellor_data['industry_success'][lead.industry]['total']
                score += success_rate * 100
            
            # Source expertise bonus
            if lead.source and lead.source.id in counsellor_data['source_success']:
                success_rate = counsellor_data['source_success'][lead.source.id]['won'] / counsellor_data['source_success'][lead.source.id]['total']
                score += success_rate * 50
            
            # Workload penalty (prefer counsellors with fewer leads)
            workload_penalty = counsellor_data['current_workload'] * 2
            score -= workload_penalty
            
            if score > best_score:
                best_score = score
                best_counsellor = counsellor_data['counsellor']
        
        if best_counsellor:
            lead.assigned_counsellor = best_counsellor
            lead.save()
            
            # Update workload
            for counsellor_data in counsellor_specializations.values():
                if counsellor_data['counsellor'] == best_counsellor:
                    counsellor_data['current_workload'] += 1
                    break
            
            assigned_count += 1
    
    return assigned_count


def transfer_lead(request, lead_id):
    """Transfer lead to another counsellor"""
    lead = get_object_or_404(Lead, id=lead_id)
    form = LeadTransferForm(request.POST or None)
    context = {
        'form': form,
        'lead': lead,
        'page_title': 'Transfer Lead'
    }
    
    if request.method == 'POST':
        if form.is_valid():
            try:
                transfer = form.save(commit=False)
                transfer.lead = lead
                transfer.from_counsellor = lead.assigned_counsellor
                transfer.admin_approved = True
                transfer.approved_by = request.user
                transfer.approved_at = timezone.now()
                transfer.save()
                
                # Update lead assignment
                lead.previous_counsellor = lead.assigned_counsellor
                lead.assigned_counsellor = transfer.to_counsellor
                lead.status = 'TRANSFERRED'
                lead.save()
                
                messages.success(request, f"Lead transferred to {transfer.to_counsellor.admin.first_name}")
                return redirect(reverse('manage_leads'))
                
            except Exception as e:
                messages.error(request, f"Transfer failed: {str(e)}")
        else:
            messages.error(request, "Please fill the form properly!")
    
    return render(request, 'admin_template/transfer_lead.html', context)


def manage_lead_sources(request):
    """Manage lead sources"""
    sources = LeadSource.objects.all().prefetch_related('lead_set')
    context = {
        'sources': sources,
        'page_title': 'Manage Lead Sources'
    }
    return render(request, 'admin_template/manage_lead_sources.html', context)


def add_lead_source(request):
    """Add new lead source"""
    form = LeadSourceForm(request.POST or None)
    context = {'form': form, 'page_title': 'Add Lead Source'}
    if request.method == 'POST':
        if form.is_valid():
            try:
                form.save()
                messages.success(request, "Lead source added successfully!")
                return redirect(reverse('manage_lead_sources'))
            except Exception as e:
                messages.error(request, f"Could not add lead source: {str(e)}")
        else:
            messages.error(request, "Please fill the form properly!")
    return render(request, 'admin_template/add_lead_source.html', context)


def edit_lead_source(request, source_id):
    """Edit lead source"""
    lead_source = get_object_or_404(LeadSource, id=source_id)
    form = LeadSourceForm(request.POST or None, instance=lead_source)
    context = {'form': form, 'lead_source': lead_source, 'page_title': 'Edit Lead Source'}
    if request.method == 'POST':
        if form.is_valid():
            try:
                form.save()
                messages.success(request, "Lead source updated successfully!")
                return redirect(reverse('manage_lead_sources'))
            except Exception as e:
                messages.error(request, f"Could not update lead source: {str(e)}")
        else:
            messages.error(request, "Please fill the form properly!")
    return render(request, 'admin_template/edit_lead_source.html', context)


def delete_lead_source(request, source_id):
    """Delete lead source"""
    lead_source = get_object_or_404(LeadSource, id=source_id)
    try:
        lead_source.delete()
        messages.success(request, "Lead source deleted successfully!")
    except Exception as e:
        messages.error(request, f"Could not delete lead source: {str(e)}")
    return redirect(reverse('manage_lead_sources'))


def manage_businesses(request):
    """Manage all businesses"""
    businesses = Business.objects.select_related('lead', 'counsellor__admin').all()
    context = {
        'businesses': businesses,
        'page_title': 'Manage Businesses'
    }
    return render(request, 'admin_template/manage_businesses.html', context)


def counsellor_performance(request):
    """View counsellor performance analytics"""
    counsellors = Counsellor.objects.filter(is_active=True)
    performance_data = []
    
    for counsellor in counsellors:
        # Get monthly performance
        current_month = timezone.now().replace(day=1)
        monthly_performance = CounsellorPerformance.objects.filter(
            counsellor=counsellor,
            month=current_month
        ).first()
        
        if not monthly_performance:
            # Calculate performance if not exists
            monthly_leads = counsellor.lead_set.filter(created_at__gte=current_month).count()
            monthly_business = counsellor.business_set.filter(
                created_at__gte=current_month, status='ACTIVE'
            ).aggregate(total=Sum('value'))['total'] or 0
            
            try:
                conversion_rate = monthly_business / monthly_leads * 100 if monthly_leads > 0 else 0
            except ZeroDivisionError:
                conversion_rate = 0
                
            monthly_performance = CounsellorPerformance.objects.create(
                counsellor=counsellor,
                month=current_month,
                total_leads_assigned=monthly_leads,
                total_business_generated=monthly_business,
                conversion_rate=conversion_rate
            )
        
        performance_data.append({
            'counsellor': counsellor,
            'performance': monthly_performance
        })
    
    context = {
        'performance_data': performance_data,
        'page_title': 'Counsellor Performance'
    }
    return render(request, 'admin_template/counsellor_performance.html', context)


def send_counsellor_notification(request):
    """Send notification to counsellors"""
    form = NotificationCounsellorForm(request.POST or None)
    context = {'form': form, 'page_title': 'Send Notification'}
    if request.method == 'POST':
        if form.is_valid():
            try:
                form.save()
                messages.success(request, "Notification sent successfully!")
                return redirect(reverse('admin_home'))
            except Exception as e:
                messages.error(request, f"Could not send notification: {str(e)}")
        else:
            messages.error(request, "Please fill the form properly!")
    return render(request, 'admin_template/send_counsellor_notification.html', context)


def admin_view_profile(request):
    """Admin profile view"""
    admin = get_object_or_404(Admin, admin=request.user)
    context = {
        'admin': admin,
        'page_title': 'Admin Profile'
    }
    return render(request, 'admin_template/admin_view_profile.html', context)


def admin_view_notifications(request):
    """View admin notifications"""
    notifications = NotificationAdmin.objects.all().order_by('-created_at')
    context = {
        'notifications': notifications,
        'page_title': 'Notifications'
    }
    return render(request, 'admin_template/admin_view_notifications.html', context)


def get_lead_analytics(request):
    """AJAX endpoint for lead analytics"""
    if request.method == 'GET':
        try:
            # Lead status distribution
            status_data = Lead.objects.values('status').annotate(
                count=Count('id')
            ).values('status', 'count')
            
            # Monthly trend
            current_month = timezone.now().replace(day=1)
            monthly_data = []
            for i in range(6):
                month_start = current_month - timedelta(days=30*i)
                month_end = month_start + timedelta(days=30)
                month_leads = Lead.objects.filter(
                    created_at__gte=month_start,
                    created_at__lt=month_end
                ).count()
                monthly_data.append({
                    'month': month_start.strftime('%B'),
                    'leads': month_leads
                })
            
            return JsonResponse({
                'status_data': list(status_data),
                'monthly_data': monthly_data
            })
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    
    return JsonResponse({'error': 'Invalid request'}, status=400)


@login_required(login_url='login')
def download_import_template(request, file_type):
    """Download sample import template files"""
    import os
    from django.http import FileResponse
    from django.conf import settings
    
    if file_type == 'excel':
        file_path = os.path.join(settings.BASE_DIR, 'main_app', 'static', 'templates', 'lead_import_template.xlsx')
        content_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        filename = 'lead_import_template.xlsx'
    elif file_type == 'csv':
        file_path = os.path.join(settings.BASE_DIR, 'main_app', 'static', 'templates', 'lead_import_template.csv')
        content_type = 'text/csv'
        filename = 'lead_import_template.csv'
    else:
        return HttpResponse('Invalid file type', status=400)
    
    if os.path.exists(file_path):
        response = FileResponse(open(file_path, 'rb'), content_type=content_type)
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
    else:
        return HttpResponse('Template file not found', status=404)


@login_required(login_url='login')
def admin_view_lead(request, lead_id):
    """Admin view to display detailed lead information"""
    try:
        lead = get_object_or_404(Lead, id=lead_id)
        
        # Get lead activities
        activities = LeadActivity.objects.filter(lead=lead).order_by('-scheduled_date')
        
        # Get related business if exists
        business = Business.objects.filter(lead=lead).first()
        
        context = {
            'lead': lead,
            'activities': activities,
            'business': business,
            'page_title': f'Lead Details - {lead.first_name} {lead.last_name}'
        }
        
        return render(request, 'admin_template/view_lead.html', context)
        
    except Exception as e:
        messages.error(request, f'Error loading lead details: {str(e)}')
        return redirect('manage_leads')


@login_required(login_url='login')
def admin_run_ai_workflow(request, lead_id):
    """Admin view to run AI workflow for a lead"""
    try:
        lead = get_object_or_404(Lead, id=lead_id)
        
        # Check if lead has an assigned counsellor
        if not lead.assigned_counsellor:
            messages.error(request, 'Lead must be assigned to a counsellor to run AI workflow.')
            return redirect('admin_view_lead', lead_id=lead_id)
        
        # Import the workflow function from counsellor_views
        from .counsellor_views import run_agentic_workflow
        
        # Temporarily change the request user to the assigned counsellor
        original_user = request.user
        request.user = lead.assigned_counsellor.admin
        
        try:
            # Call the workflow function
            result = run_agentic_workflow(request, lead_id)
            
            # If we get here without exception, the workflow completed successfully
            messages.success(request, 'AI workflow completed successfully!')
                
        finally:
            # Restore the original user
            request.user = original_user
            
    except Exception as e:
        messages.error(request, f'Error running AI workflow: {str(e)}')
    
    return redirect('admin_view_lead', lead_id=lead_id)


@login_required(login_url='login')
def ai_assign_counsellor(request, lead_id):
    """AI-powered counsellor assignment for a lead"""
    try:
        lead = get_object_or_404(Lead, id=lead_id)
        
        # Get all active counsellors
        active_counsellors = Counsellor.objects.filter(is_active=True)
        
        if not active_counsellors.exists():
            messages.error(request, 'No active counsellors available for assignment.')
            return redirect('admin_view_lead', lead_id=lead_id)
        
        # AI Assignment Logic
        best_counsellor = None
        assignment_reason = ""
        
        # Factor 1: Workload Balance (leads assigned but not converted)
        counsellor_workloads = {}
        for counsellor in active_counsellors:
            active_leads = Lead.objects.filter(
                assigned_counsellor=counsellor,
                status__in=['NEW', 'CONTACTED', 'QUALIFIED']
            ).count()
            counsellor_workloads[counsellor] = active_leads
        
        # Factor 2: Performance Score (conversion rate)
        counsellor_performance = {}
        for counsellor in active_counsellors:
            total_leads = Lead.objects.filter(assigned_counsellor=counsellor).count()
            converted_leads = Lead.objects.filter(
                assigned_counsellor=counsellor,
                status='CONVERTED'
            ).count()
            conversion_rate = (converted_leads / total_leads * 100) if total_leads > 0 else 0
            counsellor_performance[counsellor] = conversion_rate
        
        # Factor 3: Academic Specialization Match (based on graduation status, course interested, and academic background)
        specialization_scores = {}
        for counsellor in active_counsellors:
            score = 0
            
            # Check if counsellor has experience with similar graduation status
            similar_leads = Lead.objects.filter(
                assigned_counsellor=counsellor,
                graduation_status=lead.graduation_status
            ).count()
            score += similar_leads * 2
            
            # Check if counsellor has experience with similar courses (academic specialization)
            if lead.course_interested:
                course_leads = Lead.objects.filter(
                    assigned_counsellor=counsellor,
                    course_interested__icontains=lead.course_interested.split()[0]  # First word of course
                ).count()
                score += course_leads * 3
                
                # Bonus for specific academic fields
                course_lower = lead.course_interested.lower()
                if any(field in course_lower for field in ['engineering', 'medicine', 'law', 'mba', 'masters']):
                    score += 2  # Specialized fields get bonus
            
            # Check if counsellor has experience with similar school types
            if lead.school_name:
                school_leads = Lead.objects.filter(
                    assigned_counsellor=counsellor,
                    school_name__icontains=lead.school_name.split()[0]  # First word of school
                ).count()
                score += school_leads * 1
                
            # Check if counsellor has experience with similar graduation courses
            if lead.graduation_course and lead.graduation_course != 'Not Applicable':
                course_leads = Lead.objects.filter(
                    assigned_counsellor=counsellor,
                    graduation_course__icontains=lead.graduation_course.split()[0]
                ).count()
                score += course_leads * 2
            
            specialization_scores[counsellor] = score
        
        # Calculate final scores for each counsellor
        final_scores = {}
        for counsellor in active_counsellors:
            workload_score = max(0, 10 - counsellor_workloads[counsellor])  # Lower workload = higher score
            performance_score = counsellor_performance[counsellor] / 10  # Normalize to 0-10
            specialization_score = min(specialization_scores[counsellor], 10)  # Cap at 10
            
            # Weighted combination: 40% workload, 30% performance, 30% specialization
            final_score = (workload_score * 0.4) + (performance_score * 0.3) + (specialization_score * 0.3)
            final_scores[counsellor] = final_score
        
        # Select the best counsellor
        best_counsellor = max(final_scores.keys(), key=lambda x: final_scores[x])
        
        # Generate assignment reason
        workload = counsellor_workloads[best_counsellor]
        performance = counsellor_performance[best_counsellor]
        specialization = specialization_scores[best_counsellor]
        
        assignment_reason = (
            f"AI Academic Assignment: Selected {best_counsellor.admin.first_name} {best_counsellor.admin.last_name} "
            f"based on workload ({workload} active students), performance ({performance:.1f}% enrollment rate), "
            f"and academic specialization match (score: {specialization}). Final AI score: {final_scores[best_counsellor]:.2f}"
        )
        
        # Assign the lead
        lead.assigned_counsellor = best_counsellor
        lead.save()
        
        # Create a notification for the assigned counsellor
        NotificationCounsellor.objects.create(
            counsellor=best_counsellor,
            message=f"New student assigned: {lead.first_name} {lead.last_name} - Interested in {lead.course_interested}"
        )
        
        messages.success(request, f'Student successfully assigned to {best_counsellor.admin.first_name} {best_counsellor.admin.last_name} using AI academic analysis.')
        
        # Log the assignment reason
        if not lead.notes:
            lead.notes = assignment_reason
        else:
            lead.notes += f"\n\n{assignment_reason}"
        lead.save()
        
    except Exception as e:
        messages.error(request, f'Error in AI assignment: {str(e)}')
    
    return redirect('admin_view_lead', lead_id=lead_id)


@login_required(login_url='login')
def bulk_ai_assign_counsellors(request):
    """Bulk AI assignment for multiple unassigned leads"""
    if request.method == 'POST':
        try:
            # Get all unassigned leads
            unassigned_leads = Lead.objects.filter(assigned_counsellor__isnull=True)
            
            if not unassigned_leads.exists():
                messages.info(request, 'No unassigned leads found.')
                return redirect('manage_leads')
            
            # Get all active counsellors
            active_counsellors = Counsellor.objects.filter(is_active=True)
            
            if not active_counsellors.exists():
                messages.error(request, 'No active counsellors available for assignment.')
                return redirect('manage_leads')
            
            assigned_count = 0
            
            for lead in unassigned_leads:
                # Use the same AI logic as single assignment
                counsellor_workloads = {}
                for counsellor in active_counsellors:
                    active_leads = Lead.objects.filter(
                        assigned_counsellor=counsellor,
                        status__in=['NEW', 'CONTACTED', 'QUALIFIED']
                    ).count()
                    counsellor_workloads[counsellor] = active_leads
                
                counsellor_performance = {}
                for counsellor in active_counsellors:
                    total_leads = Lead.objects.filter(assigned_counsellor=counsellor).count()
                    converted_leads = Lead.objects.filter(
                        assigned_counsellor=counsellor,
                        status='CONVERTED'
                    ).count()
                    conversion_rate = (converted_leads / total_leads * 100) if total_leads > 0 else 0
                    counsellor_performance[counsellor] = conversion_rate
                
                specialization_scores = {}
                for counsellor in active_counsellors:
                    score = 0
                    
                    similar_leads = Lead.objects.filter(
                        assigned_counsellor=counsellor,
                        graduation_status=lead.graduation_status
                    ).count()
                    score += similar_leads * 2
                    
                    if lead.course_interested:
                        course_leads = Lead.objects.filter(
                            assigned_counsellor=counsellor,
                            course_interested__icontains=lead.course_interested.split()[0]
                        ).count()
                        score += course_leads * 3
                    
                    if lead.school_name:
                        school_leads = Lead.objects.filter(
                            assigned_counsellor=counsellor,
                            school_name__icontains=lead.school_name.split()[0]
                        ).count()
                        score += school_leads * 1
                    
                    specialization_scores[counsellor] = score
                
                # Calculate final scores
                final_scores = {}
                for counsellor in active_counsellors:
                    workload_score = max(0, 10 - counsellor_workloads[counsellor])
                    performance_score = counsellor_performance[counsellor] / 10
                    specialization_score = min(specialization_scores[counsellor], 10)
                    
                    final_score = (workload_score * 0.4) + (performance_score * 0.3) + (specialization_score * 0.3)
                    final_scores[counsellor] = final_score
                
                # Select best counsellor
                best_counsellor = max(final_scores.keys(), key=lambda x: final_scores[x])
                
                # Assign the lead
                lead.assigned_counsellor = best_counsellor
                lead.save()
                
                # Create notification
                NotificationCounsellor.objects.create(
                    counsellor=best_counsellor,
                    message=f"New lead assigned: {lead.first_name} {lead.last_name} - {lead.course_interested}"
                )
                
                assigned_count += 1
            
            messages.success(request, f'Successfully assigned {assigned_count} leads using AI analysis.')
            
        except Exception as e:
            messages.error(request, f'Error in bulk AI assignment: {str(e)}')
    
    return redirect('manage_leads')


@login_required(login_url='login')
def manual_route_student(request, lead_id):
    """Manual routing of student to different academic departments"""
    if request.method == 'POST':
        try:
            lead = get_object_or_404(Lead, id=lead_id)
            route_to = request.POST.get('route_to')
            custom_reason = request.POST.get('custom_reason', '')
            
            if not route_to:
                messages.error(request, 'Please select a routing option.')
                return redirect('admin_view_lead', lead_id=lead_id)
            
            # Import the routing function from counsellor_views
            from .counsellor_views import execute_academic_routing
            
            # Use custom reason if provided, otherwise use default
            if custom_reason:
                routing_reason = f"Manual routing: {custom_reason}"
            else:
                routing_reason = f"Manually routed to {route_to.replace('_', ' ')} by admin"
            
            # Execute the routing
            routing_success = execute_academic_routing(lead, route_to, routing_reason)
            
            if routing_success:
                messages.success(request, f'Student successfully routed to {route_to.replace("_", " ")}.')
            else:
                messages.error(request, 'Routing failed. Please try again.')
                
        except Exception as e:
            messages.error(request, f'Error in manual routing: {str(e)}')
    
    return redirect('admin_view_lead', lead_id=lead_id)
