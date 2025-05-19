from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.urls import path
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from django.db import transaction
from .models import Employee, Attendance, EmployeeLoan, Salary

@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('name', 'job_title', 'department', 'salary', 'status', 'hire_date')
    list_filter = ('status', 'department', 'hire_date')
    search_fields = ('name', 'national_id', 'phone')
    fieldsets = (
        (_('معلومات أساسية'), {
            'fields': ('name', 'national_id', 'phone', 'address')
        }),
        (_('معلومات وظيفية'), {
            'fields': ('job_title', 'department', 'hire_date', 'salary', 'status')
        }),
        (_('ملاحظات'), {
            'fields': ('notes',)
        }),
    )

class AttendanceStatusFilter(admin.SimpleListFilter):
    title = _('حالة الحضور')
    parameter_name = 'status'

    def lookups(self, request, model_admin):
        return Attendance.STATUS_CHOICES

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(status=self.value())
        return queryset

@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('employee', 'date', 'get_status_display', 'check_in', 'check_out')
    list_filter = (AttendanceStatusFilter, 'date')
    search_fields = ('employee__name',)
    date_hierarchy = 'date'

    def get_status_display(self, obj):
        return obj.get_status_display()
    get_status_display.short_description = _('الحالة')

@admin.register(EmployeeLoan)
class EmployeeLoanAdmin(admin.ModelAdmin):
    list_display = ('employee', 'amount', 'date', 'is_paid', 'is_posted')
    list_filter = ('is_paid', 'is_posted', 'date')
    search_fields = ('employee__name', 'description')
    readonly_fields = ('transaction',)

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('<path:object_id>/post/', self.admin_site.admin_view(self.post_loan_view), name='employees_employeeloan_post'),
            path('<path:object_id>/unpost/', self.admin_site.admin_view(self.unpost_loan_view), name='employees_employeeloan_unpost'),
        ]
        return custom_urls + urls

    def post_loan_view(self, request, object_id):
        """عرض ترحيل السلفة"""
        loan = get_object_or_404(EmployeeLoan, pk=object_id)

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

        return redirect('admin:employees_employeeloan_change', object_id=object_id)

    def unpost_loan_view(self, request, object_id):
        """عرض إلغاء ترحيل السلفة"""
        loan = get_object_or_404(EmployeeLoan, pk=object_id)

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

        return redirect('admin:employees_employeeloan_change', object_id=object_id)

@admin.register(Salary)
class SalaryAdmin(admin.ModelAdmin):
    list_display = ('employee', 'month', 'year', 'base_salary', 'deductions', 'loans_deduction', 'net_salary', 'is_paid', 'is_posted')
    list_filter = ('is_paid', 'is_posted', 'month', 'year')
    search_fields = ('employee__name',)
    readonly_fields = ('transaction',)

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('<path:object_id>/post/', self.admin_site.admin_view(self.post_salary_view), name='employees_salary_post'),
            path('<path:object_id>/unpost/', self.admin_site.admin_view(self.unpost_salary_view), name='employees_salary_unpost'),
        ]
        return custom_urls + urls

    def post_salary_view(self, request, object_id):
        """عرض ترحيل الراتب"""
        salary = get_object_or_404(Salary, pk=object_id)

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

        return redirect('admin:employees_salary_change', object_id=object_id)

    def unpost_salary_view(self, request, object_id):
        """عرض إلغاء ترحيل الراتب"""
        salary = get_object_or_404(Salary, pk=object_id)

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

        return redirect('admin:employees_salary_change', object_id=object_id)
