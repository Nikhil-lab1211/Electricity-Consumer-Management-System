from django.shortcuts import render

# Create your views here.
# user_app/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse
from datetime import timedelta
import uuid

from .models import User, Consumer, Bill, ConsumptionRecord, PowerOutage, Complaint
from .forms import (LoginForm, UserRegistrationForm, ConsumerRegistrationForm,
                   BillCheckForm, PaymentForm, OutageReportForm, ComplaintForm, ConsumptionTrackForm)

def index(request):
    return render(request, 'user_app/index.html')

def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            remember = form.cleaned_data['remember_me']
            
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                if not remember:
                    request.session.set_expiry(0)
                return redirect('dashboard')
            else:
                form.add_error(None, 'Invalid username or password')
    else:
        form = LoginForm()
    
    return render(request, 'user_app/login.html', {'form': form})

@login_required
def logout_view(request):
    logout(request)
    return redirect('index')

def register(request):
    if request.method == 'POST':
        user_form = UserRegistrationForm(request.POST)
        consumer_form = ConsumerRegistrationForm(request.POST)
        
        if user_form.is_valid() and consumer_form.is_valid():
            user = user_form.save(commit=False)
            user.role = 'consumer'
            user.save()
            
            consumer = consumer_form.save(commit=False)
            consumer.user = user
            consumer.consumer_id = f"CONS-{uuid.uuid4().hex[:8].upper()}"
            consumer.save()
            
            return redirect('login')
    else:
        user_form = UserRegistrationForm()
        consumer_form = ConsumerRegistrationForm()
    
    return render(request, 'user_app/register.html', {
        'user_form': user_form,
        'consumer_form': consumer_form
    })

@login_required
def dashboard(request):
    # Different dashboards for different roles
    if request.user.role == 'admin':
        return render(request, 'user_app/admin_dashboard.html')
    elif request.user.role == 'staff':
        return render(request, 'user_app/staff_dashboard.html')
    else:  # consumer
        try:
            consumer = Consumer.objects.get(user=request.user)
            bills = Bill.objects.filter(consumer=consumer).order_by('-bill_date')[:5]
            complaints = Complaint.objects.filter(consumer=consumer).order_by('-complaint_date')[:5]
            consumption = ConsumptionRecord.objects.filter(consumer=consumer).order_by('-reading_date')[:6]
            
            return render(request, 'user_app/consumer_dashboard.html', {
                'consumer': consumer,
                'bills': bills,
                'complaints': complaints,
                'consumption': consumption
            })
        except Consumer.DoesNotExist:
            return redirect('complete_profile')

@login_required
def complete_profile(request):
    if hasattr(request.user, 'consumer_profile'):
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = ConsumerRegistrationForm(request.POST)
        if form.is_valid():
            consumer = form.save(commit=False)
            consumer.user = request.user
            consumer.consumer_id = f"CONS-{uuid.uuid4().hex[:8].upper()}"
            consumer.save()
            return redirect('dashboard')
    else:
        form = ConsumerRegistrationForm()
    
    return render(request, 'user_app/complete_profile.html', {'form': form})

@login_required
def bill_view(request):
    if request.user.role == 'consumer':
        try:
            consumer = Consumer.objects.get(user=request.user)
            bills = Bill.objects.filter(consumer=consumer).order_by('-bill_date')
            return render(request, 'user_app/bills.html', {'bills': bills})
        except Consumer.DoesNotExist:
            return redirect('complete_profile')
    elif request.user.role in ['admin', 'staff']:
        bills = Bill.objects.all().order_by('-bill_date')
        return render(request, 'user_app/bills.html', {'bills': bills})

