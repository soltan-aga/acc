from django.shortcuts import render, redirect, get_object_or_404, reverse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.db import transaction
from django.db.models import Sum, Count, Q
from django.http import HttpResponse
from datetime import datetime, timedelta
import calendar
from .models import Employee, Attendance, EmployeeLoan, Salary
from core.models import Safe
from .forms import EmployeeForm, AttendanceForm, BulkAttendanceForm, EmployeeLoanForm, SalaryForm, SalaryGenerateForm

# صفحات الموظفين
@login_required
def employee_list(request):
    """عرض قائمة الموظفين"""
    employees = Employee.objects.all()
    return render(request, 'employees/employee/list.html', {'employees': employees})

@login_required
def employee_detail(request, pk):
    """عرض تفاصيل موظف"""
    employee = get_object_or_404(Employee, pk=pk)

    # الحصول على بيانات الحضور للشهر الحالي
    today = timezone.now().date()
    attendance_records = employee.attendance_records.filter(
        date__year=today.year,
        date__month=today.month
    ).order_by('date')

    # الحصول على السلف النشطة
    active_loans = employee.loans.filter(is_paid=False)

    # الحصول على آخر راتب
    last_salary = employee.salaries.first()

    context = {
        'employee': employee,
        'attendance_records': attendance_records,
        'active_loans': active_loans,
        'last_salary': last_salary,
    }

    return render(request, 'employees/employee/detail.html', context)

@login_required
def employee_add(request):
    """إضافة موظف جديد"""
    if request.method == 'POST':
        form = EmployeeForm(request.POST)
        if form.is_valid():
            employee = form.save()
            messages.success(request, f'تم إضافة الموظف {employee.name} بنجاح')
            return redirect('employees:employee_detail', pk=employee.pk)
    else:
        form = EmployeeForm(initial={
            'hire_date': timezone.now().date(),
            'status': 'active'
        })

    return render(request, 'employees/employee/form.html', {
        'form': form,
        'title': 'إضافة موظف جديد'
    })

@login_required
def employee_edit(request, pk):
    """تعديل بيانات موظف"""
    employee = get_object_or_404(Employee, pk=pk)

    if request.method == 'POST':
        form = EmployeeForm(request.POST, instance=employee)
        if form.is_valid():
            employee = form.save()
            messages.success(request, f'تم تعديل بيانات الموظف {employee.name} بنجاح')
            return redirect('employees:employee_detail', pk=employee.pk)
    else:
        form = EmployeeForm(instance=employee)

    return render(request, 'employees/employee/form.html', {
        'form': form,
        'title': f'تعديل بيانات الموظف: {employee.name}',
        'employee': employee
    })

# صفحات الحضور والغياب
@login_required
def attendance_list(request):
    """عرض قائمة سجلات الحضور"""
    attendance_records = Attendance.objects.all().order_by('-date')
    return render(request, 'employees/attendance/list.html', {'attendance_records': attendance_records})

@login_required
def attendance_daily(request):
    """عرض سجلات الحضور اليومية"""
    # الحصول على التاريخ المطلوب (اليوم الحالي افتراضيًا)
    date_str = request.GET.get('date')
    if date_str:
        try:
            selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            selected_date = timezone.now().date()
    else:
        selected_date = timezone.now().date()

    # الحصول على سجلات الحضور لهذا اليوم
    attendance_records = Attendance.objects.filter(date=selected_date).order_by('employee__name')

    # الحصول على جميع الموظفين النشطين
    active_employees = Employee.objects.filter(status=Employee.ACTIVE)

    # إنشاء قائمة بالموظفين وحالة حضورهم
    employees_attendance = []
    for employee in active_employees:
        try:
            attendance = attendance_records.get(employee=employee)
        except Attendance.DoesNotExist:
            attendance = None

        employees_attendance.append({
            'employee': employee,
            'attendance': attendance
        })

    context = {
        'selected_date': selected_date,
        'employees_attendance': employees_attendance,
        'present_count': attendance_records.filter(status=Attendance.PRESENT).count(),
        'absent_count': attendance_records.filter(status=Attendance.ABSENT).count(),
        'excused_count': attendance_records.filter(status=Attendance.EXCUSED).count(),
    }

    return render(request, 'employees/attendance/daily.html', context)

