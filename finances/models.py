from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from core.models import Safe, Contact, Store, Representative, Driver
from products.models import Product, ProductUnit

class ExpenseCategory(models.Model):
    """أقسام المصروفات في النظام"""
    name = models.CharField(_("اسم القسم"), max_length=100)
    description = models.TextField(_("الوصف"), blank=True, null=True)
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, blank=True, null=True,
                             related_name='children', verbose_name=_("القسم الأب"))

    class Meta:
        verbose_name = _("قسم المصروفات")
        verbose_name_plural = _("أقسام المصروفات")

    def __str__(self):
        return self.name

class IncomeCategory(models.Model):
    """أقسام الإيرادات في النظام"""
    name = models.CharField(_("اسم القسم"), max_length=100)
    description = models.TextField(_("الوصف"), blank=True, null=True)
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, blank=True, null=True,
                             related_name='children', verbose_name=_("القسم الأب"))

    class Meta:
        verbose_name = _("قسم الإيرادات")
        verbose_name_plural = _("أقسام الإيرادات")

    def __str__(self):
        return self.name

class SafeTransaction(models.Model):
    # أنواع العمليات المالية المتعلقة بالخزنة
    SALE_INVOICE = 'sale_invoice'
    PURCHASE_INVOICE = 'purchase_invoice'
    SALE_RETURN_INVOICE = 'sale_return_invoice'
    PURCHASE_RETURN_INVOICE = 'purchase_return_invoice'
    COLLECTION = 'collection'
    PAYMENT = 'payment'
    DEPOSIT = 'deposit'
    WITHDRAWAL = 'withdrawal'
    EXPENSE = 'expense'
    INCOME = 'income'

    TRANSACTION_TYPE_CHOICES = [
        (SALE_INVOICE, _("فاتورة بيع")),
        (PURCHASE_INVOICE, _("فاتورة شراء")),
        (SALE_RETURN_INVOICE, _("مرتجع بيع")),
        (PURCHASE_RETURN_INVOICE, _("مرتجع شراء")),
        (COLLECTION, _("تحصيل")),
        (PAYMENT, _("دفع")),
        (DEPOSIT, _("إيداع")),
        (WITHDRAWAL, _("سحب")),
        (EXPENSE, _("مصروف")),
        (INCOME, _("إيراد")),
    ]

    safe = models.ForeignKey(Safe, on_delete=models.CASCADE, related_name='transactions', verbose_name=_("الخزنة"))
    date = models.DateTimeField(_("تاريخ العملية"), default=timezone.now)
    amount = models.DecimalField(_("المبلغ"), max_digits=15, decimal_places=2)
    transaction_type = models.CharField(_("نوع العملية"), max_length=25, choices=TRANSACTION_TYPE_CHOICES)
    description = models.TextField(_("الوصف"), blank=True, null=True)
    invoice = models.ForeignKey('invoices.Invoice', on_delete=models.SET_NULL, related_name='safe_transactions',
                              verbose_name=_("الفاتورة"), null=True, blank=True)
    contact = models.ForeignKey(Contact, on_delete=models.SET_NULL, related_name='safe_transactions',
                              verbose_name=_("جهة الاتصال"), null=True, blank=True)
    reference_number = models.CharField(_("الرقم المرجعي"), max_length=50, blank=True, null=True)
    balance_before = models.DecimalField(_("الرصيد قبل العملية"), max_digits=15, decimal_places=2)
    balance_after = models.DecimalField(_("الرصيد بعد العملية"), max_digits=15, decimal_places=2)

    class Meta:
        verbose_name = _("حركة الخزنة")
        verbose_name_plural = _("حركات الخزنة")
        ordering = ['date']  # ترتيب الحركات حسب التاريخ تصاعديًا للحصول على تسلسل صحيح

    def __str__(self):
        return f"{self.get_transaction_type_display()} - {self.safe.name} - {self.amount}"

    def set_transaction_type_from_invoice(self):
        """تحديد نوع العملية بناءً على نوع الفاتورة المرتبطة"""
        if self.invoice:
            if self.invoice.invoice_type == 'sale':
                self.transaction_type = self.SALE_INVOICE
            elif self.invoice.invoice_type == 'purchase':
                self.transaction_type = self.PURCHASE_INVOICE
            elif self.invoice.invoice_type == 'sale_return':
                self.transaction_type = self.SALE_RETURN_INVOICE
            elif self.invoice.invoice_type == 'purchase_return':
                self.transaction_type = self.PURCHASE_RETURN_INVOICE

    @staticmethod
    def recalculate_balances(safe):
        """
        إعادة حساب أرصدة جميع حركات الخزنة لخزنة معينة من البداية
        """
        from django.db import transaction

        with transaction.atomic():
            # الحصول على جميع حركات الخزنة مرتبة حسب التاريخ
            transactions = SafeTransaction.objects.filter(safe=safe).order_by('date')

            # إعادة تعيين رصيد الخزنة إلى الرصيد الافتتاحي
            current_balance = safe.initial_balance

            # طباعة معلومات تصحيح الأخطاء
            print(f"إعادة حساب أرصدة الخزنة {safe.name} - الرصيد الافتتاحي: {current_balance}")

            # إعادة حساب الأرصدة لكل حركة
            for trans in transactions:
                # تحديث الرصيد قبل العملية
                old_balance_before = trans.balance_before
                old_balance_after = trans.balance_after

                trans.balance_before = current_balance

                # إعادة حساب الرصيد بعد العملية بناءً على نوع العملية
                if trans.transaction_type in [SafeTransaction.SALE_INVOICE, SafeTransaction.COLLECTION, SafeTransaction.DEPOSIT, SafeTransaction.INCOME]:
                    # عمليات تزيد رصيد الخزنة
                    trans.balance_after = trans.balance_before + trans.amount
                elif trans.transaction_type in [SafeTransaction.PURCHASE_INVOICE, SafeTransaction.PAYMENT, SafeTransaction.WITHDRAWAL, SafeTransaction.EXPENSE]:
                    # عمليات تنقص رصيد الخزنة
                    trans.balance_after = trans.balance_before - trans.amount
                elif trans.transaction_type == SafeTransaction.SALE_RETURN_INVOICE:
                    # مرتجع بيع ينقص الخزنة
                    trans.balance_after = trans.balance_before - trans.amount
                elif trans.transaction_type == SafeTransaction.PURCHASE_RETURN_INVOICE:
                    # مرتجع شراء يزيد الخزنة
                    trans.balance_after = trans.balance_before + trans.amount

                # طباعة معلومات تصحيح الأخطاء
                print(f"العملية: {trans.get_transaction_type_display()} - المبلغ: {trans.amount}")
                print(f"الرصيد قبل (قديم): {old_balance_before} - الرصيد بعد (قديم): {old_balance_after}")
                print(f"الرصيد قبل (جديد): {trans.balance_before} - الرصيد بعد (جديد): {trans.balance_after}")
                print("---")

                # تحديث الرصيد الحالي للحركة التالية
                current_balance = trans.balance_after

                # حفظ التغييرات بدون استدعاء دالة save المخصصة
                SafeTransaction.objects.filter(pk=trans.pk).update(
                    balance_before=trans.balance_before,
                    balance_after=trans.balance_after
                )

            # تحديث رصيد الخزنة النهائي
            if transactions.exists():
                safe.current_balance = transactions.last().balance_after
            else:
                safe.current_balance = safe.initial_balance

            safe.save(update_fields=['current_balance'])

            # طباعة معلومات تصحيح الأخطاء
            print(f"الرصيد النهائي للخزنة {safe.name}: {safe.current_balance}")

            return safe.current_balance

    def save(self, *args, **kwargs):
        # تحديد نوع العملية من الفاتورة إذا كانت متوفرة
        if self.invoice and not self.transaction_type:
            self.set_transaction_type_from_invoice()

        # حفظ الحركة أولاً
        super().save(*args, **kwargs)

        # إعادة حساب جميع الأرصدة من البداية
        SafeTransaction.recalculate_balances(self.safe)

    def delete(self, *args, **kwargs):
        """
        تجاوز دالة الحذف الافتراضية لإعادة حساب الأرصدة
        """
        from django.db import transaction

        with transaction.atomic():
            # حفظ المعلومات المطلوبة قبل الحذف
            safe = self.safe

            # حذف العملية الحالية
            super().delete(*args, **kwargs)

            # إعادة حساب جميع الأرصدة من البداية
            SafeTransaction.recalculate_balances(safe)