@csrf_exempt
def check_bill_api(request):
    if request.method == 'POST':
        account_number = request.POST.get('account_number')
        try:
            consumer = Consumer.objects.get(account_number=account_number)
            recent_bill = Bill.objects.filter(consumer=consumer).order_by('-bill_date').first()
            
            if not recent_bill:
                return JsonResponse({'success': False, 'message': 'No bills found for this account'})
            
            return JsonResponse({
                'success': True,
                'bill': {
                    'bill_number': recent_bill.bill_number,
                    'bill_date': recent_bill.bill_date.strftime('%Y-%m-%d'),
                    'due_date': recent_bill.due_date.strftime('%Y-%m-%d'),
                    'amount': float(recent_bill.amount),
                    'units_consumed': recent_bill.units_consumed,
                    'status': recent_bill.status
                }
            })
        except Consumer.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Account number not found'})
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})

def check_bill(request):
    if request.method == 'POST':
        form = BillCheckForm(request.POST)
        if form.is_valid():
            account_number = form.cleaned_data['account_number']
            try:
                consumer = Consumer.objects.get(account_number=account_number)
                bill = Bill.objects.filter(consumer=consumer).order_by('-bill_date').first()
                
                if bill:
                    return render(request, 'user_app/bill_details.html', {'bill': bill})
                else:
                    form.add_error(None, 'No bills found for this account')
            except Consumer.DoesNotExist:
                form.add_error(None, 'Account number not found')
    else:
        form = BillCheckForm()
    
    return render(request, 'user_app/check_bill.html', {'form': form})

@login_required
def pay_bill(request, bill_id=None):
    if bill_id:
        bill = get_object_or_404(Bill, id=bill_id)
        
        if request.method == 'POST':
            form = PaymentForm(request.POST)
            if form.is_valid():
                payment_method = form.cleaned_data['payment_method']
                
                # Update bill status
                bill.status = 'paid'
                bill.payment_date = timezone.now()
                bill.payment_method = payment_method
                bill.payment_reference = f"PYM-{uuid.uuid4().hex[:8].upper()}"
                bill.save()
                
                return render(request, 'user_app/payment_success.html', {'bill': bill})
        else:
            form = PaymentForm(initial={
                'consumer_id': bill.consumer.consumer_id,
                'bill_amount': bill.amount
            })
        
        return render(request, 'user_app/pay_bill.html', {'form': form, 'bill': bill})
    else:
        return redirect('bills')

@csrf_exempt
def pay_bill_api(request):
    if request.method == 'POST':
        consumer_id = request.POST.get('consumer_id')
        bill_amount = float(request.POST.get('bill_amount'))
        payment_method = request.POST.get('payment_method')
        
        try:
            consumer = Consumer.objects.get(consumer_id=consumer_id)
            unpaid_bill = Bill.objects.filter(consumer=consumer, status='unpaid').first()
            
            if not unpaid_bill:
                return JsonResponse({'success': False, 'message': 'No unpaid bills found'})
            
            # Update bill status
            unpaid_bill.status = 'paid'
            unpaid_bill.payment_date = timezone.now()
            unpaid_bill.payment_method = payment_method
            unpaid_bill.payment_reference = f"PYM-{uuid.uuid4().hex[:8].upper()}"
            unpaid_bill.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Payment successful',
                'payment_reference': unpaid_bill.payment_reference,
                'payment_date': unpaid_bill.payment_date.strftime('%Y-%m-%d %H:%M')
            })
        except Consumer.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Consumer ID not found'})
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})

@login_required
def report_outage(request):
    if request.method == 'POST':
        form = OutageReportForm(request.POST)
        if form.is_valid():
            outage = form.save(commit=False)
            outage.reported_by = request.user
            outage.estimated_resolution_time = timezone.now() + timedelta(hours=4)
            outage.save()
            
            return render(request, 'user_app/outage_reported.html', {'outage': outage})
    else:
        form = OutageReportForm()
    
    return render(request, 'user_app/report_outage.html', {'form': form})