@login_required
def attendance_monthly(request):
    """عرض سجلات الحضور الشهرية"""
    # الحصول على الشهر والسنة المطلوبين (الشهر الحالي افتراضيًا)
    year = request.GET.get('year', timezone.now().year)
    month = request.GET.get('month', timezone.now().month)

    try:
        year = int(year)
        month = int(month)
    except ValueError:
        year = timezone.now().year
        month = timezone.now().month

    # الحصول على عدد أيام الشهر
    _, days_in_month = calendar.monthrange(year, month)

    # الحصول على جميع الموظفين النشطين
    active_employees = Employee.objects.filter(status=Employee.ACTIVE)

    # الحصول على سجلات الحضور لهذا الشهر
    attendance_records = Attendance.objects.filter(
        date__year=year,
        date__month=month
    )

    # إنشاء قاموس لتسهيل الوصول إلى سجلات الحضور
    attendance_dict = {}
    for record in attendance_records:
        key = f"{record.employee_id}_{record.date.day}"
        attendance_dict[key] = record

    # إنشاء بيانات الجدول
    employees_data = []
    for employee in active_employees:
        days_data = []
        for day in range(1, days_in_month + 1):
            key = f"{employee.id}_{day}"
            attendance = attendance_dict.get(key)
            days_data.append({
                'day': day,
                'attendance': attendance
            })

        employees_data.append({
            'employee': employee,
            'days': days_data,
            'present_count': attendance_records.filter(employee=employee, status=Attendance.PRESENT).count(),
            'absent_count': attendance_records.filter(employee=employee, status=Attendance.ABSENT).count(),
            'excused_count': attendance_records.filter(employee=employee, status=Attendance.EXCUSED).count(),
        })

    context = {
        'year': year,
        'month': month,
        'month_name': calendar.month_name[month],
        'days_in_month': days_in_month,
        'employees_data': employees_data,
    }

    return render(request, 'employees/attendance/monthly.html', context)

@login_required
def attendance_add(request):
    """إضافة سجل حضور"""
    # الحصول على الموظف والتاريخ من الاستعلام إذا كانت متوفرة
    employee_id = request.GET.get('employee_id')
    date_str = request.GET.get('date')

    initial_data = {}

    # تعيين التاريخ الافتراضي
    if date_str:
        try:
            initial_data['date'] = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            initial_data['date'] = timezone.now().date()
    else:
        initial_data['date'] = timezone.now().date()

    # تعيين الموظف الافتراضي
    if employee_id:
        try:
            employee = Employee.objects.get(pk=employee_id)
            initial_data['employee'] = employee
        except Employee.DoesNotExist:
            pass

    # التحقق من وجود سجل حضور سابق لهذا الموظف في هذا التاريخ
    existing_attendance = None
    if employee_id and 'date' in initial_data:
        try:
            existing_attendance = Attendance.objects.get(
                employee_id=employee_id,
                date=initial_data['date']
            )
        except Attendance.DoesNotExist:
            pass

    if request.method == 'POST':
        # إذا كان هناك سجل موجود، قم بتحديثه
        if existing_attendance:
            form = AttendanceForm(request.POST, instance=existing_attendance)
        else:
            form = AttendanceForm(request.POST)

        if form.is_valid():
            attendance = form.save()

            # رسالة نجاح مختلفة بناءً على ما إذا كان تحديثًا أو إنشاءً جديدًا
            if existing_attendance:
                messages.success(request, f'تم تحديث سجل حضور {attendance.employee.name} بنجاح')
            else:
                messages.success(request, f'تم إضافة سجل حضور {attendance.employee.name} بنجاح')

            # إعادة التوجيه إلى صفحة الحضور اليومي مع تاريخ السجل
            return redirect(f"{reverse('employees:attendance_daily')}?date={attendance.date.strftime('%Y-%m-%d')}")
    else:
        # إذا كان هناك سجل موجود، قم بتحميله للتعديل
        if existing_attendance:
            form = AttendanceForm(instance=existing_attendance)
            title = f'تعديل سجل حضور: {existing_attendance.employee.name}'
        else:
            form = AttendanceForm(initial=initial_data)
            title = 'إضافة سجل حضور جديد'

    return render(request, 'employees/attendance/form.html', {
        'form': form,
        'title': title
    })

