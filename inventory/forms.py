from django import forms
from .models import Supplier, DisinfectantCategory, Disinfectant, DisinfectantReceived, DisinfectantIssued

class SupplierForm(forms.ModelForm):
    class Meta:
        model = Supplier
        fields = ['name', 'contact_person', 'phone', 'email', 'address', 'is_active', 'notes']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'contact_person': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class DisinfectantCategoryForm(forms.ModelForm):
    class Meta:
        model = DisinfectantCategory
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class DisinfectantForm(forms.ModelForm):
    class Meta:
        model = Disinfectant
        fields = ['name', 'category', 'unit', 'minimum_stock', 'description', 'is_active', 'notes']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'unit': forms.TextInput(attrs={'class': 'form-control'}),
            'minimum_stock': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class DisinfectantReceivedForm(forms.ModelForm):
    class Meta:
        model = DisinfectantReceived
        fields = ['disinfectant', 'supplier', 'date', 'quantity', 'unit_price', 'invoice_number', 'expiry_date', 'notes']
        widgets = {
            'disinfectant': forms.Select(attrs={'class': 'form-select'}),
            'supplier': forms.Select(attrs={'class': 'form-select'}),
            'date': forms.DateInput(attrs={'class': 'form-control datepicker', 'type': 'date'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'unit_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'invoice_number': forms.TextInput(attrs={'class': 'form-control'}),
            'expiry_date': forms.DateInput(attrs={'class': 'form-control datepicker', 'type': 'date'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        disinfectant_id = kwargs.pop('disinfectant_id', None)
        super().__init__(*args, **kwargs)
        if disinfectant_id:
            self.fields['disinfectant'].initial = disinfectant_id
            self.fields['disinfectant'].widget.attrs['readonly'] = True


class DisinfectantIssuedForm(forms.ModelForm):
    class Meta:
        model = DisinfectantIssued
        fields = ['disinfectant', 'date', 'quantity', 'issued_to', 'purpose', 'notes']
        widgets = {
            'disinfectant': forms.Select(attrs={'class': 'form-select'}),
            'date': forms.DateInput(attrs={'class': 'form-control datepicker', 'type': 'date'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'issued_to': forms.TextInput(attrs={'class': 'form-control'}),
            'purpose': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        disinfectant_id = kwargs.pop('disinfectant_id', None)
        super().__init__(*args, **kwargs)
        if disinfectant_id:
            self.fields['disinfectant'].initial = disinfectant_id
            self.fields['disinfectant'].widget.attrs['readonly'] = True
    
    def clean(self):
        cleaned_data = super().clean()
        disinfectant = cleaned_data.get('disinfectant')
        quantity = cleaned_data.get('quantity')
        
        if disinfectant and quantity:
            available = disinfectant.current_stock
            if self.instance.pk:
                # إذا كان هذا تحديثًا لسجل موجود
                current = DisinfectantIssued.objects.get(pk=self.instance.pk)
                if current.disinfectant == disinfectant:
                    available += current.quantity
                    
            if quantity > available:
                self.add_error('quantity', f'الكمية المتاحة من المطهر {disinfectant} هي {available} {disinfectant.unit} فقط.')
