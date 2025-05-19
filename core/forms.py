from django import forms
from .models import Company, Branch, Store, Safe, Representative, Driver, Contact, SystemSettings

class CompanyForm(forms.ModelForm):
    class Meta:
        model = Company
        fields = ['name', 'address', 'phone', 'email', 'tax_number', 'logo']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'dir': 'ltr'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'dir': 'ltr'}),
            'tax_number': forms.TextInput(attrs={'class': 'form-control'}),
            'logo': forms.FileInput(attrs={'class': 'form-control'}),
        }

class BranchForm(forms.ModelForm):
    class Meta:
        model = Branch
        fields = ['company', 'name', 'address', 'phone', 'manager']
        widgets = {
            'company': forms.Select(attrs={'class': 'form-select'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'dir': 'ltr'}),
            'manager': forms.TextInput(attrs={'class': 'form-control'}),
        }

class StoreForm(forms.ModelForm):
    class Meta:
        model = Store
        fields = ['branch', 'name', 'address', 'keeper', 'notes']
        widgets = {
            'branch': forms.Select(attrs={'class': 'form-select'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'keeper': forms.TextInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class SafeForm(forms.ModelForm):
    class Meta:
        model = Safe
        fields = ['branch', 'name', 'initial_balance']
        widgets = {
            'branch': forms.Select(attrs={'class': 'form-select'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'initial_balance': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }

class RepresentativeForm(forms.ModelForm):
    class Meta:
        model = Representative
        fields = ['name', 'phone', 'address', 'id_number', 'commission_percentage', 'notes']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'dir': 'ltr'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'id_number': forms.TextInput(attrs={'class': 'form-control'}),
            'commission_percentage': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class DriverForm(forms.ModelForm):
    class Meta:
        model = Driver
        fields = ['name', 'phone', 'address', 'id_number', 'license_number', 'notes']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'dir': 'ltr'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'id_number': forms.TextInput(attrs={'class': 'form-control'}),
            'license_number': forms.TextInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class ContactForm(forms.ModelForm):
    class Meta:
        model = Contact
        fields = ['name', 'contact_type', 'phone', 'alternative_phone', 'address',
                 'email', 'tax_number', 'initial_balance', 'credit_limit', 'notes']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'contact_type': forms.Select(attrs={'class': 'form-select'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'dir': 'ltr'}),
            'alternative_phone': forms.TextInput(attrs={'class': 'form-control', 'dir': 'ltr'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'dir': 'ltr'}),
            'tax_number': forms.TextInput(attrs={'class': 'form-control'}),
            'initial_balance': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'credit_limit': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class SystemSettingsForm(forms.ModelForm):
    """نموذج إعدادات النظام"""
    class Meta:
        model = SystemSettings
        fields = [
            # إعدادات الفواتير
            'default_invoice_type', 'update_purchase_price', 'update_sale_price',
            'alert_below_sale_price', 'alert_below_purchase_price',
            'duplicate_item_handling',
            'default_customer', 'default_supplier', 'default_safe', 'default_store',
            # إعدادات طباعة الفاتورة
            'hide_company_info', 'show_previous_balance',
            'invoice_header_text', 'invoice_footer_text',
            # إعدادات طباعة تقرير الأذونات المخزنية
            'show_driver_in_permit_report', 'show_representative_in_permit_report'
        ]
        widgets = {
            # إعدادات الفواتير
            'default_invoice_type': forms.Select(attrs={'class': 'form-select'}),
            'update_purchase_price': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'update_sale_price': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'alert_below_sale_price': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'alert_below_purchase_price': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'duplicate_item_handling': forms.RadioSelect(attrs={'class': 'form-check-input'}),
            'default_customer': forms.Select(attrs={'class': 'form-select'}),
            'default_supplier': forms.Select(attrs={'class': 'form-select'}),
            'default_safe': forms.Select(attrs={'class': 'form-select'}),
            'default_store': forms.Select(attrs={'class': 'form-select'}),
            # إعدادات طباعة الفاتورة
            'hide_company_info': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'show_previous_balance': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'invoice_header_text': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'invoice_footer_text': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