@login_required
def attendance_bulk_add(request):
    """إضافة سجلات حضور بشكل جماعي"""
    # الحصول على التاريخ من الاستعلام إذا كان متوفرًا
    date_str = request.GET.get('date')

    if date_str:
        try:
            selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            selected_date = timezone.now().date()
    else:
        selected_date = timezone.now().date()

    # الحصول على جميع الموظفين النشطين
    active_employees = Employee.objects.filter(status=Employee.ACTIVE).order_by('name')

    if request.method == 'POST':
        form = BulkAttendanceForm(request.POST, employees=active_employees)
        if form.is_valid():
            date = form.cleaned_data['date']

            # حفظ سجلات الحضور لكل موظف
            for employee in active_employees:
                status_field = f'status_{employee.id}'
                check_in_field = f'check_in_{employee.id}'
                check_out_field = f'check_out_{employee.id}'

                if status_field in form.cleaned_data:
                    status = form.cleaned_data[status_field]
                    check_in = form.cleaned_data.get(check_in_field)
                    check_out = form.cleaned_data.get(check_out_field)

                    # التحقق من وجود سجل حضور سابق لهذا الموظف في هذا التاريخ
                    try:
                        attendance = Attendance.objects.get(employee=employee, date=date)
                        # تحديث السجل الموجود
                        attendance.status = status
                        attendance.check_in = check_in
                        attendance.check_out = check_out
                        attendance.save()
                    except Attendance.DoesNotExist:
                        # إنشاء سجل جديد
                        Attendance.objects.create(
                            employee=employee,
                            date=date,
                            status=status,
                            check_in=check_in,
                            check_out=check_out
                        )

            messages.success(request, f'تم تسجيل الحضور الجماعي بنجاح ليوم {date.strftime("%Y-%m-%d")}')
            return redirect(f"{reverse('employees:attendance_daily')}?date={date.strftime('%Y-%m-%d')}")
    else:
        form = BulkAttendanceForm(initial={'date': selected_date}, employees=active_employees)

    return render(request, 'employees/attendance/bulk_form.html', {
        'form': form,
        'selected_date': selected_date
    })

@login_required
def attendance_delete(request, pk):
    """حذف سجل حضور"""
    attendance = get_object_or_404(Attendance, pk=pk)

    if request.method == 'POST':
        date = attendance.date
        employee_name = attendance.employee.name
        attendance.delete()
        messages.success(request, f'تم حذف سجل حضور {employee_name} بنجاح')
        return redirect(f"{reverse('employees:attendance_daily')}?date={date.strftime('%Y-%m-%d')}")

    return render(request, 'employees/attendance/delete.html', {
        'attendance': attendance
    })

# صفحات السلف
@login_required
def loan_list(request):
    """عرض قائمة السلف"""
    loans = EmployeeLoan.objects.all().order_by('-date')
    return render(request, 'employees/loan/list.html', {'loans': loans})

@login_required
def loan_detail(request, pk):
    """عرض تفاصيل سلفة"""
    loan = get_object_or_404(EmployeeLoan, pk=pk)
    return render(request, 'employees/loan/detail.html', {'loan': loan})

@login_required
def loan_add(request):
    """إضافة سلفة جديدة"""
    if request.method == 'POST':
        form = EmployeeLoanForm(request.POST)
        if form.is_valid():
            loan = form.save(commit=False)
            loan.save()

            # ترحيل السلفة تلقائياً إذا تم اختيار ذلك
            auto_post = form.cleaned_data.get('auto_post')
            if auto_post:
                try:
                    with transaction.atomic():
                        if loan.post_loan():
                            messages.success(request, _('تم ترحيل السلفة بنجاح'))
                        else:
                            messages.error(request, _('فشل ترحيل السلفة'))
                except Exception as e:
                    messages.error(request, f'{_("حدث خطأ أثناء ترحيل السلفة")}: {str(e)}')

            messages.success(request, f'تم إضافة سلفة للموظف {loan.employee.name} بنجاح')
            return redirect('employees:loan_detail', pk=loan.pk)
    else:
        form = EmployeeLoanForm(initial={
            'date': timezone.now().date(),
        })

    return render(request, 'employees/loan/form.html', {
        'form': form,
        'title': 'إضافة سلفة جديدة'
    })

