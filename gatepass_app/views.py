# gatepass_app/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import GatePass
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

current_time = timezone.now().astimezone(timezone.get_current_timezone())


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


# --- DRF API Views ---

class GatePassViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows GatePass records to be viewed or updated for IN/OUT.
    """
    queryset = GatePass.objects.all()
    serializer_class = GatePassSerializer
    permission_classes = [IsAuthenticated]

    def update(self, request, *args, **kwargs):
        partial = False
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        gatepass_no = instance.GATEPASS_NO
        current_time = timezone.now()
        security_guard_identifier = request.user.username
        update_fields = []
        params = {}

        if 'OUT_TIME' in request.data:
            update_fields.append("OUT_TIME = :out_time")
            params['out_time'] = out_time
        if 'OUT_BY' in request.data:
            update_fields.append("OUT_BY = :out_by")
            params['out_by'] = out_by
        if 'IN_TIME' in request.data:
            update_fields.append("IN_TIME = :in_time")
            params['in_time'] = in_time
        if 'IN_BY' in request.data:
            update_fields.append("IN_BY = :in_by")
            params['in_by'] = in_by
        if 'INOUT_STATUS' in request.data:
            update_fields.append("INOUT_STATUS = :inout_status")
            params['inout_status'] = inout_status
        
        if 'OUT_BY' not in request.data and 'OUT_TIME' in request.data and out_time:
            update_fields.append("OUT_BY = :out_by_auto")
            params['out_by_auto'] = security_guard_identifier
            inout_status = 'O'
            update_fields.append("INOUT_STATUS = 'O'")

        if 'IN_BY' not in request.data and 'IN_TIME' in request.data and in_time:
            update_fields.append("IN_BY = :in_by_auto")
            params['in_by_auto'] = security_guard_identifier
            inout_status = 'I'
            update_fields.append("INOUT_STATUS = 'I'")

        if not update_fields:
            return Response({"detail": "No updatable fields provided."}, status=status.HTTP_400_BAD_REQUEST)

        sql = f"UPDATE GATEPASS SET {', '.join(update_fields)} WHERE GATEPASS_NO = :gatepass_no"
        params['gatepass_no'] = gatepass_no

        try:
            with connection.cursor() as cursor:
                cursor.execute(sql, params)
                updated_instance = GatePass.objects.get(pk=gatepass_no)
                serializer = self.get_serializer(updated_instance)
                return Response(serializer.data)
        except Exception as e:
            return Response({"detail": f"Error updating GatePass: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)


@login_required
def create_manual_gatepass_entry(request):
    if request.method == 'POST':
        form = ManualGatePassForm(request.POST)
        if form.is_valid():
            paycode = form.cleaned_data['PAYCODE']
            gatepass_type = form.cleaned_data['GATEPASS_TYPE']

            try:
                # MARK_IN_TIME from hidden input (YYYY-MM-DDTHH:MM:SS from JS)
                mark_in_time_str = request.POST.get('MARK_IN_TIME')
                # MARK_OUT_TIME from hidden input (YYYY-MM-DDTHH:MM:SS from JS)
                mark_out_time_str = request.POST.get('MARK_OUT_TIME')

                # Use datetime.fromisoformat for both, as they now should consistently be 'YYYY-MM-DDTHH:MM:SS'
                mark_in_time_naive = datetime.fromisoformat(mark_in_time_str)
                mark_out_time_naive = datetime.fromisoformat(mark_out_time_str)

                # Make them timezone-aware using the ORACLE_SERVER_TIMEZONE (IST)
                mark_in_time_aware = ORACLE_SERVER_TIMEZONE.localize(mark_in_time_naive)
                mark_out_time_aware = ORACLE_SERVER_TIMEZONE.localize(mark_out_time_naive)

                # Convert to naive datetime objects for Oracle insertion if needed
                naive_mark_in_time_for_oracle = mark_in_time_aware.replace(tzinfo=None)
                naive_mark_out_time_for_oracle = mark_out_time_aware.replace(tzinfo=None)

            except (ValueError, TypeError) as e:
                messages.error(request, f"Error parsing time data: {e}. Please ensure correct time format.")
                form = ManualGatePassForm(request.POST)  # Pass POST data back to re-render form with errors
                return render(request, 'gatepass_app/create_manual_gatepass.html', {'form': form})

            current_date_aware = timezone.now().astimezone(ORACLE_SERVER_TIMEZONE)
            current_date_naive = current_date_aware.date()  # Get just the date part for GATEPASS_DATE

            with connection.cursor() as cursor:
                # Find the highest sequence number for today's manual entries
                cursor.execute(
                    f"SELECT MAX(GATEPASS_NO) FROM GATEPASS"
                )
                last_seq = cursor.fetchone()[0]
                if last_seq:
                    next_seq = int(last_seq) + 1
                else:
                    next_seq = 1
                new_gatepass_no = f"{next_seq}"

                # Fetch employee name and department from EMP_MST based on PAYCODE
                emp_name = None
                department = None
                try:
                    cursor.execute(
                        """
                        SELECT A.EMP_NAME, B.DEPARTMENTNAME ,A.EMP_TYPE  FROM EMP_MST@DB_APPS_TO_SVR A, TBLDEPARTMENT@DB_APPS_TO_SVR B
                        WHERE LTRIM(RTRIM(A.PAYCODE)) = :P_PAYCODE AND A.DEPT_CODE = B.DEPARTMENTCODE
                        """,
                        {'p_paycode': paycode}
                    )
                    emp_details = cursor.fetchone()
                    if emp_details:
                        emp_name = emp_details[0]
                        department = emp_details[1]
                        emp_type = emp_details[2]
                    else:
                        messages.warning(request, f"Employee with Pay Code {paycode} not found in master data. Proceeding without name/department.")
                        # Set default values if not found, so insertion doesn't fail
                        emp_name = "UNKNOWN"
                        department = "UNKNOWN"
                        emp_type = "UNKNOWN"
                except Exception as e:
                    messages.warning(request, f"Could not fetch employee details for Pay Code {paycode}: {e}. Proceeding with default values.")
                    emp_name = "DB_ERROR"
                    department = "DB_ERROR"
                    emp_type = "DB_ERROR"

                security_guard_identifier = request.user.username

                try:
                    cursor.execute(
                        """
                        INSERT INTO GATEPASS@DB_APPS_TO_SVR (
                            GATEPASS_NO, GATEPASS_DATE, PAYCODE, NAME, DEPARTMENT, GATEPASS_TYPE,
                            REMARKS, OUT_TIME, OUT_BY, IN_TIME, IN_BY, INOUT_STATUS, FINAL_STATUS,
                            REQUEST_TIME, AUTH, AUTH1_BY, AUTH1_STATUS, AUTH1_DATE, AUTH1_REMARKS,EMP_TYPE,USER_ID,BYPASS_REASON
                        ) VALUES (
                            :gatepass_no, :gatepass_date, :paycode, :name, :department, :gatepass_type,
                            :remarks, :out_time, :out_by, :in_time, :in_by, :inout_status, :final_status,
                            :request_time, :auth, :auth1_by, :auth1_status, :auth1_date, :auth1_remarks,:emp_type,:user_id,:bypass_reason
                        )
                        """,
                        {
                            'gatepass_no': new_gatepass_no,
                            'gatepass_date': current_date_naive,  # Gatepass date is today
                            'paycode': paycode,
                            'name': emp_name,
                            'department': department,
                            'gatepass_type': gatepass_type,
                            'remarks': 'Without intimation leave taken - Manual Entry',  # Added more context
                            'out_time': naive_mark_out_time_for_oracle,  # Use parsed value from frontend
                            'out_by': security_guard_identifier,
                            'in_time': naive_mark_in_time_for_oracle,  # Use parsed value from frontend
                            'in_by': security_guard_identifier,
                            'inout_status': 'I',  # Marked as 'In' since both times are provided for a manual entry
                            'final_status': 'A',  # Assuming manually approved
                            'request_time': mark_in_time_aware.strftime('%I:%M:%S %p'),  # Use MARK_IN_TIME as REQUEST_TIME
                            'auth': '1',  # N = Not required for approval, or set to 'Y' if manual entry bypasses auth.
                            # Given AUTH1_STATUS is 'B', 'N' for AUTH makes sense (No approval needed).
                            'auth1_by': None,  # No specific approver for manual bypass
                            'auth1_status': 'B',  # B = By-passed
                            'auth1_date': None,  # No approval date for bypass
                            'auth1_remarks': None,  # Specific remark for bypass
                            'emp_type': emp_type,  
                            'user_id': paycode,  # User who created this entry
                            'bypass_reason': 'Marked by security - Manual',  # More specific reason
                        }
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


@login_required
def get_employee_details(request):
    """
    AJAX endpoint to fetch employee name and department based on paycode.
    """
    paycode = request.GET.get('paycode', None)
    employee_name = "N/A"
    department_name = "N/A"

    if paycode:
        with connection.cursor() as cursor:
            try:
                cursor.execute(
                    """
                    SELECT a.EMPNAME, b.DEPARTMENTNAME
                    FROM savior9x.tblemployee a, SAVIOR9X.TBLDEPARTMENT b
                    WHERE LTRIM(RTRIM(a.PAYCODE)) = :p_paycode AND a.DEPARTMENTCODE = b.DEPARTMENTCODE
                    """,
                    {'p_paycode': paycode}
                )
                emp_details = cursor.fetchone()
                if emp_details:
                    employee_name = emp_details[0]
                    department_name = emp_details[1]
            except Exception as e:
                # Log the error, but return N/A to the frontend
                print(f"Database error fetching employee details for {paycode}: {e}")

    return JsonResponse({
        'employee_name': employee_name,
        'department_name': department_name
    })