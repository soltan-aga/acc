from django import forms
from django.forms import inlineformset_factory
from django.utils import timezone
from .models import (
    BatchName, BatchEntry, BatchIncubation, BatchHatching,
    Customer, CulledSale, DisinfectantCategory, DisinfectantInventory,
    DisinfectantTransaction, BatchDistribution, BatchDistributionItem
)

class BatchNameForm(forms.ModelForm):
    class Meta:
        model = BatchName
        fields = ['name', 'description', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class BatchEntryForm(forms.ModelForm):
    class Meta:
        model = BatchEntry
        fields = ['batch_name', 'date', 'quantity', 'driver', 'notes']
        widgets = {
            'batch_name': forms.Select(attrs={'class': 'form-select'}),
            'date': forms.DateInput(attrs={'class': 'form-control datepicker', 'type': 'date'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control'}),
            'driver': forms.TextInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class BatchIncubationForm(forms.ModelForm):
    class Meta:
        model = BatchIncubation
        fields = ['batch_entry', 'incubation_date', 'incubation_quantity', 'damaged_quantity', 'notes']
        widgets = {
            'batch_entry': forms.Select(attrs={'class': 'form-select'}),
            'incubation_date': forms.DateInput(attrs={'class': 'form-control datepicker', 'type': 'date'}),
            'incubation_quantity': forms.NumberInput(attrs={'class': 'form-control'}),
            'damaged_quantity': forms.NumberInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        batch_id = kwargs.pop('batch_id', None)
        super().__init__(*args, **kwargs)
        if batch_id:
            self.fields['batch_entry'].initial = batch_id
            self.fields['batch_entry'].widget.attrs['readonly'] = True


class BatchHatchingForm(forms.ModelForm):
    class Meta:
        model = BatchHatching
        fields = ['incubation', 'hatch_date', 'chicks_count', 'culled_count', 'dead_count',
                 'fertility_rate', 'hatch_rate', 'notes']
        widgets = {
            'incubation': forms.Select(attrs={'class': 'form-select'}),
            'hatch_date': forms.DateInput(attrs={'class': 'form-control datepicker', 'type': 'date'}),
            'chicks_count': forms.NumberInput(attrs={'class': 'form-control', 'id': 'id_chicks_count'}),
            'culled_count': forms.NumberInput(attrs={'class': 'form-control', 'id': 'id_culled_count'}),
            'dead_count': forms.NumberInput(attrs={'class': 'form-control', 'id': 'id_dead_count'}),
            'fertility_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'id': 'id_fertility_rate'}),
            'hatch_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'id': 'id_hatch_rate', 'readonly': 'readonly'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        incubation_id = kwargs.pop('incubation_id', None)
        super().__init__(*args, **kwargs)
        if incubation_id:
            self.fields['incubation'].initial = incubation_id
            self.fields['incubation'].widget.attrs['readonly'] = True

        # جعل حقل نسبة الفقس الحقيقية للقراءة فقط
        self.fields['hatch_rate'].widget.attrs['readonly'] = True


class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ['name', 'phone', 'address', 'is_active', 'notes']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class CulledSaleForm(forms.ModelForm):
    class Meta:
        model = CulledSale
        fields = ['customer', 'hatching', 'invoice_date', 'quantity', 'price_per_unit', 'paid_amount', 'notes']
        widgets = {
            'customer': forms.Select(attrs={'class': 'form-select form-select-lg', 'style': 'font-size: 1.1rem; height: auto;'}),
            'hatching': forms.Select(attrs={'class': 'form-select'}),
            'invoice_date': forms.DateInput(attrs={'class': 'form-control datepicker', 'type': 'date'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'id': 'id_quantity'}),
            'price_per_unit': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'id': 'id_price_per_unit'}),
            'paid_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        hatching_id = kwargs.pop('hatching_id', None)
        super().__init__(*args, **kwargs)
        if hatching_id:
            self.fields['hatching'].initial = hatching_id
            self.fields['hatching'].widget.attrs['readonly'] = True

    def clean(self):
        cleaned_data = super().clean()
        hatching = cleaned_data.get('hatching')
        quantity = cleaned_data.get('quantity')

        if hatching and quantity:
            available = hatching.available_culled_count
            if self.instance.pk:
                # إذا كان هذا تحديثًا لسجل موجود
                current = CulledSale.objects.get(pk=self.instance.pk)
                available += current.quantity

            if quantity > available:
                self.add_error('quantity', f'عدد الكتاكيت الفرزة المتاحة للبيع هو {available} فقط.')

        return cleaned_data


class DisinfectantCategoryForm(forms.ModelForm):
    class Meta:
        model = DisinfectantCategory
        fields = ['name', 'description', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class DisinfectantInventoryForm(forms.ModelForm):
    class Meta:
        model = DisinfectantInventory
        fields = ['category', 'name', 'supplier', 'unit', 'current_stock', 'minimum_stock', 'notes']
        widgets = {
            'category': forms.Select(attrs={'class': 'form-select'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'supplier': forms.TextInput(attrs={'class': 'form-control'}),
            'unit': forms.TextInput(attrs={'class': 'form-control'}),
            'current_stock': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'minimum_stock': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class DisinfectantTransactionForm(forms.ModelForm):
    class Meta:
        model = DisinfectantTransaction
        fields = ['disinfectant', 'transaction_type', 'transaction_date', 'quantity', 'notes']
        widgets = {
            'disinfectant': forms.Select(attrs={'class': 'form-select'}),
            'transaction_type': forms.Select(attrs={'class': 'form-select'}),
            'transaction_date': forms.DateInput(attrs={'class': 'form-control datepicker', 'type': 'date'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        disinfectant_id = kwargs.pop('disinfectant_id', None)
        transaction_type = kwargs.pop('transaction_type', None)
        super().__init__(*args, **kwargs)

        if disinfectant_id:
            self.fields['disinfectant'].initial = disinfectant_id
            self.fields['disinfectant'].widget.attrs['readonly'] = True

        if transaction_type:
            self.fields['transaction_type'].initial = transaction_type
            self.fields['transaction_type'].widget.attrs['readonly'] = True

    def clean(self):
        cleaned_data = super().clean()
        disinfectant = cleaned_data.get('disinfectant')
        transaction_type = cleaned_data.get('transaction_type')
        quantity = cleaned_data.get('quantity')

        if disinfectant and transaction_type == 'dispense' and quantity:
            # التحقق من أن كمية الصرف لا تتجاوز المخزون الحالي
            if quantity > disinfectant.current_stock:
                self.add_error('quantity', f'الكمية المتاحة للصرف هي {disinfectant.current_stock} {disinfectant.unit} فقط.')

        return cleaned_data


class BatchDistributionForm(forms.ModelForm):
    class Meta:
        model = BatchDistribution
        fields = ['hatching', 'distribution_date', 'notes']
        widgets = {
            'hatching': forms.Select(attrs={'class': 'form-select'}),
            'distribution_date': forms.DateInput(attrs={'class': 'form-control datepicker', 'type': 'date'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        hatching_id = kwargs.pop('hatching_id', None)
        super().__init__(*args, **kwargs)

        # تحديد الدفعات المتاحة للتوزيع (الدفعات التي خرجت اليوم)
        today = timezone.now().date()
        self.fields['hatching'].queryset = BatchHatching.objects.filter(
            hatch_date=today
        ).order_by('-hatch_date')

        if hatching_id:
            self.fields['hatching'].initial = hatching_id
            self.fields['hatching'].widget.attrs['readonly'] = True


class BatchDistributionItemForm(forms.ModelForm):
    class Meta:
        model = BatchDistributionItem
        fields = ['customer', 'chicks_count', 'price_per_unit', 'paid_amount', 'notes']
        widgets = {
            'customer': forms.Select(attrs={'class': 'form-select'}),
            'chicks_count': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'price_per_unit': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'paid_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        distribution = kwargs.pop('distribution', None)
        super().__init__(*args, **kwargs)

        # تحديد العملاء النشطين فقط
        self.fields['customer'].queryset = Customer.objects.filter(is_active=True).order_by('name')

        self.distribution = distribution

    def clean_chicks_count(self):
        chicks_count = self.cleaned_data.get('chicks_count')

        if self.distribution:
            # حساب عدد الكتاكيت المتبقية المتاحة للتوزيع
            hatching = self.distribution.hatching
            distributed_count = sum(item.chicks_count for item in self.distribution.distribution_items.all() if item != self.instance)
            available_count = hatching.chicks_count - distributed_count

            if self.instance and self.instance.pk:
                # إذا كان هذا تحديثًا لعنصر موجود، نضيف عدد الكتاكيت الحالي للعنصر
                available_count += self.instance.chicks_count

            if chicks_count > available_count:
                raise forms.ValidationError(f'عدد الكتاكيت المتاحة للتوزيع هو {available_count} فقط.')

        return chicks_count


# إنشاء نموذج مجموعة لعناصر التوزيع
BatchDistributionItemFormSet = inlineformset_factory(
    BatchDistribution,
    BatchDistributionItem,
    form=BatchDistributionItemForm,
    extra=1,
    can_delete=True
)


class PrintSettingsForm(forms.Form):
    """نموذج إعدادات الطباعة والتصدير"""

    # إعدادات عامة
    show_created_today = forms.BooleanField(
        label='إظهار الدفعات المسجلة اليوم بغض النظر عن تاريخ الدخول',
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    hide_empty_sections = forms.BooleanField(
        label='إخفاء الأقسام التي لا توجد بها بيانات',
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    # إعدادات التوزيعات
    show_price_in_distribution = forms.BooleanField(
        label='إظهار سعر الكتكوت في التوزيعة',
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    # إعدادات مبيعات الفرزة
    show_price_in_culled_sales = forms.BooleanField(
        label='إظهار سعر الكتكوت الفرزة والمدفوع والإجمالي',
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