@login_required
def loan_edit(request, pk):
    """تعديل سلفة"""
    loan = get_object_or_404(EmployeeLoan, pk=pk)

    # حفظ حالة الترحيل الأصلية
    was_posted = loan.is_posted

    # إلغاء ترحيل السلفة مؤقتاً إذا كانت مرحلة
    if was_posted:
        try:
            with transaction.atomic():
                if not loan.unpost_loan():
                    messages.error(request, _('فشل إلغاء ترحيل السلفة للتعديل'))
                    return redirect('employees:loan_detail', pk=loan.pk)
        except Exception as e:
            messages.error(request, f'{_("حدث خطأ أثناء إلغاء ترحيل السلفة للتعديل")}: {str(e)}')
            return redirect('employees:loan_detail', pk=loan.pk)

    if request.method == 'POST':
        form = EmployeeLoanForm(request.POST, instance=loan)
        if form.is_valid():
            loan = form.save()

            # إعادة ترحيل السلفة إذا كانت مرحلة سابقاً أو تم اختيار الترحيل التلقائي
            auto_post = form.cleaned_data.get('auto_post')
            if was_posted or auto_post:
                try:
                    with transaction.atomic():
                        if loan.post_loan():
                            messages.success(request, _('تم ترحيل السلفة بنجاح'))
                        else:
                            messages.error(request, _('فشل ترحيل السلفة'))
                except Exception as e:
                    messages.error(request, f'{_("حدث خطأ أثناء ترحيل السلفة")}: {str(e)}')

            messages.success(request, f'تم تعديل سلفة الموظف {loan.employee.name} بنجاح')
            return redirect('employees:loan_detail', pk=loan.pk)
    else:
        form = EmployeeLoanForm(instance=loan)
        # إذا كانت السلفة مرحلة، نضبط الترحيل التلقائي على True
        if was_posted:
            form.initial['auto_post'] = True

    return render(request, 'employees/loan/form.html', {
        'form': form,
        'title': f'تعديل سلفة الموظف: {loan.employee.name}',
        'loan': loan,
        'was_posted': was_posted
    })

@login_required
def loan_post(request, pk):
    """ترحيل سلفة"""
    loan = get_object_or_404(EmployeeLoan, pk=pk)

    if loan.is_posted:
        messages.warning(request, _('تم ترحيل السلفة بالفعل'))
    else:
        try:
            with transaction.atomic():
                if loan.post_loan():
                    messages.success(request, _('تم ترحيل السلفة بنجاح'))
                else:
                    messages.error(request, _('فشل ترحيل السلفة'))
        except Exception as e:
            messages.error(request, f'{_("حدث خطأ أثناء ترحيل السلفة")}: {str(e)}')

    return redirect('employees:loan_detail', pk=pk)

@login_required
def loan_unpost(request, pk):
    """إلغاء ترحيل سلفة"""
    loan = get_object_or_404(EmployeeLoan, pk=pk)

    if not loan.is_posted:
        messages.warning(request, _('لم يتم ترحيل السلفة بعد'))
    else:
        try:
            with transaction.atomic():
                if loan.unpost_loan():
                    messages.success(request, _('تم إلغاء ترحيل السلفة بنجاح'))
                else:
                    messages.error(request, _('فشل إلغاء ترحيل السلفة'))
        except Exception as e:
            messages.error(request, f'{_("حدث خطأ أثناء إلغاء ترحيل السلفة")}: {str(e)}')

    return redirect('employees:loan_detail', pk=pk)

@login_required
def loan_delete(request, pk):
    """حذف سلفة"""
    loan = get_object_or_404(EmployeeLoan, pk=pk)

    # حفظ حالة الترحيل الأصلية
    was_posted = loan.is_posted

    if request.method == 'POST':
        employee_name = loan.employee.name

        # إلغاء ترحيل السلفة أولاً إذا كانت مرحلة
        if was_posted:
            try:
                with transaction.atomic():
                    if not loan.unpost_loan():
                        messages.error(request, _('فشل إلغاء ترحيل السلفة للحذف'))
                        return redirect('employees:loan_detail', pk=pk)
            except Exception as e:
                messages.error(request, f'{_("حدث خطأ أثناء إلغاء ترحيل السلفة للحذف")}: {str(e)}')
                return redirect('employees:loan_detail', pk=pk)

        # حذف السلفة
        loan.delete()
        messages.success(request, f'تم حذف سلفة الموظف {employee_name} بنجاح')
        return redirect('employees:loan_list')

    return render(request, 'employees/loan/delete.html', {
        'loan': loan,
        'was_posted': was_posted
    })

# صفحات المرتبات
@login_required
def salary_list(request):
    """عرض قائمة المرتبات"""
    salaries = Salary.objects.all().order_by('-year', '-month')
    return render(request, 'employees/salary/list.html', {'salaries': salaries})

@login_required
def salary_detail(request, pk):
    """عرض تفاصيل راتب"""
    salary = get_object_or_404(Salary, pk=pk)
    return render(request, 'employees/salary/detail.html', {'salary': salary})

