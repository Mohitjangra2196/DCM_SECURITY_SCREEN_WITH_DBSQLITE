# gatepass_app/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import GatePass
from django.db.models import Max
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt 
from django.contrib.auth import get_user_model
from datetime import datetime, timedelta

# Import the new form
from .forms import ManualGatePassForm

# DRF Imports
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from .serializers import GatePassSerializer

# Import for timezone handling
from django.utils import timezone
from django.conf import settings 
import pytz
from datetime import timedelta

current_time = timezone.now().astimezone(timezone.get_current_timezone()).replace(microsecond=0).replace(tzinfo=None)


User = get_user_model() # Get the currently active user model (which is now Django's default User)

@login_required
def home_screen(request):
    # Filter out superusers from the list of security guards
    # is_superuser=False will exclude any user marked as a superuser.
    security_guards = User.objects.filter(is_superuser=False).order_by('username')
    return render(request, 'gatepass_app/home_screen.html', {'security_guards': security_guards})

@login_required
def mark_out_screen(request):
    employees_to_mark_out = []
    # Fetch employees who are currently out and not yet marked in   
    approved_gatepass = GatePass.objects.filter(
        FINAL_STATUS='A',
        OUT_TIME__isnull=True,  # Not yet marked out
    ).values(
        'PAYCODE', 'NAME', 'DEPARTMENT', 'UNIT_NAME',  
        'AUTH', 'GATEPASS_TYPE', 'EMP_TYPE' ,'LUNCH', 'GATEPASS_NO'
    )   
    # Convert the queryset to a list of dictionaries
    for employee in approved_gatepass:      
        employee_dict = {
            'NAME': employee['NAME'] + ' - ' + employee['PAYCODE'] + ' - ' + employee['EMP_TYPE'],
            'DEPARTMENT_UNIT': employee['DEPARTMENT'] + ' - ' + employee['UNIT_NAME'],
            'STATUS_TYPE_LUNCH': f"{'ByPass' if employee['AUTH'] == '1' else 'Approved'} - {employee['GATEPASS_TYPE']} - {employee['LUNCH']}",
            'GATEPASS_NO': employee['GATEPASS_NO'],  # Include GATEPASS_NO for processing later
        }
        employees_to_mark_out.append(employee_dict)
    return render(request, 'gatepass_app/mark_out_screen.html', {'employees': employees_to_mark_out})


@login_required
def process_mark_out(request, gatepass_no):
    if request.method == 'POST':
        try:
            gp_record = GatePass.objects.get(GATEPASS_NO=gatepass_no)
            gp_record.OUT_TIME = current_time
            gp_record.OUT_BY = request.user.username
            gp_record.INOUT_STATUS = 'O' 
            gp_record.save() # This commits the changes to the database
            messages.success(request, f"Employee {gp_record.NAME} with Gatepass no : {gatepass_no} marked OUT successfully.")
        except GatePass.DoesNotExist:
            print(f"Error: GatePass record with {gatepass_no} does not exist.")
        except Exception as e:
            print(f"An error occurred: {e}")
    return redirect('mark_out_screen')

@login_required
def mark_in_screen(request):
    employees_to_mark_in = []
    out_employees = GatePass.objects.filter(
        INOUT_STATUS='O',
        IN_TIME__isnull=True,  # Not yet marked out
    ).values(
        'GATEPASS_NO','NAME','PAYCODE','EMP_TYPE','DEPARTMENT',
        'UNIT_NAME','OUT_TIME'
    )

    for I in out_employees:
        employee_dict = {
            'GATEPASS_NO' : I['GATEPASS_NO'],
            'NAME' : I['NAME'] + ' - ' + I['PAYCODE'] + ' - ' + I['EMP_TYPE'] ,
            'DEPARTMENT_UNIT' : I['DEPARTMENT'] + ' - ' + I['UNIT_NAME'],
            'OUT_TIME' : I['OUT_TIME'],
        }
        employees_to_mark_in.append(employee_dict)
    return render(request, 'gatepass_app/mark_in_screen.html', {'employees': employees_to_mark_in})

@login_required
def process_mark_in(request, gatepass_no):
    if request.method == 'POST':
        try:
            gp_record = GatePass.objects.get(GATEPASS_NO=gatepass_no)
            gp_record.IN_TIME = current_time
            gp_record.IN_BY = request.user.username
            gp_record.INOUT_STATUS = 'I' 
            gp_record.save()
            messages.success(request, f"Employee {gp_record.NAME} with Gatepass no : {gatepass_no} marked IN successfully.")
        except GatePass.DoesNotExist:
            print(f"Error: GatePass record with {gatepass_no} does not exist.")
        except Exception as e:
            print(f"An error occurred: {e}")
    return redirect('mark_in_screen')


@login_required
def create_manual_gatepass_entry(request):
    if request.method == 'POST':
        form = ManualGatePassForm(request.POST)
        if form.is_valid():

            try:
                #print(f'sdds:{form.cleaned_data['mark_out_duration']}')
                max_gatepass_no = GatePass.objects.aggregate(max_no=Max('GATEPASS_NO'))['max_no']
                new_gatepass_no = str(int(max_gatepass_no) + 1) if max_gatepass_no else "0001"
                GatePass.objects.create(
                    GATEPASS_NO=new_gatepass_no,
                    GATEPASS_DATE=current_time.strftime("%Y-%m-%d"),
                    PAYCODE=form.cleaned_data['PAYCODE'] ,
                    # NAME=form.cleaned_data['EMPLOYEE_NAME'] ,
                    # DEPARTMENT=form.cleaned_data['DEPARTMENT_NAME'] ,
                    NAME='MJ',
                    DEPARTMENT = 'IT',
                    GATEPASS_TYPE=form.cleaned_data['GATEPASS_TYPE'] ,
                    REMARKS='Without intimation leave taken - Manual Entry',
                    OUT_TIME=(current_time - timedelta(minutes=int(form.cleaned_data['mark_out_duration']))) ,
                    OUT_BY = request.user.username,
                    IN_TIME=current_time ,#.strftime("%d-%m-%Y %I-%M-%S-%p"),    
                    IN_BY = request.user.username,
                    INOUT_STATUS=None,
                    FINAL_STATUS='A',
                    REQUEST_TIME=current_time.strftime('%I:%M:%S %p'), 
                    AUTH='1', 
                    AUTH1_BY=None,
                    AUTH1_STATUS='B',
                    AUTH1_DATE=None,
                    AUTH1_REMARKS=None,
                    UNIT_NAME='Unit-1',  
                    EMP_TYPE='S',
                    LUNCH='Y',     
                )
                messages.success(request, f"Manual Gatepass {new_gatepass_no} created successfully.")
                return redirect('mark_in_screen')
            except Exception as e:
                messages.error(request, f"Error creating manual gatepass: {e}")
        else:
            messages.error(request, "Please correct the errors in the form.")
    else:
        form = ManualGatePassForm()
    return render(request, 'gatepass_app/create_manual_gatepass.html', {'form': form})


