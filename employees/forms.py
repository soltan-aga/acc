from django import forms
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from .models import Employee, Attendance, EmployeeLoan, Salary
from core.models import Safe

class EmployeeForm(forms.ModelForm):
    """نموذج بيانات الموظف"""
    
    class Meta:
        model = Employee
        fields = ['name', 'national_id', 'phone', 'address', 'job_title', 
                 'department', 'hire_date', 'salary', 'status', 'notes']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'national_id': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'job_title': forms.TextInput(attrs={'class': 'form-control'}),
            'department': forms.TextInput(attrs={'class': 'form-control'}),
            'hire_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'salary': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class AttendanceForm(forms.ModelForm):
    """نموذج سجل الحضور"""
    
    class Meta:
        model = Attendance
        fields = ['employee', 'date', 'status', 'check_in', 'check_out', 'notes']
        widgets = {
            'employee': forms.Select(attrs={'class': 'form-select'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'check_in': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'check_out': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class BulkAttendanceForm(forms.Form):
    """نموذج إدخال الحضور الجماعي"""
    
    date = forms.DateField(
        label=_('التاريخ'),
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        initial=timezone.now().date()
    )
    
    def __init__(self, *args, **kwargs):
        employees = kwargs.pop('employees', None)
        super().__init__(*args, **kwargs)
        
        if employees:
            for employee in employees:
                field_name = f'status_{employee.id}'
                self.fields[field_name] = forms.ChoiceField(
                    label=employee.name,
                    choices=Attendance.STATUS_CHOICES,
                    initial=Attendance.PRESENT,
                    widget=forms.Select(attrs={'class': 'form-select'})
                )
                
                field_name = f'check_in_{employee.id}'
                self.fields[field_name] = forms.TimeField(
                    label=_('وقت الحضور'),
                    required=False,
                    widget=forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'})
                )
                
                field_name = f'check_out_{employee.id}'
                self.fields[field_name] = forms.TimeField(
                    label=_('وقت الانصراف'),
                    required=False,
                    widget=forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'})
                )

class EmployeeLoanForm(forms.ModelForm):
    """نموذج سلفة موظف"""
    
    auto_post = forms.BooleanField(
        label=_('ترحيل تلقائي'),
        required=False,
        initial=True,
        help_text=_('ترحيل السلفة تلقائياً بعد الحفظ')
    )
    
    class Meta:
        model = EmployeeLoan
        fields = ['employee', 'amount', 'date', 'description', 'safe']
        widgets = {
            'employee': forms.Select(attrs={'class': 'form-select'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0.01'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'safe': forms.Select(attrs={'class': 'form-select'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # تعيين التاريخ الافتراضي
        if not self.instance.pk:
            self.fields['date'].initial = timezone.now().date()

class SalaryForm(forms.ModelForm):
    """نموذج راتب موظف"""
    
    auto_post = forms.BooleanField(
        label=_('ترحيل تلقائي'),
        required=False,
        initial=True,
        help_text=_('ترحيل الراتب تلقائياً بعد الحفظ')
    )
    
    class Meta:
        model = Salary
        fields = ['employee', 'month', 'year', 'base_salary', 'deductions', 
                 'loans_deduction', 'net_salary', 'notes', 'safe']
        widgets = {
            'employee': forms.Select(attrs={'class': 'form-select'}),
            'month': forms.Select(attrs={'class': 'form-select'}),
            'year': forms.NumberInput(attrs={'class': 'form-control', 'min': '2000', 'max': '2100'}),
            'base_salary': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'deductions': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'loans_deduction': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'net_salary': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0', 'readonly': 'readonly'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'safe': forms.Select(attrs={'class': 'form-select'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # تعيين القيم الافتراضية
        if not self.instance.pk:
            today = timezone.now().date()
            self.fields['month'].initial = today.month
            self.fields['year'].initial = today.year
    
    def clean(self):
        cleaned_data = super().clean()
        base_salary = cleaned_data.get('base_salary') or 0
        deductions = cleaned_data.get('deductions') or 0
        loans_deduction = cleaned_data.get('loans_deduction') or 0
        
        # حساب صافي الراتب
        net_salary = base_salary - deductions - loans_deduction
        
        # التحقق من أن صافي الراتب لا يقل عن صفر
        if net_salary < 0:
            raise forms.ValidationError(_('صافي الراتب لا يمكن أن يكون أقل من صفر'))
        
        cleaned_data['net_salary'] = net_salary
        
        return cleaned_data

class SalaryGenerateForm(forms.Form):
    """نموذج إنشاء رواتب شهرية"""
    
    month = forms.ChoiceField(
        label=_('الشهر'),
        choices=[(i, i) for i in range(1, 13)],
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    year = forms.IntegerField(
        label=_('السنة'),
        min_value=2000,
        max_value=2100,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'min': '2000', 'max': '2100'})
    )
    
    safe = forms.ModelChoiceField(
        label=_('الخزنة'),
        queryset=Safe.objects.all(),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    auto_post = forms.BooleanField(
        label=_('ترحيل تلقائي'),
        required=False,
        initial=False,
        help_text=_('ترحيل الرواتب تلقائياً بعد الإنشاء')
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # تعيين القيم الافتراضية
        today = timezone.now().date()
        self.fields['month'].initial = today.month
        self.fields['year'].initial = today.year
