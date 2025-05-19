from django import forms
from .models import Category, Unit, Product, ProductUnit

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'parent', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'parent': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class UnitForm(forms.ModelForm):
    class Meta:
        model = Unit
        fields = ['name', 'symbol']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'symbol': forms.TextInput(attrs={'class': 'form-control'}),
        }

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'code', 'barcode', 'category', 'default_store',
                 'initial_balance', 'image', 'description', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'code': forms.TextInput(attrs={'class': 'form-control'}),
            'barcode': forms.TextInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'default_store': forms.Select(attrs={'class': 'form-select'}),
            'initial_balance': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.001'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class ProductUnitForm(forms.ModelForm):
    class Meta:
        model = ProductUnit
        fields = ['unit', 'conversion_factor', 'purchase_price', 'selling_price',
                 'barcode', 'is_default_purchase', 'is_default_sale']
        widgets = {
            'unit': forms.Select(attrs={'class': 'form-select'}),
            'conversion_factor': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.001'}),
            'purchase_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'selling_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'barcode': forms.TextInput(attrs={'class': 'form-control'}),
            'is_default_purchase': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_default_sale': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

# نموذج مجموعة وحدات المنتج (Formset)
ProductUnitFormSet = forms.inlineformset_factory(
    Product,
    ProductUnit,
    form=ProductUnitForm,
    extra=0,  # تغيير من 1 إلى 0 لمنع إضافة صفوف تلقائيًا
    can_delete=True,
    min_num=1  # ضمان وجود صف واحد على الأقل
)