class ContactTransaction(models.Model):
    # أنواع العمليات المتعلقة بحسابات العملاء والموردين
    SALE_INVOICE = 'sale_invoice'
    PURCHASE_INVOICE = 'purchase_invoice'
    SALE_RETURN_INVOICE = 'sale_return_invoice'
    PURCHASE_RETURN_INVOICE = 'purchase_return_invoice'
    COLLECTION = 'collection'
    PAYMENT = 'payment'

    TRANSACTION_TYPE_CHOICES = [
        (SALE_INVOICE, _("فاتورة بيع")),
        (PURCHASE_INVOICE, _("فاتورة شراء")),
        (SALE_RETURN_INVOICE, _("مرتجع بيع")),
        (PURCHASE_RETURN_INVOICE, _("مرتجع شراء")),
        (COLLECTION, _("تحصيل")),
        (PAYMENT, _("دفع")),
    ]

    contact = models.ForeignKey(Contact, on_delete=models.CASCADE, related_name='transactions', verbose_name=_("جهة الاتصال"))
    date = models.DateTimeField(_("تاريخ العملية"), default=timezone.now)
    amount = models.DecimalField(_("المبلغ"), max_digits=15, decimal_places=2)
    transaction_type = models.CharField(_("نوع العملية"), max_length=25, choices=TRANSACTION_TYPE_CHOICES)
    invoice = models.ForeignKey('invoices.Invoice', on_delete=models.SET_NULL, related_name='contact_transactions',
                              verbose_name=_("الفاتورة"), null=True, blank=True)
    description = models.TextField(_("الوصف"), blank=True, null=True)
    reference_number = models.CharField(_("الرقم المرجعي"), max_length=50, blank=True, null=True)
    balance_before = models.DecimalField(_("الرصيد قبل العملية"), max_digits=15, decimal_places=2)
    balance_after = models.DecimalField(_("الرصيد بعد العملية"), max_digits=15, decimal_places=2)

    class Meta:
        verbose_name = _("حركة حساب")
        verbose_name_plural = _("حركات الحسابات")
        ordering = ['date']  # ترتيب الحركات حسب التاريخ تصاعديًا للحصول على تسلسل صحيح

    def __str__(self):
        return f"{self.get_transaction_type_display()} - {self.contact.name} - {self.amount}"

    def set_transaction_type_from_invoice(self):
        """تحديد نوع العملية بناءً على نوع الفاتورة المرتبطة"""
        if self.invoice:
            if self.invoice.invoice_type == 'sale':
                self.transaction_type = self.SALE_INVOICE
            elif self.invoice.invoice_type == 'purchase':
                self.transaction_type = self.PURCHASE_INVOICE
            elif self.invoice.invoice_type == 'sale_return':
                self.transaction_type = self.SALE_RETURN_INVOICE
            elif self.invoice.invoice_type == 'purchase_return':
                self.transaction_type = self.PURCHASE_RETURN_INVOICE

    @staticmethod
    def recalculate_balances(contact):
        """
        إعادة حساب أرصدة جميع حركات الحساب لجهة اتصال معينة من البداية
        """
        from django.db import transaction

        with transaction.atomic():
            # الحصول على جميع حركات الحساب لجهة الاتصال مرتبة حسب التاريخ
            transactions = ContactTransaction.objects.filter(contact=contact).order_by('date')

            # إعادة تعيين رصيد جهة الاتصال إلى الرصيد الافتتاحي
            current_balance = contact.initial_balance

            # طباعة معلومات تصحيح الأخطاء
            print(f"إعادة حساب أرصدة {contact.name} - الرصيد الافتتاحي: {current_balance}")

            # إعادة حساب الأرصدة لكل حركة
            for trans in transactions:
                # تحديث الرصيد قبل العملية
                old_balance_before = trans.balance_before
                old_balance_after = trans.balance_after

                trans.balance_before = current_balance

                # إعادة حساب الرصيد بعد العملية بناءً على نوع العملية
                if contact.contact_type == Contact.CUSTOMER:
                    # العمليات المتعلقة بالعملاء
                    if trans.transaction_type == ContactTransaction.SALE_INVOICE:
                        # فاتورة بيع تزيد مديونية العميل
                        trans.balance_after = trans.balance_before + trans.amount
                    elif trans.transaction_type == ContactTransaction.SALE_RETURN_INVOICE:
                        # مرتجع بيع ينقص مديونية العميل
                        trans.balance_after = trans.balance_before - trans.amount
                    elif trans.transaction_type == ContactTransaction.COLLECTION:
                        # تحصيل من العميل ينقص مديونيته
                        trans.balance_after = trans.balance_before - trans.amount
                    else:
                        # أي عملية أخرى لا تؤثر على الرصيد
                        trans.balance_after = trans.balance_before
                else:
                    # العمليات المتعلقة بالموردين
                    if trans.transaction_type == ContactTransaction.PURCHASE_INVOICE:
                        # فاتورة شراء تزيد الالتزام تجاه المورد
                        trans.balance_after = trans.balance_before + trans.amount
                    elif trans.transaction_type == ContactTransaction.PURCHASE_RETURN_INVOICE:
                        # مرتجع شراء ينقص الالتزام تجاه المورد
                        trans.balance_after = trans.balance_before - trans.amount
                    elif trans.transaction_type == ContactTransaction.PAYMENT:
                        # دفع للمورد ينقص الالتزام تجاهه
                        trans.balance_after = trans.balance_before - trans.amount
                    else:
                        # أي عملية أخرى لا تؤثر على الرصيد
                        trans.balance_after = trans.balance_before

                # طباعة معلومات تصحيح الأخطاء
                print(f"العملية: {trans.get_transaction_type_display()} - المبلغ: {trans.amount}")
                print(f"الرصيد قبل (قديم): {old_balance_before} - الرصيد بعد (قديم): {old_balance_after}")
                print(f"الرصيد قبل (جديد): {trans.balance_before} - الرصيد بعد (جديد): {trans.balance_after}")
                print("---")

                # تحديث الرصيد الحالي للحركة التالية
                current_balance = trans.balance_after

                # حفظ التغييرات بدون استدعاء دالة save المخصصة
                ContactTransaction.objects.filter(pk=trans.pk).update(
                    balance_before=trans.balance_before,
                    balance_after=trans.balance_after
                )

            # تحديث رصيد جهة الاتصال النهائي
            if transactions.exists():
                contact.current_balance = transactions.last().balance_after
            else:
                contact.current_balance = contact.initial_balance

            contact.save(update_fields=['current_balance'])

            # طباعة معلومات تصحيح الأخطاء
            print(f"الرصيد النهائي لـ {contact.name}: {contact.current_balance}")

            return contact.current_balance

    def save(self, *args, **kwargs):
        # تحديد نوع العملية من الفاتورة إذا كانت متوفرة
        if self.invoice and not self.transaction_type:
            self.set_transaction_type_from_invoice()

        # حفظ الحركة أولاً
        super().save(*args, **kwargs)

        # إعادة حساب جميع الأرصدة من البداية
        ContactTransaction.recalculate_balances(self.contact)

    def delete(self, *args, **kwargs):
        """
        تجاوز دالة الحذف الافتراضية لإعادة حساب الأرصدة
        """
        from django.db import transaction

        with transaction.atomic():
            # حفظ المعلومات المطلوبة قبل الحذف
            contact = self.contact

            # حذف العملية الحالية
            super().delete(*args, **kwargs)

            # إعادة حساب جميع الأرصدة من البداية
            ContactTransaction.recalculate_balances(contact)

