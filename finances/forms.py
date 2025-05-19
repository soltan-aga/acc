from django import forms
from .models import (
    SafeTransaction, ContactTransaction, ProductTransaction,
    Expense, Income, ExpenseCategory, IncomeCategory,
    SafeDeposit, SafeWithdrawal, StoreIssue, StoreIssueItem,
    StoreReceive, StoreReceiveItem, StorePermit, StorePermitItem
)
from products.models import ProductUnit

class ProductTransactionForm(forms.ModelForm):
    class Meta:
        model = ProductTransaction
        fields = ['product', 'quantity', 'product_unit', 'transaction_type', 'description', 'reference_number']
        widgets = {
            'product': forms.Select(attrs={'class': 'form-select'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.001'}),
            'product_unit': forms.Select(attrs={'class': 'form-select'}),
            'transaction_type': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'reference_number': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # تحديث حقل وحدات المنتج بناءً على المنتج المحدد
        if 'product' in self.data:
            try:
                product_id = int(self.data.get('product'))
                self.fields['product_unit'].queryset = ProductTransaction.objects.filter(product_id=product_id)
            except (ValueError, TypeError):
                pass
        elif self.instance.pk and self.instance.product:
            self.fields['product_unit'].queryset = self.instance.product.units.all()
        else:
            self.fields['product_unit'].queryset = ProductTransaction.objects.none()

class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = ['category', 'safe', 'amount', 'payee', 'notes', 'reference_number', 'date']
        widgets = {
            'category': forms.Select(attrs={'class': 'form-select'}),
            'safe': forms.Select(attrs={'class': 'form-select'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'payee': forms.TextInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'reference_number': forms.TextInput(attrs={'class': 'form-control'}),
            'date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
        }

class IncomeForm(forms.ModelForm):
    class Meta:
        model = Income
        fields = ['category', 'safe', 'amount', 'payer', 'notes', 'reference_number', 'date']
        widgets = {
            'category': forms.Select(attrs={'class': 'form-select'}),
            'safe': forms.Select(attrs={'class': 'form-select'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'payer': forms.TextInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'reference_number': forms.TextInput(attrs={'class': 'form-control'}),
            'date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
        }

class ExpenseCategoryForm(forms.ModelForm):
    class Meta:
        model = ExpenseCategory
        fields = ['name', 'parent', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'parent': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # استثناء الفئة الحالية من قائمة الفئات الأب لمنع التسلسل الدائري
        if self.instance.pk:
            self.fields['parent'].queryset = ExpenseCategory.objects.exclude(pk=self.instance.pk)
        # جعل حقل الفئة الأب اختياري
        self.fields['parent'].required = False

class IncomeCategoryForm(forms.ModelForm):
    class Meta:
        model = IncomeCategory
        fields = ['name', 'parent', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'parent': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # استثناء الفئة الحالية من قائمة الفئات الأب لمنع التسلسل الدائري
        if self.instance.pk:
            self.fields['parent'].queryset = IncomeCategory.objects.exclude(pk=self.instance.pk)
        # جعل حقل الفئة الأب اختياري
        self.fields['parent'].required = False

class SafeDepositForm(forms.ModelForm):
    class Meta:
        model = SafeDeposit
        fields = ['safe', 'amount', 'source', 'notes', 'reference_number', 'date']
        widgets = {
            'safe': forms.Select(attrs={'class': 'form-select'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'source': forms.TextInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'reference_number': forms.TextInput(attrs={'class': 'form-control'}),
            'date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
        }

class SafeWithdrawalForm(forms.ModelForm):
    class Meta:
        model = SafeWithdrawal
        fields = ['safe', 'amount', 'destination', 'notes', 'reference_number', 'date']
        widgets = {
            'safe': forms.Select(attrs={'class': 'form-select'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'destination': forms.TextInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'reference_number': forms.TextInput(attrs={'class': 'form-control'}),
            'date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
        }


class StoreIssueForm(forms.ModelForm):
    class Meta:
        model = StoreIssue
        fields = ['store', 'recipient', 'driver', 'representative', 'reference_number', 'notes', 'is_posted', 'date']
        widgets = {
            'store': forms.Select(attrs={'class': 'form-select'}),
            'recipient': forms.TextInput(attrs={'class': 'form-control'}),
            'driver': forms.Select(attrs={'class': 'form-select'}),
            'representative': forms.Select(attrs={'class': 'form-select'}),
            'reference_number': forms.TextInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_posted': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
        }


class StoreIssueItemForm(forms.ModelForm):
    class Meta:
        model = StoreIssueItem
        fields = ['product', 'product_unit', 'quantity', 'notes']
        widgets = {
            'product': forms.Select(attrs={'class': 'form-select product-select'}),
            'product_unit': forms.Select(attrs={'class': 'form-select product-unit-select'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.001'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # تعيين قائمة فارغة كقيمة افتراضية
        self.fields['product_unit'].queryset = ProductUnit.objects.none()

        # تقييد خيارات وحدات المنتج إلى وحدات المنتج المحدد فقط
        if 'product' in self.data:
            try:
                product_id = int(self.data.get('product'))
                if product_id:
                    self.fields['product_unit'].queryset = ProductUnit.objects.filter(product_id=product_id)
            except (ValueError, TypeError):
                pass  # في حالة عدم وجود منتج محدد أو قيمة غير صالحة
        elif self.instance.pk and self.instance.product:
            # في حالة تعديل بند موجود
            self.fields['product_unit'].queryset = self.instance.product.units.all()


class StoreReceiveForm(forms.ModelForm):
    class Meta:
        model = StoreReceive
        fields = ['store', 'sender', 'driver', 'representative', 'reference_number', 'notes', 'is_posted', 'date']
        widgets = {
            'store': forms.Select(attrs={'class': 'form-select'}),
            'sender': forms.TextInput(attrs={'class': 'form-control'}),
            'driver': forms.Select(attrs={'class': 'form-select'}),
            'representative': forms.Select(attrs={'class': 'form-select'}),
            'reference_number': forms.TextInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_posted': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
        }


class StoreReceiveItemForm(forms.ModelForm):
    class Meta:
        model = StoreReceiveItem
        fields = ['product', 'product_unit', 'quantity', 'notes']
        widgets = {
            'product': forms.Select(attrs={'class': 'form-select product-select'}),
            'product_unit': forms.Select(attrs={'class': 'form-select product-unit-select'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.001'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # تعيين قائمة فارغة كقيمة افتراضية
        self.fields['product_unit'].queryset = ProductUnit.objects.none()

        # تقييد خيارات وحدات المنتج إلى وحدات المنتج المحدد فقط
        if 'product' in self.data:
            try:
                product_id = int(self.data.get('product'))
                if product_id:
                    self.fields['product_unit'].queryset = ProductUnit.objects.filter(product_id=product_id)
            except (ValueError, TypeError):
                pass  # في حالة عدم وجود منتج محدد أو قيمة غير صالحة
        elif self.instance.pk and self.instance.product:
            # في حالة تعديل بند موجود
            self.fields['product_unit'].queryset = self.instance.product.units.all()


class StorePermitForm(forms.ModelForm):
    class Meta:
        model = StorePermit
        fields = ['permit_type', 'store', 'person_name', 'driver', 'representative', 'reference_number', 'notes', 'is_posted', 'date']
        widgets = {
            'permit_type': forms.Select(attrs={'class': 'form-select'}),
            'store': forms.Select(attrs={'class': 'form-select'}),
            'person_name': forms.TextInput(attrs={'class': 'form-control'}),
            'driver': forms.Select(attrs={'class': 'form-select'}),
            'representative': forms.Select(attrs={'class': 'form-select'}),
            'reference_number': forms.TextInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_posted': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
        }


class StorePermitItemForm(forms.ModelForm):
    class Meta:
        model = StorePermitItem
        fields = ['product', 'product_unit', 'quantity', 'notes']
        widgets = {
            'product': forms.Select(attrs={'class': 'form-select product-select'}),
            'product_unit': forms.Select(attrs={'class': 'form-select product-unit-select'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.001'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

    def clean_quantity(self):
        """تنظيف حقل الكمية وتقريبه إلى رقم صحيح إذا كان بدون كسور"""
        quantity = self.cleaned_data.get('quantity')
        if quantity is not None:
            # إذا كانت الكمية تساوي قيمتها المقربة إلى أقرب عدد صحيح
            if quantity == int(quantity):
                # تحويل الكمية إلى عدد صحيح إذا كانت بدون كسور
                quantity = int(quantity)
        return quantity

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # تعيين قائمة فارغة كقيمة افتراضية
        self.fields['product_unit'].queryset = ProductUnit.objects.none()

        # تحديد المفتاح الصحيح للوحدة في البيانات
        product_key = None
        unit_key = None

        # البحث عن المفاتيح الصحيحة في البيانات
        if self.data:
            prefix = self.prefix or ''
            if prefix:
                product_key = f"{prefix}-product"
                unit_key = f"{prefix}-product_unit"
            else:
                # البحث عن المفاتيح التي تنتهي بـ -product و -product_unit
                for key in self.data:
                    if key.endswith('-product'):
                        product_key = key
                    if key.endswith('-product_unit'):
                        unit_key = key

                # إذا لم نجد المفاتيح، نستخدم المفاتيح العادية
                if not product_key:
                    product_key = 'product'
                if not unit_key:
                    unit_key = 'product_unit'

            print(f"مفتاح المنتج: {product_key}, مفتاح الوحدة: {unit_key}")

        # تقييد خيارات وحدات المنتج إلى وحدات المنتج المحدد فقط
        if product_key and product_key in self.data and self.data.get(product_key):
            try:
                product_id = int(self.data.get(product_key))
                if product_id:
                    # جلب جميع وحدات المنتج
                    product_units = ProductUnit.objects.filter(product_id=product_id)
                    self.fields['product_unit'].queryset = product_units

                    print(f"تم العثور على {product_units.count()} وحدة للمنتج {product_id}")
                    for unit in product_units:
                        print(f"- وحدة: {unit.unit.name} (ID: {unit.id})")

                    # التحقق من وجود وحدة محددة في البيانات
                    if unit_key and unit_key in self.data and self.data.get(unit_key):
                        try:
                            unit_id = int(self.data.get(unit_key))
                            print(f"وحدة محددة في البيانات: {unit_id}")

                            # التحقق من أن الوحدة المحددة تنتمي للمنتج
                            if not product_units.filter(id=unit_id).exists():
                                # إذا كانت الوحدة غير صالحة، نحاول تحديد وحدة افتراضية
                                default_unit = product_units.filter(is_default_sale=True).first() or product_units.first()
                                if default_unit:
                                    print(f"تم تعيين وحدة افتراضية: {default_unit.id} ({default_unit.unit.name})")
                                    # لا يمكننا تعديل self.data مباشرة لأنه غير قابل للتعديل
                                    # لكن يمكننا تعيين قيمة الحقل بعد التحقق من الصحة
                                    self.initial['product_unit'] = default_unit.id
                        except (ValueError, TypeError) as e:
                            print(f"خطأ في معالجة وحدة المنتج: {e}")
            except (ValueError, TypeError) as e:
                print(f"خطأ في معالجة المنتج: {e}")
        elif self.instance.pk and self.instance.product:
            # في حالة تعديل بند موجود
            self.fields['product_unit'].queryset = self.instance.product.units.all()
            print(f"تحميل وحدات المنتج لبند موجود: {self.instance.product.name}")
            print(f"عدد الوحدات: {self.instance.product.units.count()}")

    def clean(self):
        """التحقق من صحة البيانات وتصحيح أي أخطاء محتملة"""
        cleaned_data = super().clean()
        product = cleaned_data.get('product')
        product_unit = cleaned_data.get('product_unit')

        # إذا كان هناك منتج ولكن لا توجد وحدة صالحة
        if product and not product_unit:
            # محاولة العثور على وحدة افتراضية
            default_unit = ProductUnit.objects.filter(
                product=product,
                is_default_sale=True
            ).first() or ProductUnit.objects.filter(product=product).first()

            if default_unit:
                print(f"تم تعيين وحدة افتراضية في clean(): {default_unit.id} ({default_unit.unit.name})")
                cleaned_data['product_unit'] = default_unit

        return cleaned_data

    def clean_product_unit(self):
        """التحقق من صحة وحدة المنتج"""
        product = self.cleaned_data.get('product')
        product_unit = self.cleaned_data.get('product_unit')

        if product and not product_unit:
            # محاولة العثور على وحدة افتراضية
            default_unit = ProductUnit.objects.filter(
                product=product,
                is_default_sale=True
            ).first() or ProductUnit.objects.filter(product=product).first()

            if default_unit:
                print(f"تم تعيين وحدة افتراضية في clean_product_unit(): {default_unit.id} ({default_unit.unit.name})")
                return default_unit

        return product_unit