@login_required
def salary_add(request):
    """إضافة راتب جديد"""
    if request.method == 'POST':
        form = SalaryForm(request.POST)
        if form.is_valid():
            salary = form.save(commit=False)
            # حساب صافي الراتب
            salary.net_salary = salary.base_salary - salary.deductions - salary.loans_deduction
            salary.save()

            # ترحيل الراتب تلقائياً إذا تم اختيار ذلك
            auto_post = form.cleaned_data.get('auto_post')
            if auto_post and salary.safe:
                try:
                    with transaction.atomic():
                        if salary.post_salary():
                            messages.success(request, _('تم ترحيل الراتب بنجاح'))
                        else:
                            messages.error(request, _('فشل ترحيل الراتب'))
                except Exception as e:
                    messages.error(request, f'{_("حدث خطأ أثناء ترحيل الراتب")}: {str(e)}')

            messages.success(request, f'تم إضافة راتب للموظف {salary.employee.name} بنجاح')
            return redirect('employees:salary_detail', pk=salary.pk)
    else:
        # تعيين القيم الافتراضية
        today = timezone.now().date()
        form = SalaryForm(initial={
            'month': today.month,
            'year': today.year,
        })

    return render(request, 'employees/salary/form.html', {
        'form': form,
        'title': 'إضافة راتب جديد'
    })

@login_required
def salary_edit(request, pk):
    """تعديل راتب"""
    salary = get_object_or_404(Salary, pk=pk)

    # حفظ حالة الترحيل الأصلية
    was_posted = salary.is_posted

    # إلغاء ترحيل الراتب مؤقتاً إذا كان مرحل
    if was_posted:
        try:
            with transaction.atomic():
                if not salary.unpost_salary():
                    messages.error(request, _('فشل إلغاء ترحيل الراتب للتعديل'))
                    return redirect('employees:salary_detail', pk=pk)
        except Exception as e:
            messages.error(request, f'{_("حدث خطأ أثناء إلغاء ترحيل الراتب للتعديل")}: {str(e)}')
            return redirect('employees:salary_detail', pk=pk)

    if request.method == 'POST':
        form = SalaryForm(request.POST, instance=salary)
        if form.is_valid():
            salary = form.save(commit=False)
            # حساب صافي الراتب
            salary.net_salary = salary.base_salary - salary.deductions - salary.loans_deduction
            salary.save()

            # إعادة ترحيل الراتب إذا كان مرحل سابقاً أو تم اختيار الترحيل التلقائي
            auto_post = form.cleaned_data.get('auto_post')
            if (was_posted or auto_post) and salary.safe:
                try:
                    with transaction.atomic():
                        if salary.post_salary():
                            messages.success(request, _('تم ترحيل الراتب بنجاح'))
                        else:
                            messages.error(request, _('فشل ترحيل الراتب'))
                except Exception as e:
                    messages.error(request, f'{_("حدث خطأ أثناء ترحيل الراتب")}: {str(e)}')

            messages.success(request, f'تم تعديل راتب الموظف {salary.employee.name} بنجاح')
            return redirect('employees:salary_detail', pk=salary.pk)
    else:
        form = SalaryForm(instance=salary)
        # إذا كان الراتب مرحل، نضبط الترحيل التلقائي على True
        if was_posted:
            form.initial['auto_post'] = True

    return render(request, 'employees/salary/form.html', {
        'form': form,
        'title': f'تعديل راتب الموظف: {salary.employee.name}',
        'salary': salary,
        'was_posted': was_posted
    })

@login_required
def salary_post(request, pk):
    """ترحيل راتب"""
    salary = get_object_or_404(Salary, pk=pk)

    if salary.is_posted:
        messages.warning(request, _('تم ترحيل الراتب بالفعل'))
    else:
        try:
            with transaction.atomic():
                if salary.post_salary():
                    messages.success(request, _('تم ترحيل الراتب بنجاح'))
                else:
                    messages.error(request, _('فشل ترحيل الراتب'))
        except Exception as e:
            messages.error(request, f'{_("حدث خطأ أثناء ترحيل الراتب")}: {str(e)}')

    return redirect('employees:salary_detail', pk=pk)

@login_required
def salary_unpost(request, pk):
    """إلغاء ترحيل راتب"""
    salary = get_object_or_404(Salary, pk=pk)

    if not salary.is_posted:
        messages.warning(request, _('لم يتم ترحيل الراتب بعد'))
    else:
        try:
            with transaction.atomic():
                if salary.unpost_salary():
                    messages.success(request, _('تم إلغاء ترحيل الراتب بنجاح'))
                else:
                    messages.error(request, _('فشل إلغاء ترحيل الراتب'))
        except Exception as e:
            messages.error(request, f'{_("حدث خطأ أثناء إلغاء ترحيل الراتب")}: {str(e)}')

    return redirect('employees:salary_detail', pk=pk)