class ProductTransaction(models.Model):
    # أنواع حركات المنتجات
    SALE = 'sale'
    PURCHASE = 'purchase'
    SALE_RETURN = 'sale_return'
    PURCHASE_RETURN = 'purchase_return'
    ADJUSTMENT = 'adjustment'

    TRANSACTION_TYPE_CHOICES = [
        (SALE, _("بيع")),
        (PURCHASE, _("شراء")),
        (SALE_RETURN, _("مرتجع بيع")),
        (PURCHASE_RETURN, _("مرتجع شراء")),
        (ADJUSTMENT, _("تسوية مخزون")),
    ]

    @property
    def quantity_display(self):
        """عرض الكمية بالوحدة الكبرى والصغرى معًا"""
        # البحث عن الوحدة الافتراضية (الأساسية) للمنتج
        try:
            base_unit = self.product.units.get(conversion_factor=1)
            # محاولة العثور على الوحدة الكبرى (ذات أكبر معامل تحويل)
            main_unit = self.product.units.exclude(id=base_unit.id).order_by('-conversion_factor').first()

            if not main_unit:
                # إذا لم يكن هناك وحدة كبرى، فقط نعرض الكمية بالوحدة الحالية
                return self._format_number_display(self.quantity, self.product_unit.unit.name)

            # حساب القيم بالوحدة الكبرى والمتبقي
            main_unit_factor = main_unit.conversion_factor
            base_quantity = self.base_quantity

            main_unit_count = int(base_quantity / main_unit_factor)
            remaining = base_quantity % main_unit_factor

            # تنسيق النص - تحويل الأرقام إلى أرقام صحيحة إذا كانت بدون كسور
            remaining_formatted = self._format_number(remaining)

            # تنسيق النص
            if main_unit_count > 0 and remaining > 0:
                return f"{main_unit_count} {main_unit.unit.name} و {remaining_formatted} {base_unit.unit.name}"
            elif main_unit_count > 0:
                return f"{main_unit_count} {main_unit.unit.name}"
            else:
                return f"{remaining_formatted} {base_unit.unit.name}"
        except:
            # في حالة حدوث أي خطأ، نعرض الكمية بالوحدة الحالية
            return self._format_number_display(self.quantity, self.product_unit.unit.name)

    @property
    def balance_display(self):
        """عرض الرصيد بعد العملية بالوحدة الكبرى والصغرى معًا"""
        # البحث عن الوحدة الافتراضية (الأساسية) للمنتج
        try:
            base_unit = self.product.units.get(conversion_factor=1)
            # محاولة العثور على الوحدة الكبرى (ذات أكبر معامل تحويل)
            main_unit = self.product.units.exclude(id=base_unit.id).order_by('-conversion_factor').first()

            if not main_unit:
                # إذا لم يكن هناك وحدة كبرى، فقط نعرض الرصيد بالوحدة الأساسية
                return self._format_number_display(self.balance_after, base_unit.unit.name)

            # حساب القيم بالوحدة الكبرى والمتبقي
            main_unit_factor = main_unit.conversion_factor
            balance = self.balance_after

            main_unit_count = int(balance / main_unit_factor)
            remaining = balance % main_unit_factor

            # تنسيق النص - تحويل الأرقام إلى أرقام صحيحة إذا كانت بدون كسور
            remaining_formatted = self._format_number(remaining)

            # تنسيق النص
            if main_unit_count > 0 and remaining > 0:
                return f"{main_unit_count} {main_unit.unit.name} و {remaining_formatted} {base_unit.unit.name}"
            elif main_unit_count > 0:
                return f"{main_unit_count} {main_unit.unit.name}"
            else:
                return f"{remaining_formatted} {base_unit.unit.name}"
        except:
            # في حالة حدوث أي خطأ، نعرض الرصيد بدون وحدة
            return self._format_number(self.balance_after)

    def _format_number(self, number):
        """تنسيق الرقم بحيث يتم عرضه كعدد صحيح إذا كان بدون كسور"""
        if number == int(number):
            # إذا كان الرقم عددًا صحيحًا، نعرضه بدون نقطة عشرية
            return str(int(number))
        else:
            # إذا كان به كسور، نستخدم الرقم العشري
            return str(number)

    def _format_number_display(self, number, unit_name):
        """تنسيق الرقم والوحدة معًا"""
        formatted_number = self._format_number(number)
        return f"{formatted_number} {unit_name}"

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='transactions', verbose_name=_("المنتج"))
    date = models.DateTimeField(_("تاريخ العملية"), default=timezone.now)
    quantity = models.DecimalField(_("الكمية"), max_digits=15, decimal_places=3)
    product_unit = models.ForeignKey(ProductUnit, on_delete=models.CASCADE, related_name='transactions', verbose_name=_("وحدة المنتج"))
    base_quantity = models.DecimalField(_("الكمية بالوحدة الأساسية"), max_digits=15, decimal_places=3)
    transaction_type = models.CharField(_("نوع العملية"), max_length=20, choices=TRANSACTION_TYPE_CHOICES)
    invoice = models.ForeignKey('invoices.Invoice', on_delete=models.SET_NULL, related_name='product_transactions',
                              verbose_name=_("الفاتورة"), null=True, blank=True)
    store = models.ForeignKey('core.Store', on_delete=models.CASCADE, related_name='product_transactions',
                            verbose_name=_("المخزن"), default=1)
    description = models.TextField(_("الوصف"), blank=True, null=True)
    reference_number = models.CharField(_("الرقم المرجعي"), max_length=50, blank=True, null=True)
    balance_before = models.DecimalField(_("الرصيد قبل العملية"), max_digits=15, decimal_places=3)
    balance_after = models.DecimalField(_("الرصيد بعد العملية"), max_digits=15, decimal_places=3)

    class Meta:
        verbose_name = _("حركة منتج")
        verbose_name_plural = _("حركات المنتجات")
        ordering = ['date']  # ترتيب الحركات حسب التاريخ تصاعديًا للحصول على تسلسل صحيح

    def __str__(self):
        return f"{self.get_transaction_type_display()} - {self.product.name} - {self.quantity}"

    def set_transaction_type_from_invoice(self):
        """تحديد نوع حركة المنتج بناءً على نوع الفاتورة المرتبطة"""
        if self.invoice:
            self.transaction_type = self.invoice.invoice_type

    @staticmethod
    def recalculate_balances(product):
        """
        إعادة حساب أرصدة جميع حركات المنتج لمنتج معين من البداية
        """
        from django.db import transaction

        with transaction.atomic():
            # الحصول على جميع حركات المنتج مرتبة حسب التاريخ
            transactions = ProductTransaction.objects.filter(product=product).order_by('date')

            # إعادة تعيين رصيد المنتج إلى الرصيد الافتتاحي
            current_balance = product.initial_balance

            # طباعة معلومات تصحيح الأخطاء
            print(f"إعادة حساب أرصدة المنتج {product.name} - الرصيد الافتتاحي: {current_balance}")

            # إعادة حساب الأرصدة لكل حركة
            for trans in transactions:
                # تحديث الرصيد قبل العملية
                old_balance_before = trans.balance_before
                old_balance_after = trans.balance_after

                trans.balance_before = current_balance

                # إعادة حساب الرصيد بعد العملية بناءً على نوع العملية
                if trans.transaction_type in [ProductTransaction.SALE, ProductTransaction.SALE_RETURN]:
                    # عمليات تنقص المخزون
                    trans.balance_after = trans.balance_before - trans.base_quantity
                else:
                    # عمليات تزيد المخزون
                    trans.balance_after = trans.balance_before + trans.base_quantity

                # طباعة معلومات تصحيح الأخطاء
                print(f"العملية: {trans.get_transaction_type_display()} - الكمية: {trans.quantity} {trans.product_unit.unit.name} - الكمية الأساسية: {trans.base_quantity}")
                print(f"الرصيد قبل (قديم): {old_balance_before} - الرصيد بعد (قديم): {old_balance_after}")
                print(f"الرصيد قبل (جديد): {trans.balance_before} - الرصيد بعد (جديد): {trans.balance_after}")
                print("---")

                # تحديث الرصيد الحالي للحركة التالية
                current_balance = trans.balance_after

                # حفظ التغييرات بدون استدعاء دالة save المخصصة
                ProductTransaction.objects.filter(pk=trans.pk).update(
                    balance_before=trans.balance_before,
                    balance_after=trans.balance_after
                )

            # تحديث رصيد المنتج النهائي
            if transactions.exists():
                product.current_balance = transactions.last().balance_after
            else:
                product.current_balance = product.initial_balance

            product.save(update_fields=['current_balance'])

            # طباعة معلومات تصحيح الأخطاء
            print(f"الرصيد النهائي للمنتج {product.name}: {product.current_balance}")

            return product.current_balance

    def save(self, *args, **kwargs):
        # تحديد نوع العملية من الفاتورة إذا كانت متوفرة
        if self.invoice and not self.transaction_type:
            self.set_transaction_type_from_invoice()

        # تحويل الكمية إلى الوحدة الأساسية
        self.base_quantity = self.quantity * self.product_unit.conversion_factor

        # حفظ الحركة أولاً
        super().save(*args, **kwargs)

        # إعادة حساب جميع الأرصدة من البداية
        ProductTransaction.recalculate_balances(self.product)

    def delete(self, *args, **kwargs):
        """
        تجاوز دالة الحذف الافتراضية لإعادة حساب الأرصدة
        """
        from django.db import transaction

        with transaction.atomic():
            # حفظ المعلومات المطلوبة قبل الحذف
            product = self.product

            # حذف العملية الحالية
            super().delete(*args, **kwargs)

            # إعادة حساب جميع الأرصدة من البداية
            ProductTransaction.recalculate_balances(product)


