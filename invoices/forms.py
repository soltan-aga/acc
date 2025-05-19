from django import forms
from django.forms import inlineformset_factory
from .models import Invoice, InvoiceItem, Payment
from products.models import Product, ProductUnit

class InvoiceForm(forms.ModelForm):
    class Meta:
        model = Invoice
        fields = ['number', 'invoice_type', 'payment_type', 'contact', 'store', 'safe',
                 'representative', 'driver', 'discount_amount', 'tax_amount', 'paid_amount', 'notes']
        widgets = {
            'number': forms.TextInput(attrs={'class': 'form-control'}),
            'invoice_type': forms.Select(attrs={'class': 'form-select'}),
            'payment_type': forms.Select(attrs={'class': 'form-select'}),
            'contact': forms.Select(attrs={'class': 'form-select'}),
            'store': forms.Select(attrs={'class': 'form-select'}),
            'safe': forms.Select(attrs={'class': 'form-select'}),
            'representative': forms.Select(attrs={'class': 'form-select'}),
            'driver': forms.Select(attrs={'class': 'form-select'}),
            'discount_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'tax_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'paid_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        invoice_type = kwargs.pop('invoice_type', None)
        super().__init__(*args, **kwargs)

        # إذا كان نوع الفاتورة محدد مسبقاً
        if invoice_type:
            self.fields['invoice_type'].initial = invoice_type
            self.fields['invoice_type'].widget.attrs['readonly'] = True

            # تحميل جميع جهات الاتصال بغض النظر عن نوعها
            # تعيين التسمية المناسبة بناءً على نوع الفاتورة
            if invoice_type in [Invoice.SALE, Invoice.SALE_RETURN]:
                self.fields['contact'].label = 'العميل/المورد (فاتورة بيع)'
            else:
                self.fields['contact'].label = 'العميل/المورد (فاتورة شراء)'

        # جعل حقل الخزنة مطلوباً إذا كان نوع الدفع نقدي
        if self.instance.payment_type == Invoice.CASH:
            self.fields['safe'].required = True
        else:
            self.fields['safe'].required = False

        # جعل حقل المندوب والسائق اختياري
        self.fields['representative'].required = False
        self.fields['driver'].required = False

class InvoiceItemForm(forms.ModelForm):
    class Meta:
        model = InvoiceItem
        fields = ['product', 'product_unit', 'quantity', 'unit_price', 'discount_percentage', 'tax_percentage']
        widgets = {
            'product': forms.Select(attrs={
                'class': 'form-select product-select',
                'data-placeholder': 'اختر المنتج...'
            }),
            'product_unit': forms.Select(attrs={'class': 'form-select product-unit-select'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control quantity-input', 'step': '0.001', 'min': '0.001'}),
            'unit_price': forms.NumberInput(attrs={'class': 'form-control price-input', 'step': '0.01', 'min': '0'}),
            'discount_percentage': forms.NumberInput(attrs={'class': 'form-control discount-input', 'step': '0.01', 'min': '0', 'max': '100'}),
            'tax_percentage': forms.NumberInput(attrs={'class': 'form-control tax-input', 'step': '0.01', 'min': '0'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # تحديث حقل وحدات المنتج بناءً على المنتج المحدد
        if self.instance.pk and self.instance.product:
            self.fields['product_unit'].queryset = self.instance.product.units.all()
        else:
            self.fields['product_unit'].queryset = ProductUnit.objects.none()

        # جعل الحقول مطلوبة
        self.fields['product'].required = True
        self.fields['product_unit'].required = True
        self.fields['quantity'].required = True
        self.fields['unit_price'].required = True

    def clean(self):
        cleaned_data = super().clean()
        product = cleaned_data.get('product')
        product_unit = cleaned_data.get('product_unit')
        quantity = cleaned_data.get('quantity')
        unit_price = cleaned_data.get('unit_price')

        # التحقق من تحديد المنتج
        if not product:
            self.add_error('product', 'يجب تحديد المنتج')

        # التحقق من تحديد الوحدة
        if not product_unit:
            self.add_error('product_unit', 'يجب تحديد وحدة المنتج')

        # التحقق من الكمية
        if not quantity or quantity <= 0:
            self.add_error('quantity', 'يجب أن تكون الكمية أكبر من صفر')

        # التحقق من السعر
        if not unit_price or unit_price < 0:
            self.add_error('unit_price', 'يجب أن يكون السعر صفر أو أكبر')

        # التحقق من أن الوحدة تنتمي للمنتج
        if product and product_unit and product_unit.product != product:
            self.add_error('product_unit', 'وحدة المنتج غير متوافقة مع المنتج المحدد')

        return cleaned_data

# إنشاء نموذج مجموعة بنود الفاتورة
InvoiceItemFormSet = inlineformset_factory(
    Invoice,
    InvoiceItem,
    form=InvoiceItemForm,
    extra=0,
    can_delete=True,
    validate_min=True,
    min_num=1,
    validate_max=True,
    max_num=50,
)

class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['number', 'payment_type', 'amount', 'contact', 'safe', 'notes', 'reference_number']
        widgets = {
            'number': forms.TextInput(attrs={'class': 'form-control'}),
            'payment_type': forms.Select(attrs={'class': 'form-select'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0.01'}),
            'contact': forms.Select(attrs={'class': 'form-select'}),
            'safe': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'reference_number': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        payment_type = kwargs.pop('payment_type', None)
        super().__init__(*args, **kwargs)

        # إذا كان نوع العملية محدد مسبقاً
        if payment_type:
            self.fields['payment_type'].initial = payment_type
            self.fields['payment_type'].widget.attrs['readonly'] = True

            # تحميل جميع جهات الاتصال بغض النظر عن نوعها
            # تعيين التسمية المناسبة بناءً على نوع العملية
            if payment_type == Payment.RECEIPT:
                self.fields['contact'].label = 'العميل/المورد (تحصيل)'
            else:
                self.fields['contact'].label = 'العميل/المورد (دفع)'