@login_required
def salary_delete(request, pk):
    """حذف راتب"""
    salary = get_object_or_404(Salary, pk=pk)

    # حفظ حالة الترحيل الأصلية
    was_posted = salary.is_posted

    if request.method == 'POST':
        employee_name = salary.employee.name

        # إلغاء ترحيل الراتب أولاً إذا كان مرحل
        if was_posted:
            try:
                with transaction.atomic():
                    if not salary.unpost_salary():
                        messages.error(request, _('فشل إلغاء ترحيل الراتب للحذف'))
                        return redirect('employees:salary_detail', pk=pk)
            except Exception as e:
                messages.error(request, f'{_("حدث خطأ أثناء إلغاء ترحيل الراتب للحذف")}: {str(e)}')
                return redirect('employees:salary_detail', pk=pk)

        # حذف الراتب
        salary.delete()
        messages.success(request, f'تم حذف راتب الموظف {employee_name} بنجاح')
        return redirect('employees:salary_list')

    return render(request, 'employees/salary/delete.html', {
        'salary': salary,
        'was_posted': was_posted
    })

@login_required
def salary_generate_monthly(request):
    """إنشاء رواتب شهرية لجميع الموظفين"""
    preview_data = []
    total_base_salary = 0
    total_deductions = 0
    total_loans_deduction = 0
    total_net_salary = 0

    if request.method == 'POST':
        form = SalaryGenerateForm(request.POST)
        if form.is_valid():
            month = form.cleaned_data['month']
            year = form.cleaned_data['year']
            safe = form.cleaned_data['safe']
            auto_post = form.cleaned_data['auto_post']

            # التحقق من عدم وجود رواتب للشهر المحدد
            existing_salaries = Salary.objects.filter(month=month, year=year)
            if existing_salaries.exists():
                messages.warning(request, _('يوجد رواتب بالفعل لهذا الشهر. يمكنك تعديلها من قائمة الرواتب.'))
                return redirect('employees:salary_list')

            # الحصول على جميع الموظفين النشطين
            active_employees = Employee.objects.filter(status=Employee.ACTIVE)

            # إنشاء رواتب لجميع الموظفين
            created_salaries = []
            for employee in active_employees:
                # حساب خصم السلف
                loans_deduction = 0  # يمكن تنفيذ حساب خصم السلف لاحقًا

                # حساب صافي الراتب
                net_salary = employee.salary - employee.deductions - loans_deduction

                # إنشاء الراتب
                salary = Salary(
                    employee=employee,
                    month=month,
                    year=year,
                    base_salary=employee.salary,
                    deductions=employee.deductions,
                    loans_deduction=loans_deduction,
                    net_salary=net_salary,
                    safe=safe
                )

                # حفظ الراتب
                salary.save()
                created_salaries.append(salary)

                # ترحيل الراتب إذا تم اختيار ذلك
                if auto_post:
                    try:
                        with transaction.atomic():
                            salary.post_salary()
                    except Exception as e:
                        messages.error(request, f'{_("حدث خطأ أثناء ترحيل راتب الموظف")}: {employee.name} - {str(e)}')

            messages.success(request, f'تم إنشاء {len(created_salaries)} راتب بنجاح')
            return redirect('employees:salary_list')
    else:
        # تعيين القيم الافتراضية
        today = timezone.now().date()
        form = SalaryGenerateForm(initial={
            'month': today.month,
            'year': today.year,
        })

        # إنشاء معاينة للرواتب
        active_employees = Employee.objects.filter(status=Employee.ACTIVE)
        for employee in active_employees:
            # حساب خصم السلف
            loans_deduction = 0  # يمكن تنفيذ حساب خصم السلف لاحقًا

            # حساب صافي الراتب
            net_salary = employee.salary - employee.deductions - loans_deduction

            preview_data.append({
                'employee': employee,
                'base_salary': employee.salary,
                'deductions': employee.deductions,
                'loans_deduction': loans_deduction,
                'net_salary': net_salary
            })

            # حساب الإجماليات
            total_base_salary += employee.salary
            total_deductions += employee.deductions
            total_loans_deduction += loans_deduction
            total_net_salary += net_salary

    return render(request, 'employees/salary/generate_monthly.html', {
        'form': form,
        'preview_data': preview_data,
        'total_base_salary': total_base_salary,
        'total_deductions': total_deductions,
        'total_loans_deduction': total_loans_deduction,
        'total_net_salary': total_net_salary
    })