# تم نقل نموذج StorePermit إلى نهاية الملف


# تم نقل نموذج StorePermitItem إلى نهاية الملف


# الاحتفاظ بالنماذج القديمة مؤقتًا للهجرة
class StoreIssue(models.Model):
    """نموذج صرف المنتجات من المخزن (قديم)"""

    number = models.CharField(_("رقم المستند"), max_length=50, blank=True)
    date = models.DateTimeField(_("تاريخ المستند"), default=timezone.now)
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name='issues',
                            verbose_name=_("المخزن"))
    recipient = models.CharField(_("المستلم"), max_length=255)
    driver = models.ForeignKey(Driver, on_delete=models.SET_NULL, related_name='store_issues',
                             verbose_name=_("السائق"), null=True, blank=True)
    representative = models.ForeignKey(Representative, on_delete=models.SET_NULL, related_name='store_issues',
                                     verbose_name=_("المندوب"), null=True, blank=True)
    notes = models.TextField(_("ملاحظات"), blank=True, null=True)
    reference_number = models.CharField(_("الرقم المرجعي"), max_length=50, blank=True, null=True)
    is_posted = models.BooleanField(_("مرحل"), default=True)

    # معرف حركات المنتجات التي تم إنشاؤها بواسطة هذا الصرف
    created_transactions = models.ManyToManyField(ProductTransaction, blank=True, related_name='created_by_issue',
                                              verbose_name=_("حركات المنتجات المنشأة"))

    class Meta:
        verbose_name = _("صرف من المخزن (قديم)")
        verbose_name_plural = _("عمليات الصرف من المخازن (قديم)")

    def __str__(self):
        return f"{self.number} - {self.store.name} - {self.date}"