@csrf_exempt
def report_outage_api(request):
    if request.method == 'POST':
        area_code = request.POST.get('area_code')
        
        # Create a new outage report
        new_outage = PowerOutage(
            area_code=area_code,
            reported_by=request.user if request.user.is_authenticated else None,
            description="Reported through website",
            estimated_resolution_time=timezone.now() + timedelta(hours=4)
        )
        new_outage.save()
        
        return JsonResponse({
            'success': True, 
            'message': 'Outage reported successfully',
            'outage_id': new_outage.id,
            'estimated_resolution': new_outage.estimated_resolution_time.strftime('%Y-%m-%d %H:%M')
        })
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})

@login_required
def file_complaint(request):
    if request.user.role != 'consumer':
        return redirect('dashboard')
    
    try:
        consumer = Consumer.objects.get(user=request.user)
        
        if request.method == 'POST':
            form = ComplaintForm(request.POST)
            if form.is_valid():
                complaint = form.save(commit=False)
                complaint.consumer = consumer
                complaint.complaint_number = f"COMP-{uuid.uuid4().hex[:8].upper()}"
                complaint.save()
                
                return render(request, 'user_app/complaint_filed.html', {'complaint': complaint})
        else:
            form = ComplaintForm()
        
        return render(request, 'user_app/file_complaint.html', {'form': form})
    except Consumer.DoesNotExist:
        return redirect('complete_profile')

@login_required
def view_complaints(request):
    if request.user.role == 'consumer':
        try:
            consumer = Consumer.objects.get(user=request.user)
            complaints = Complaint.objects.filter(consumer=consumer).order_by('-complaint_date')
            return render(request, 'user_app/view_complaints.html', {'complaints': complaints})
        except Consumer.DoesNotExist:
            return redirect('complete_profile')
    elif request.user.role in ['admin', 'staff']:
        complaints = Complaint.objects.all().order_by('-complaint_date')
        return render(request, 'user_app/view_complaints.html', {'complaints': complaints})

@login_required
def view_outages(request):
    outages = PowerOutage.objects.all().order_by('-start_time')
    return render(request, 'user_app/view_outages.html', {'outages': outages})

@login_required
def track_consumption(request):
    if request.user.role == 'consumer':
        try:
            consumer = Consumer.objects.get(user=request.user)
            consumption_records = ConsumptionRecord.objects.filter(consumer=consumer).order_by('-reading_date')
            
            # Prepare data for chart
            labels = []
            data = []
            for record in consumption_records:
                labels.append(record.reading_date.strftime('%Y-%m-%d'))
                data.append(record.units_consumed)
            
            return render(request, 'user_app/track_consumption.html', {
                'records': consumption_records,
                'labels': labels,
                'data': data
            })
        except Consumer.DoesNotExist:
            return redirect('complete_profile')
    else:
        form = ConsumptionTrackForm()
        records = None
        
        if request.method == 'POST':
            form = ConsumptionTrackForm(request.POST)
            if form.is_valid():
                meter_number = form.cleaned_data['meter_number']
                try:
                    consumer = Consumer.objects.get(meter_number=meter_number)
                    records = ConsumptionRecord.objects.filter(consumer=consumer).order_by('-reading_date')
                except Consumer.DoesNotExist:
                    form.add_error(None, 'Meter number not found')
        
        return render(request, 'user_app/track_consumption_admin.html', {
            'form': form,
            'records': records
        })

@csrf_exempt
def track_consumption_api(request):
    if request.method == 'POST':
        meter_number = request.POST.get('meter_number')
        
        try:
            consumer = Consumer.objects.get(meter_number=meter_number)
            consumption_records = ConsumptionRecord.objects.filter(consumer=consumer).order_by('-reading_date')[:6]
            
            if not consumption_records:
                return JsonResponse({'success': False, 'message': 'No consumption records found'})
            
            # Format the data
            data = []
            for record in consumption_records:
                data.append({
                    'date': record.reading_date.strftime('%Y-%m-%d'),
                    'reading': record.meter_reading,
                    'units': record.units_consumed,
                    'type': record.reading_type
                })
            
            return JsonResponse({
                'success': True,
                'consumer_id': consumer.consumer_id,
                'consumption_data': data
            })
        except Consumer.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Meter number not found'})
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})