# التقارير
@login_required
def report_attendance_daily(request):
    """تقرير الحضور اليومي"""
    # الحصول على التاريخ المطلوب (اليوم الحالي افتراضيًا)
    date_str = request.GET.get('date')
    if date_str:
        try:
            selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            selected_date = timezone.now().date()
    else:
        selected_date = timezone.now().date()

    # الحصول على سجلات الحضور لهذا اليوم
    attendance_records = Attendance.objects.filter(date=selected_date).order_by('employee__name')

    # الحصول على جميع الموظفين النشطين
    active_employees = Employee.objects.filter(status=Employee.ACTIVE)

    # إنشاء قائمة بالموظفين وحالة حضورهم
    employees_attendance = []
    for employee in active_employees:
        try:
            attendance = attendance_records.get(employee=employee)
        except Attendance.DoesNotExist:
            attendance = None

        employees_attendance.append({
            'employee': employee,
            'attendance': attendance
        })

    context = {
        'selected_date': selected_date,
        'employees_attendance': employees_attendance,
        'present_count': attendance_records.filter(status=Attendance.PRESENT).count(),
        'absent_count': attendance_records.filter(status=Attendance.ABSENT).count(),
        'excused_count': attendance_records.filter(status=Attendance.EXCUSED).count(),
        'now': timezone.now(),
    }

    # التحقق مما إذا كان المستخدم يريد استخدام قالب الطباعة المخصص
    print_mode = request.GET.get('print', False)
    if print_mode:
        return render(request, 'employees/reports/print_templates/attendance_daily_print.html', context)

    return render(request, 'employees/reports/attendance_daily.html', context)

@login_required
def report_attendance_monthly(request):
    """تقرير الحضور الشهري"""
    # الحصول على الشهر والسنة المطلوبين (الشهر الحالي افتراضيًا)
    year = request.GET.get('year', timezone.now().year)
    month = request.GET.get('month', timezone.now().month)

    try:
        year = int(year)
        month = int(month)
    except ValueError:
        year = timezone.now().year
        month = timezone.now().month

    # الحصول على جميع الموظفين النشطين
    active_employees = Employee.objects.filter(status=Employee.ACTIVE)

    # إنشاء بيانات التقرير
    report_data = []
    for employee in active_employees:
        present_count = employee.get_attendance_count(year, month)
        absent_count = employee.get_absence_count(year, month)
        excused_count = employee.get_excused_absence_count(year, month)

        report_data.append({
            'employee': employee,
            'present_count': present_count,
            'absent_count': absent_count,
            'excused_count': excused_count,
            'total_days': present_count + absent_count + excused_count
        })

    context = {
        'year': year,
        'month': month,
        'month_name': calendar.month_name[month],
        'report_data': report_data,
        'now': timezone.now(),
    }

    # التحقق مما إذا كان المستخدم يريد استخدام قالب الطباعة المخصص
    print_mode = request.GET.get('print', False)
    if print_mode:
        # التحقق مما إذا كان المستخدم يريد التقرير التفصيلي أو الملخص
        detailed = request.GET.get('detailed', False)
        if detailed:
            # الحصول على عدد أيام الشهر
            _, days_in_month = calendar.monthrange(year, month)

            # الحصول على سجلات الحضور لهذا الشهر
            attendance_records = Attendance.objects.filter(
                date__year=year,
                date__month=month
            )

            # إنشاء قاموس لتسهيل الوصول إلى سجلات الحضور
            attendance_dict = {}
            for record in attendance_records:
                key = f"{record.employee_id}_{record.date.day}"
                attendance_dict[key] = record

            # إنشاء بيانات الجدول
            employees_data = []
            for employee in active_employees:
                days_data = []
                for day in range(1, days_in_month + 1):
                    key = f"{employee.id}_{day}"
                    attendance = attendance_dict.get(key)
                    days_data.append({
                        'day': day,
                        'attendance': attendance
                    })

                employees_data.append({
                    'employee': employee,
                    'days': days_data,
                    'present_count': attendance_records.filter(employee=employee, status=Attendance.PRESENT).count(),
                    'absent_count': attendance_records.filter(employee=employee, status=Attendance.ABSENT).count(),
                    'excused_count': attendance_records.filter(employee=employee, status=Attendance.EXCUSED).count(),
                })

            detailed_context = {
                'year': year,
                'month': month,
                'month_name': calendar.month_name[month],
                'days_in_month': days_in_month,
                'employees_data': employees_data,
                'now': timezone.now(),
            }

            return render(request, 'employees/reports/print_templates/attendance_monthly_detailed_print.html', detailed_context)

        return render(request, 'employees/reports/print_templates/attendance_monthly_print.html', context)

    return render(request, 'employees/reports/attendance_monthly.html', context)