class StoreIssueItem(models.Model):
    """نموذج بند صرف المنتجات من المخزن (قديم)"""

    issue = models.ForeignKey(StoreIssue, on_delete=models.CASCADE, related_name='items',
                            verbose_name=_("مستند الصرف"))
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='issue_items',
                              verbose_name=_("المنتج"))
    product_unit = models.ForeignKey(ProductUnit, on_delete=models.CASCADE, related_name='issue_items',
                                   verbose_name=_("وحدة المنتج"))
    quantity = models.DecimalField(_("الكمية"), max_digits=15, decimal_places=3)
    notes = models.TextField(_("ملاحظات"), blank=True, null=True)

    class Meta:
        verbose_name = _("بند صرف (قديم)")
        verbose_name_plural = _("بنود الصرف (قديم)")

    def __str__(self):
        return f"{self.product.name} - {self.quantity} {self.product_unit.unit.name}"


class StoreReceive(models.Model):
    """نموذج استلام المنتجات في المخزن (قديم)"""

    number = models.CharField(_("رقم المستند"), max_length=50, blank=True)
    date = models.DateTimeField(_("تاريخ المستند"), default=timezone.now)
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name='receives',
                            verbose_name=_("المخزن"))
    sender = models.CharField(_("المرسل"), max_length=255)
    driver = models.ForeignKey(Driver, on_delete=models.SET_NULL, related_name='store_receives',
                             verbose_name=_("السائق"), null=True, blank=True)
    representative = models.ForeignKey(Representative, on_delete=models.SET_NULL, related_name='store_receives',
                                     verbose_name=_("المندوب"), null=True, blank=True)
    notes = models.TextField(_("ملاحظات"), blank=True, null=True)
    reference_number = models.CharField(_("الرقم المرجعي"), max_length=50, blank=True, null=True)
    is_posted = models.BooleanField(_("مرحل"), default=True)

    # معرف حركات المنتجات التي تم إنشاؤها بواسطة هذا الاستلام
    created_transactions = models.ManyToManyField(ProductTransaction, blank=True, related_name='created_by_receive',
                                              verbose_name=_("حركات المنتجات المنشأة"))

    class Meta:
        verbose_name = _("استلام في المخزن (قديم)")
        verbose_name_plural = _("عمليات الاستلام في المخازن (قديم)")

    def __str__(self):
        return f"{self.number} - {self.store.name} - {self.date}"


class StoreReceiveItem(models.Model):
    """نموذج بند استلام المنتجات في المخزن (قديم)"""

    receive = models.ForeignKey(StoreReceive, on_delete=models.CASCADE, related_name='items',
                              verbose_name=_("مستند الاستلام"))
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='receive_items',
                              verbose_name=_("المنتج"))
    product_unit = models.ForeignKey(ProductUnit, on_delete=models.CASCADE, related_name='receive_items',
                                   verbose_name=_("وحدة المنتج"))
    quantity = models.DecimalField(_("الكمية"), max_digits=15, decimal_places=3)
    notes = models.TextField(_("ملاحظات"), blank=True, null=True)

    class Meta:
        verbose_name = _("بند استلام (قديم)")
        verbose_name_plural = _("بنود الاستلام (قديم)")

    def __str__(self):
        return f"{self.product.name} - {self.quantity} {self.product_unit.unit.name}"

