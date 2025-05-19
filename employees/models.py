from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from finances.models import SafeTransaction
from core.models import Safe

class Employee(models.Model):
    """نموذج بيانات الموظف"""

    # الحالة الوظيفية
    ACTIVE = 'active'
    INACTIVE = 'inactive'
    ON_LEAVE = 'on_leave'

    STATUS_CHOICES = [
        (ACTIVE, _('نشط')),
        (INACTIVE, _('غير نشط')),
        (ON_LEAVE, _('في إجازة')),
    ]

    name = models.CharField(_("اسم الموظف"), max_length=255)
    national_id = models.CharField(_("الرقم القومي"), max_length=20, blank=True, null=True)
    phone = models.CharField(_("رقم الهاتف"), max_length=20, blank=True, null=True)
    address = models.TextField(_("العنوان"), blank=True, null=True)
    job_title = models.CharField(_("المسمى الوظيفي"), max_length=100, blank=True, null=True)
    department = models.CharField(_("القسم"), max_length=100, blank=True, null=True)
    hire_date = models.DateField(_("تاريخ التعيين"), default=timezone.now)
    salary = models.DecimalField(_("الراتب"), max_digits=10, decimal_places=2, default=0)
    status = models.CharField(_("الحالة"), max_length=20, choices=STATUS_CHOICES, default=ACTIVE)
    notes = models.TextField(_("ملاحظات"), blank=True, null=True)

    class Meta:
        verbose_name = _("موظف")
        verbose_name_plural = _("الموظفين")
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_attendance_count(self, year=None, month=None):
        """حساب عدد أيام الحضور في شهر معين"""
        query = self.attendance_records.filter(status=Attendance.PRESENT)

        if year and month:
            query = query.filter(date__year=year, date__month=month)

        return query.count()

    def get_absence_count(self, year=None, month=None):
        """حساب عدد أيام الغياب في شهر معين"""
        query = self.attendance_records.filter(status=Attendance.ABSENT)

        if year and month:
            query = query.filter(date__year=year, date__month=month)

        return query.count()

    def get_excused_absence_count(self, year=None, month=None):
        """حساب عدد أيام الغياب بعذر في شهر معين"""
        query = self.attendance_records.filter(status=Attendance.EXCUSED)

        if year and month:
            query = query.filter(date__year=year, date__month=month)

        return query.count()

    def get_total_loans(self):
        """حساب إجمالي السلف المستحقة"""
        return self.loans.filter(is_paid=False).aggregate(models.Sum('amount'))['amount__sum'] or 0

    def get_monthly_attendance_report(self, year, month):
        """تقرير الحضور الشهري للموظف"""
        return self.attendance_records.filter(date__year=year, date__month=month).order_by('date')

class Attendance(models.Model):
    """نموذج سجل الحضور والغياب"""

    # حالة الحضور
    PRESENT = 'present'
    ABSENT = 'absent'
    EXCUSED = 'excused'

    STATUS_CHOICES = [
        (PRESENT, _('حاضر')),
        (ABSENT, _('غائب')),
        (EXCUSED, _('غائب بعذر')),
    ]

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='attendance_records', verbose_name=_("الموظف"))
    date = models.DateField(_("التاريخ"), default=timezone.now)
    status = models.CharField(_("الحالة"), max_length=20, choices=STATUS_CHOICES, default=PRESENT)
    check_in = models.TimeField(_("وقت الحضور"), null=True, blank=True)
    check_out = models.TimeField(_("وقت الانصراف"), null=True, blank=True)
    notes = models.TextField(_("ملاحظات"), blank=True, null=True)

    class Meta:
        verbose_name = _("سجل الحضور")
        verbose_name_plural = _("سجلات الحضور")
        ordering = ['-date']
        unique_together = ['employee', 'date']  # لا يمكن تكرار سجل لنفس الموظف في نفس اليوم

    def __str__(self):
        return f"{self.employee.name} - {self.date} - {self.get_status_display()}"