@login_required
def report_employee_attendance(request, pk):
    """تقرير حضور موظف"""
    employee = get_object_or_404(Employee, pk=pk)

    # الحصول على الشهر والسنة المطلوبين (الشهر الحالي افتراضيًا)
    year = request.GET.get('year', timezone.now().year)
    month = request.GET.get('month', timezone.now().month)

    try:
        year = int(year)
        month = int(month)
    except ValueError:
        year = timezone.now().year
        month = timezone.now().month

    # الحصول على سجلات الحضور للموظف في الشهر المحدد
    attendance_records = employee.get_monthly_attendance_report(year, month)

    context = {
        'employee': employee,
        'year': year,
        'month': month,
        'month_name': calendar.month_name[month],
        'attendance_records': attendance_records,
        'present_count': employee.get_attendance_count(year, month),
        'absent_count': employee.get_absence_count(year, month),
        'excused_count': employee.get_excused_absence_count(year, month),
        'now': timezone.now(),
    }

    # التحقق مما إذا كان المستخدم يريد استخدام قالب الطباعة المخصص
    print_mode = request.GET.get('print', False)
    if print_mode:
        return render(request, 'employees/reports/print_templates/employee_attendance_print.html', context)

    return render(request, 'employees/reports/employee_attendance.html', context)

@login_required
def report_employee_loans(request, pk):
    """تقرير سلف الموظف"""
    employee = get_object_or_404(Employee, pk=pk)

    # الحصول على جميع سلف الموظف
    loans = employee.loans.all().order_by('-date')

    # حساب إجمالي السلف
    total_amount = sum(loan.amount for loan in loans)

    # حساب إجمالي السلف المسددة وغير المسددة
    paid_loans = [loan for loan in loans if loan.is_paid]
    unpaid_loans = [loan for loan in loans if not loan.is_paid]

    total_paid = sum(loan.amount for loan in paid_loans)
    total_unpaid = sum(loan.amount for loan in unpaid_loans)

    context = {
        'employee': employee,
        'loans': loans,
        'total_amount': total_amount,
        'total_paid': total_paid,
        'total_unpaid': total_unpaid,
        'paid_count': len(paid_loans),
        'unpaid_count': len(unpaid_loans),
        'now': timezone.now(),
    }

    # إذا كان طلب طباعة، استخدم قالب الطباعة
    if request.GET.get('print'):
        return render(request, 'employees/reports/print_templates/employee_loans_print.html', context)

    return render(request, 'employees/reports/employee_loans.html', context)

@login_required
def report_monthly_loans(request):
    """تقرير السلف الشهري"""
    # الحصول على الشهر والسنة من الطلب
    year = request.GET.get('year')
    month = request.GET.get('month')

    # إذا لم يتم تحديد الشهر والسنة، استخدم الشهر والسنة الحاليين
    today = timezone.now().date()
    if not year:
        year = today.year
    else:
        year = int(year)

    if not month:
        month = today.month
    else:
        month = int(month)

    # الحصول على السلف في الشهر المحدد
    start_date = datetime(year, month, 1).date()
    if month == 12:
        end_date = datetime(year + 1, 1, 1).date() - timedelta(days=1)
    else:
        end_date = datetime(year, month + 1, 1).date() - timedelta(days=1)

    loans = EmployeeLoan.objects.filter(date__gte=start_date, date__lte=end_date).order_by('date')

    # حساب إجمالي السلف
    total_amount = sum(loan.amount for loan in loans)

    # حساب إجمالي السلف المسددة وغير المسددة
    paid_loans = [loan for loan in loans if loan.is_paid]
    unpaid_loans = [loan for loan in loans if not loan.is_paid]

    total_paid = sum(loan.amount for loan in paid_loans)
    total_unpaid = sum(loan.amount for loan in unpaid_loans)

    # الحصول على اسم الشهر بالعربية
    month_names = {
        1: 'يناير', 2: 'فبراير', 3: 'مارس', 4: 'أبريل', 5: 'مايو', 6: 'يونيو',
        7: 'يوليو', 8: 'أغسطس', 9: 'سبتمبر', 10: 'أكتوبر', 11: 'نوفمبر', 12: 'ديسمبر'
    }
    month_name = month_names.get(month, '')

    context = {
        'year': year,
        'month': month,
        'month_name': month_name,
        'loans': loans,
        'total_amount': total_amount,
        'total_paid': total_paid,
        'total_unpaid': total_unpaid,
        'paid_count': len(paid_loans),
        'unpaid_count': len(unpaid_loans),
        'now': timezone.now(),
    }

    # إذا كان طلب طباعة، استخدم قالب الطباعة
    if request.GET.get('print'):
        return render(request, 'employees/reports/print_templates/monthly_loans_print.html', context)

    return render(request, 'employees/reports/monthly_loans.html', context)