class Expense(models.Model):
    """نموذج المصروفات في النظام"""

    number = models.CharField(_("رقم المستند"), max_length=50, blank=True)
    date = models.DateTimeField(_("تاريخ المستند"), default=timezone.now)
    amount = models.DecimalField(_("المبلغ"), max_digits=15, decimal_places=2)
    category = models.ForeignKey(ExpenseCategory, on_delete=models.PROTECT, related_name='expenses',
                               verbose_name=_("قسم المصروفات"))
    safe = models.ForeignKey(Safe, on_delete=models.CASCADE, related_name='expenses',
                           verbose_name=_("الخزنة"))
    payee = models.CharField(_("المستفيد"), max_length=255)
    notes = models.TextField(_("ملاحظات"), blank=True, null=True)
    reference_number = models.CharField(_("الرقم المرجعي"), max_length=50, blank=True, null=True)
    is_posted = models.BooleanField(_("مرحل"), default=True)

    # معرف حركة الخزنة التي تم إنشاؤها بواسطة هذا المصروف
    created_transaction = models.OneToOneField(SafeTransaction, on_delete=models.SET_NULL,
                                         null=True, blank=True, related_name='created_by_expense',
                                         verbose_name=_("حركة الخزنة المنشأة"))

    class Meta:
        verbose_name = _("مصروف")
        verbose_name_plural = _("المصروفات")

    def __str__(self):
        return f"{self.number} - {self.category.name} - {self.amount}"

    def save(self, *args, **kwargs):
        # حفظ النموذج أولاً
        is_new = self.pk is None
        super().save(*args, **kwargs)

        # إذا كان جديدًا وليس له معاملة مرتبطة، قم بعملية الترحيل تلقائيًا
        if is_new and not self.created_transaction:
            self.post_expense()

    def post_expense(self):
        """ترحيل المصروف وإنشاء المعاملة المالية المرتبطة"""
        if self.is_posted and self.created_transaction:
            return False

        # إنشاء حركة الخزنة
        current_balance = self.safe.current_balance
        # المصروفات تنقص رصيد الخزنة
        balance_after = current_balance - self.amount

        safe_transaction = SafeTransaction(
            safe=self.safe,
            date=self.date,  # استخدام تاريخ المصروف
            amount=self.amount,
            transaction_type=SafeTransaction.EXPENSE,
            description=f"مصروف: {self.category.name} - {self.payee}",
            reference_number=self.number,
            balance_before=current_balance,  # تعيين الرصيد قبل العملية
            balance_after=balance_after  # تعيين الرصيد بعد العملية
        )

        safe_transaction.save()
        self.created_transaction = safe_transaction

        # تحديث حالة الترحيل
        self.is_posted = True
        self.save(update_fields=['is_posted', 'created_transaction'])

        return True

    def unpost_expense(self):
        """إلغاء ترحيل المصروف وحذف المعاملة المالية المرتبطة"""
        if not self.is_posted:
            return False

        # حذف حركة الخزنة إذا وجدت
        if self.created_transaction:
            self.created_transaction.delete()
            self.created_transaction = None

        # تحديث حالة الترحيل
        self.is_posted = False
        self.save(update_fields=['is_posted', 'created_transaction'])

        return True

class Income(models.Model):
    """نموذج الإيرادات في النظام"""

    number = models.CharField(_("رقم المستند"), max_length=50, blank=True)
    date = models.DateTimeField(_("تاريخ المستند"), default=timezone.now)
    amount = models.DecimalField(_("المبلغ"), max_digits=15, decimal_places=2)
    category = models.ForeignKey(IncomeCategory, on_delete=models.PROTECT, related_name='incomes',
                               verbose_name=_("قسم الإيرادات"))
    safe = models.ForeignKey(Safe, on_delete=models.CASCADE, related_name='incomes',
                           verbose_name=_("الخزنة"))
    payer = models.CharField(_("الدافع"), max_length=255)
    notes = models.TextField(_("ملاحظات"), blank=True, null=True)
    reference_number = models.CharField(_("الرقم المرجعي"), max_length=50, blank=True, null=True)
    is_posted = models.BooleanField(_("مرحل"), default=True)

    # معرف حركة الخزنة التي تم إنشاؤها بواسطة هذا الإيراد
    created_transaction = models.OneToOneField(SafeTransaction, on_delete=models.SET_NULL,
                                         null=True, blank=True, related_name='created_by_income',
                                         verbose_name=_("حركة الخزنة المنشأة"))

    class Meta:
        verbose_name = _("إيراد")
        verbose_name_plural = _("الإيرادات")

    def __str__(self):
        return f"{self.number} - {self.category.name} - {self.amount}"

    def save(self, *args, **kwargs):
        # حفظ النموذج أولاً
        is_new = self.pk is None
        super().save(*args, **kwargs)

        # إذا كان جديدًا وليس له معاملة مرتبطة، قم بعملية الترحيل تلقائيًا
        if is_new and not self.created_transaction:
            self.post_income()

    def post_income(self):
        """ترحيل الإيراد وإنشاء المعاملة المالية المرتبطة"""
        if self.is_posted and self.created_transaction:
            return False

        # إنشاء حركة الخزنة
        current_balance = self.safe.current_balance
        # الإيرادات تزيد رصيد الخزنة
        balance_after = current_balance + self.amount

        safe_transaction = SafeTransaction(
            safe=self.safe,
            date=self.date,  # استخدام تاريخ الإيراد
            amount=self.amount,
            transaction_type=SafeTransaction.INCOME,
            description=f"إيراد: {self.category.name} - {self.payer}",
            reference_number=self.number,
            balance_before=current_balance,  # تعيين الرصيد قبل العملية
            balance_after=balance_after  # تعيين الرصيد بعد العملية
        )

        safe_transaction.save()
        self.created_transaction = safe_transaction

        # تحديث حالة الترحيل
        self.is_posted = True
        self.save(update_fields=['is_posted', 'created_transaction'])

        return True

    def unpost_income(self):
        """إلغاء ترحيل الإيراد وحذف المعاملة المالية المرتبطة"""
        if not self.is_posted:
            return False

        # حذف حركة الخزنة إذا وجدت
        if self.created_transaction:
            self.created_transaction.delete()
            self.created_transaction = None

        # تحديث حالة الترحيل
        self.is_posted = False
        self.save(update_fields=['is_posted', 'created_transaction'])

        return True