class EmployeeLoan(models.Model):
    """نموذج سلف الموظفين"""

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='loans', verbose_name=_("الموظف"))
    amount = models.DecimalField(_("المبلغ"), max_digits=10, decimal_places=2)
    date = models.DateField(_("تاريخ السلفة"), default=timezone.now)
    description = models.TextField(_("الوصف"), blank=True, null=True)
    is_paid = models.BooleanField(_("تم السداد"), default=False)
    payment_date = models.DateField(_("تاريخ السداد"), null=True, blank=True)
    safe = models.ForeignKey(Safe, on_delete=models.PROTECT, related_name='employee_loans', verbose_name=_("الخزنة"))
    is_posted = models.BooleanField(_("مرحل"), default=False)
    transaction = models.OneToOneField(SafeTransaction, on_delete=models.SET_NULL, null=True, blank=True, related_name='employee_loan', verbose_name=_("حركة الخزنة"))

    class Meta:
        verbose_name = _("سلفة موظف")
        verbose_name_plural = _("سلف الموظفين")
        ordering = ['-date']

    def __str__(self):
        return f"{self.employee.name} - {self.amount} - {self.date}"

    def post_loan(self):
        """ترحيل السلفة وإنشاء حركة خزنة"""
        if self.is_posted:
            return False

        # إنشاء حركة خزنة للسلفة
        current_balance = self.safe.current_balance
        balance_after = current_balance - self.amount

        transaction = SafeTransaction(
            safe=self.safe,
            amount=self.amount,
            transaction_type=SafeTransaction.WITHDRAWAL,
            description=f"سلفة للموظف: {self.employee.name}",
            reference_number=f"LOAN-{self.id}",
            balance_before=current_balance,
            balance_after=balance_after
        )
        transaction.save()

        # تحديث السلفة
        self.transaction = transaction
        self.is_posted = True
        self.save(update_fields=['transaction', 'is_posted'])

        return True

    def unpost_loan(self):
        """إلغاء ترحيل السلفة وحذف حركة الخزنة"""
        if not self.is_posted or not self.transaction:
            return False

        # حذف حركة الخزنة
        self.transaction.delete()

        # تحديث السلفة
        self.transaction = None
        self.is_posted = False
        self.save(update_fields=['transaction', 'is_posted'])

        return True

class Salary(models.Model):
    """نموذج المرتبات"""

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='salaries', verbose_name=_("الموظف"))
    month = models.IntegerField(_("الشهر"), choices=[(i, i) for i in range(1, 13)])
    year = models.IntegerField(_("السنة"))
    base_salary = models.DecimalField(_("الراتب الأساسي"), max_digits=10, decimal_places=2)
    deductions = models.DecimalField(_("الخصومات"), max_digits=10, decimal_places=2, default=0)
    loans_deduction = models.DecimalField(_("خصم السلف"), max_digits=10, decimal_places=2, default=0)
    net_salary = models.DecimalField(_("صافي الراتب"), max_digits=10, decimal_places=2)
    payment_date = models.DateField(_("تاريخ الصرف"), null=True, blank=True)
    is_paid = models.BooleanField(_("تم الصرف"), default=False)
    notes = models.TextField(_("ملاحظات"), blank=True, null=True)
    safe = models.ForeignKey(Safe, on_delete=models.PROTECT, related_name='employee_salaries', verbose_name=_("الخزنة"), null=True, blank=True)
    is_posted = models.BooleanField(_("مرحل"), default=False)
    transaction = models.OneToOneField(SafeTransaction, on_delete=models.SET_NULL, null=True, blank=True, related_name='employee_salary', verbose_name=_("حركة الخزنة"))

    class Meta:
        verbose_name = _("راتب")
        verbose_name_plural = _("المرتبات")
        ordering = ['-year', '-month']
        unique_together = ['employee', 'month', 'year']  # لا يمكن تكرار راتب لنفس الموظف في نفس الشهر

    def __str__(self):
        return f"{self.employee.name} - {self.month}/{self.year} - {self.net_salary}"

    def calculate_net_salary(self):
        """حساب صافي الراتب"""
        self.net_salary = self.base_salary - self.deductions - self.loans_deduction
        return self.net_salary

    def post_salary(self):
        """ترحيل الراتب وإنشاء حركة خزنة"""
        if self.is_posted or not self.safe:
            return False

        # إنشاء حركة خزنة للراتب
        current_balance = self.safe.current_balance
        balance_after = current_balance - self.net_salary

        transaction = SafeTransaction(
            safe=self.safe,
            amount=self.net_salary,
            transaction_type=SafeTransaction.WITHDRAWAL,
            description=f"راتب الموظف: {self.employee.name} عن شهر {self.month}/{self.year}",
            reference_number=f"SALARY-{self.id}",
            balance_before=current_balance,
            balance_after=balance_after
        )
        transaction.save()

        # تحديث الراتب
        self.transaction = transaction
        self.is_posted = True
        self.is_paid = True
        self.payment_date = timezone.now().date()
        self.save(update_fields=['transaction', 'is_posted', 'is_paid', 'payment_date'])

        return True

    def unpost_salary(self):
        """إلغاء ترحيل الراتب وحذف حركة الخزنة"""
        if not self.is_posted or not self.transaction:
            return False

        # حذف حركة الخزنة
        self.transaction.delete()

        # تحديث الراتب
        self.transaction = None
        self.is_posted = False
        self.save(update_fields=['transaction', 'is_posted'])

        return True