class SafeDeposit(models.Model):
    """نموذج إيداع في الخزنة"""

    number = models.CharField(_("رقم المستند"), max_length=50, blank=True)
    date = models.DateTimeField(_("تاريخ المستند"), default=timezone.now)
    amount = models.DecimalField(_("المبلغ"), max_digits=15, decimal_places=2)
    safe = models.ForeignKey(Safe, on_delete=models.CASCADE, related_name='deposits',
                           verbose_name=_("الخزنة"))
    source = models.CharField(_("مصدر الإيداع"), max_length=255)
    notes = models.TextField(_("ملاحظات"), blank=True, null=True)
    reference_number = models.CharField(_("الرقم المرجعي"), max_length=50, blank=True, null=True)
    is_posted = models.BooleanField(_("مرحل"), default=True)

    # معرف حركة الخزنة التي تم إنشاؤها بواسطة هذا الإيداع
    created_transaction = models.OneToOneField(SafeTransaction, on_delete=models.SET_NULL,
                                           null=True, blank=True, related_name='created_by_deposit',
                                           verbose_name=_("حركة الخزنة المنشأة"))

    class Meta:
        verbose_name = _("إيداع في الخزنة")
        verbose_name_plural = _("الإيداعات في الخزن")

    def __str__(self):
        return f"{self.number} - {self.safe.name} - {self.amount}"

    def save(self, *args, **kwargs):
        # حفظ النموذج أولاً
        is_new = self.pk is None
        super().save(*args, **kwargs)

        # إذا كان جديدًا وليس له معاملة مرتبطة، قم بعملية الترحيل تلقائيًا
        if is_new and not self.created_transaction:
            self.post_deposit()

    def post_deposit(self):
        """ترحيل الإيداع وإنشاء المعاملة المالية المرتبطة"""
        if self.is_posted and self.created_transaction:
            return False

        # إنشاء حركة الخزنة
        current_balance = self.safe.current_balance
        # الإيداعات تزيد رصيد الخزنة
        balance_after = current_balance + self.amount

        safe_transaction = SafeTransaction(
            safe=self.safe,
            date=self.date,  # استخدام تاريخ الإيداع
            amount=self.amount,
            transaction_type=SafeTransaction.DEPOSIT,
            description=f"إيداع في الخزنة: {self.source}",
            reference_number=self.number,
            balance_before=current_balance,  # تعيين الرصيد قبل العملية
            balance_after=balance_after  # تعيين الرصيد بعد العملية
        )

        safe_transaction.save()
        self.created_transaction = safe_transaction

        # تحديث حالة الترحيل
        self.is_posted = True
        self.save(update_fields=['is_posted', 'created_transaction'])

        return True

    def unpost_deposit(self):
        """إلغاء ترحيل الإيداع وحذف المعاملة المالية المرتبطة"""
        if not self.is_posted:
            return False

        # حذف حركة الخزنة إذا وجدت
        if self.created_transaction:
            self.created_transaction.delete()
            self.created_transaction = None

        # تحديث حالة الترحيل
        self.is_posted = False
        self.save(update_fields=['is_posted', 'created_transaction'])

        return True

class SafeWithdrawal(models.Model):
    """نموذج سحب من الخزنة"""

    number = models.CharField(_("رقم المستند"), max_length=50, blank=True)
    date = models.DateTimeField(_("تاريخ المستند"), default=timezone.now)
    amount = models.DecimalField(_("المبلغ"), max_digits=15, decimal_places=2)
    safe = models.ForeignKey(Safe, on_delete=models.CASCADE, related_name='withdrawals',
                           verbose_name=_("الخزنة"))
    destination = models.CharField(_("جهة السحب"), max_length=255)
    notes = models.TextField(_("ملاحظات"), blank=True, null=True)
    reference_number = models.CharField(_("الرقم المرجعي"), max_length=50, blank=True, null=True)
    is_posted = models.BooleanField(_("مرحل"), default=True)

    # معرف حركة الخزنة التي تم إنشاؤها بواسطة هذا السحب
    created_transaction = models.OneToOneField(SafeTransaction, on_delete=models.SET_NULL,
                                          null=True, blank=True, related_name='created_by_withdrawal',
                                          verbose_name=_("حركة الخزنة المنشأة"))

    class Meta:
        verbose_name = _("سحب من الخزنة")
        verbose_name_plural = _("السحوبات من الخزن")

    def __str__(self):
        return f"{self.number} - {self.safe.name} - {self.amount}"

    def save(self, *args, **kwargs):
        # حفظ النموذج أولاً
        is_new = self.pk is None
        super().save(*args, **kwargs)

        # إذا كان جديدًا وليس له معاملة مرتبطة، قم بعملية الترحيل تلقائيًا
        if is_new and not self.created_transaction:
            self.post_withdrawal()

    def post_withdrawal(self):
        """ترحيل السحب وإنشاء المعاملة المالية المرتبطة"""
        if self.is_posted and self.created_transaction:
            return False

        # إنشاء حركة الخزنة
        current_balance = self.safe.current_balance
        # السحوبات تنقص رصيد الخزنة
        balance_after = current_balance - self.amount

        safe_transaction = SafeTransaction(
            safe=self.safe,
            date=self.date,  # استخدام تاريخ السحب
            amount=self.amount,
            transaction_type=SafeTransaction.WITHDRAWAL,
            description=f"سحب من الخزنة: {self.destination}",
            reference_number=self.number,
            balance_before=current_balance,  # تعيين الرصيد قبل العملية
            balance_after=balance_after  # تعيين الرصيد بعد العملية
        )

        safe_transaction.save()
        self.created_transaction = safe_transaction

        # تحديث حالة الترحيل
        self.is_posted = True
        self.save(update_fields=['is_posted', 'created_transaction'])

        return True

    def unpost_withdrawal(self):
        """إلغاء ترحيل السحب وحذف المعاملة المالية المرتبطة"""
        if not self.is_posted:
            return False

        # حذف حركة الخزنة إذا وجدت
        if self.created_transaction:
            self.created_transaction.delete()
            self.created_transaction = None

        # تحديث حالة الترحيل
        self.is_posted = False
        self.save(update_fields=['is_posted', 'created_transaction'])

        return True


class StorePermit(models.Model):
    """نموذج أذونات المخزن (صرف واستلام)"""

    # أنواع الأذونات
    ISSUE = 'issue'
    RECEIVE = 'receive'

    PERMIT_TYPES = [
        (ISSUE, _("إذن صرف")),
        (RECEIVE, _("إذن استلام")),
    ]

    number = models.CharField(_("رقم الإذن"), max_length=50, unique=True)
    permit_type = models.CharField(_("نوع الإذن"), max_length=10, choices=PERMIT_TYPES)
    date = models.DateTimeField(_("تاريخ الإذن"), default=timezone.now)
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name='permits', verbose_name=_("المخزن"))
    person_name = models.CharField(_("اسم الشخص"), max_length=255, help_text=_("المستلم في حالة الصرف أو المرسل في حالة الاستلام"))
    driver = models.ForeignKey(Driver, on_delete=models.SET_NULL, null=True, blank=True, related_name='permits', verbose_name=_("السائق"))
    representative = models.ForeignKey(Representative, on_delete=models.SET_NULL, null=True, blank=True, related_name='permits', verbose_name=_("المندوب"))
    reference_number = models.CharField(_("الرقم المرجعي"), max_length=50, blank=True, null=True)
    notes = models.TextField(_("ملاحظات"), blank=True, null=True)
    is_posted = models.BooleanField(_("مرحل"), default=False)

    class Meta:
        verbose_name = _("إذن مخزني")
        verbose_name_plural = _("أذونات المخزن")
        ordering = ['-date']

    def __str__(self):
        return f"{self.get_permit_type_display()} - {self.number}"

    def post_permit(self):
        """ترحيل الإذن وإنشاء حركات المنتجات المرتبطة"""
        if self.is_posted:
            return False

        from django.db import transaction

        with transaction.atomic():
            # إنشاء حركات المنتجات لكل بند في الإذن
            for item in self.items.all():
                # حساب الكمية بالوحدة الأساسية
                base_quantity = item.quantity * item.product_unit.conversion_factor

                # تحديد نوع الحركة بناءً على نوع الإذن
                if self.permit_type == self.ISSUE:
                    transaction_type = ProductTransaction.SALE
                    description = f"صرف من المخزن: {self.number} - {self.person_name}"
                else:  # RECEIVE
                    transaction_type = ProductTransaction.PURCHASE
                    description = f"استلام في المخزن: {self.number} - {self.person_name}"

                # الحصول على الرصيد الحالي للمنتج
                current_balance = item.product.current_balance

                # حساب الرصيد بعد العملية
                if self.permit_type == self.ISSUE:
                    # صرف ينقص الرصيد
                    balance_after = current_balance - base_quantity
                else:  # RECEIVE
                    # استلام يزيد الرصيد
                    balance_after = current_balance + base_quantity

                # إنشاء حركة المنتج
                product_transaction = ProductTransaction(
                    product=item.product,
                    date=self.date,
                    quantity=item.quantity,
                    product_unit=item.product_unit,
                    base_quantity=base_quantity,
                    transaction_type=transaction_type,
                    store=self.store,
                    description=description,
                    reference_number=self.number,
                    balance_before=current_balance,
                    balance_after=balance_after
                )

                product_transaction.save()

                # ربط حركة المنتج بالإذن
                item.created_transaction = product_transaction
                item.save(update_fields=['created_transaction'])

                # تحديث رصيد المنتج
                item.product.current_balance = balance_after
                item.product.save(update_fields=['current_balance'])

            # تحديث حالة الترحيل
            self.is_posted = True
            self.save(update_fields=['is_posted'])

            return True

    def unpost_permit(self):
        """إلغاء ترحيل الإذن وحذف حركات المنتجات المرتبطة"""
        if not self.is_posted:
            return False

        from django.db import transaction

        with transaction.atomic():
            # حذف حركات المنتجات لكل بند في الإذن
            for item in self.items.all():
                if item.created_transaction:
                    # حفظ المنتج قبل حذف الحركة
                    product = item.created_transaction.product

                    # حذف حركة المنتج
                    item.created_transaction.delete()
                    item.created_transaction = None
                    item.save(update_fields=['created_transaction'])

                    # إعادة حساب أرصدة المنتج
                    ProductTransaction.recalculate_balances(product)

            # تحديث حالة الترحيل
            self.is_posted = False
            self.save(update_fields=['is_posted'])

            return True


class StorePermitItem(models.Model):
    """نموذج بنود أذونات المخزن"""

    permit = models.ForeignKey(StorePermit, on_delete=models.CASCADE, related_name='items', verbose_name=_("الإذن"))
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='permit_items', verbose_name=_("المنتج"))
    product_unit = models.ForeignKey(ProductUnit, on_delete=models.CASCADE, related_name='permit_items', verbose_name=_("وحدة المنتج"))
    quantity = models.DecimalField(_("الكمية"), max_digits=15, decimal_places=3)
    notes = models.TextField(_("ملاحظات"), blank=True, null=True)

    # معرف حركة المنتج التي تم إنشاؤها بواسطة هذا البند
    created_transaction = models.OneToOneField(ProductTransaction, on_delete=models.SET_NULL,
                                          null=True, blank=True, related_name='created_by_permit_item',
                                          verbose_name=_("حركة المنتج المنشأة"))

    class Meta:
        verbose_name = _("بند إذن مخزني")
        verbose_name_plural = _("بنود أذونات المخزن")

    def __str__(self):
        return f"{self.product.name} - {self.formatted_quantity} {self.product_unit.unit.name}"

    @property
    def formatted_quantity(self):
        """تنسيق الكمية كرقم صحيح إذا كانت بدون كسور"""
        if self.quantity == int(self.quantity):
            return int(self.quantity)
        return self.quantity

    def save(self, *args, **kwargs):
        """تقريب الكمية إلى رقم صحيح إذا كانت بدون كسور عند الحفظ"""
        # إذا كانت الكمية تساوي قيمتها المقربة إلى أقرب عدد صحيح
        if self.quantity == round(self.quantity):
            # تحويل الكمية إلى عدد صحيح إذا كانت بدون كسور
            if self.quantity == int(self.quantity):
                # لا نغير القيمة الفعلية في قاعدة البيانات، فقط طريقة العرض
                pass

        super().save(*args, **kwargs)
