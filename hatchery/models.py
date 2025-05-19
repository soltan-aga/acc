from django.db import models
from django.utils import timezone
from datetime import timedelta

# Create your models here.

class BatchName(models.Model):
    """نموذج لتسجيل أسماء الدفعات"""

    name = models.CharField(max_length=255, unique=True, verbose_name="اسم الدفعة")
    description = models.TextField(blank=True, null=True, verbose_name="وصف الدفعة")
    is_active = models.BooleanField(default=True, verbose_name="نشط")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإنشاء")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاريخ التحديث")

    class Meta:
        verbose_name = "اسم دفعة"
        verbose_name_plural = "أسماء الدفعات"
        ordering = ['name']

    def __str__(self):
        return self.name


class BatchEntry(models.Model):
    """نموذج لإدارة الدفعات الواردة إلى المعمل"""

    batch_name = models.ForeignKey(
        BatchName,
        on_delete=models.PROTECT,
        related_name='entries',
        verbose_name="اسم الدفعة"
    )
    date = models.DateField(default=timezone.now, verbose_name="تاريخ الاستلام")
    quantity = models.PositiveIntegerField(verbose_name="العدد")
    driver = models.CharField(max_length=255, verbose_name="اسم السائق")
    notes = models.TextField(blank=True, null=True, verbose_name="ملاحظات")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإنشاء")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاريخ التحديث")

    class Meta:
        verbose_name = "دفعة واردة"
        verbose_name_plural = "الدفعات الواردة"
        ordering = ['-date']

    def __str__(self):
        return f"{self.batch_name} - {self.date} - {self.quantity}"


class BatchIncubation(models.Model):
    """نموذج لإدارة تسكين الدفعات في المعمل"""

    batch_entry = models.ForeignKey(
        BatchEntry,
        on_delete=models.CASCADE,
        related_name='incubations',
        verbose_name="الدفعة الواردة"
    )
    incubation_date = models.DateField(default=timezone.now, verbose_name="تاريخ التسكين")
    incubation_quantity = models.PositiveIntegerField(verbose_name="عدد التسكين")
    damaged_quantity = models.PositiveIntegerField(default=0, verbose_name="المعدم عند التسكين")
    expected_hatch_date = models.DateField(verbose_name="تاريخ الخروج المتوقع")
    notes = models.TextField(blank=True, null=True, verbose_name="ملاحظات")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإنشاء")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاريخ التحديث")

    class Meta:
        verbose_name = "تسكين دفعة"
        verbose_name_plural = "تسكين الدفعات"
        ordering = ['-incubation_date']

    def save(self, *args, **kwargs):
        # حساب تاريخ الخروج المتوقع (21 يوم من تاريخ التسكين)
        if not self.expected_hatch_date:
            self.expected_hatch_date = self.incubation_date + timedelta(days=21)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.batch_entry.batch_name} - تسكين {self.incubation_date} - {self.incubation_quantity}"

    @property
    def is_ready_to_hatch(self):
        """التحقق مما إذا كانت الدفعة جاهزة للخروج (تاريخ الخروج المتوقع هو اليوم أو قبله)"""
        today = timezone.now().date()
        return self.expected_hatch_date <= today


class BatchHatching(models.Model):
    """نموذج لإدارة خروج الدفعات من المعمل"""

    incubation = models.OneToOneField(
        BatchIncubation,
        on_delete=models.CASCADE,
        related_name='hatching',
        verbose_name="الدفعة المسكنة"
    )
    hatch_date = models.DateField(default=timezone.now, verbose_name="تاريخ الخروج")
    chicks_count = models.PositiveIntegerField(verbose_name="عدد الكتاكيت")
    culled_count = models.PositiveIntegerField(verbose_name="عدد الفرزة")
    dead_count = models.PositiveIntegerField(verbose_name="عدد الفاطس")
    fertility_rate = models.DecimalField(max_digits=5, decimal_places=2, verbose_name="نسبة الإخصاب (%)")
    hatch_rate = models.DecimalField(max_digits=5, decimal_places=2, verbose_name="نسبة الفقس الحقيقية (%)")
    notes = models.TextField(blank=True, null=True, verbose_name="ملاحظات")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإنشاء")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاريخ التحديث")

    def save(self, *args, **kwargs):
        # حساب نسبة الفقس الحقيقية تلقائيًا
        if self.incubation and self.chicks_count is not None:
            # عدد البيض المخصب = عدد البيض المسكن - الفاقد عند التسكين
            fertile_eggs = self.incubation.incubation_quantity - self.incubation.damaged_quantity
            if fertile_eggs > 0:
                # نسبة الفقس الحقيقية = (عدد الكتاكيت / عدد البيض المخصب) * 100
                self.hatch_rate = round((self.chicks_count / fertile_eggs) * 100, 2)

        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "خروج دفعة"
        verbose_name_plural = "خروج الدفعات"
        ordering = ['-hatch_date']

    def __str__(self):
        return f"{self.incubation.batch_entry.batch_name} - خروج {self.hatch_date} - {self.chicks_count}"

    @property
    def wasted_count(self):
        """حساب عدد المعدم (الفرق بين عدد التسكين والمجموع الكلي للكتاكيت والفرزة والفاطس)"""
        total_output = self.chicks_count + self.culled_count + self.dead_count
        return self.incubation.incubation_quantity - self.incubation.damaged_quantity - total_output

    @property
    def available_culled_count(self):
        """حساب عدد الكتاكيت الفرزة المتاحة للبيع (بعد خصم المباعة)"""
        sold_count = sum(sale.quantity for sale in self.culled_sales.all())
        return self.culled_count - sold_count


class Customer(models.Model):
    """نموذج لتسجيل بيانات العملاء"""

    name = models.CharField(max_length=255, verbose_name="اسم العميل")
    phone = models.CharField(max_length=20, blank=True, null=True, verbose_name="رقم الهاتف")
    address = models.TextField(blank=True, null=True, verbose_name="العنوان")
    is_active = models.BooleanField(default=True, verbose_name="نشط")
    notes = models.TextField(blank=True, null=True, verbose_name="ملاحظات")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإنشاء")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاريخ التحديث")

    class Meta:
        verbose_name = "عميل"
        verbose_name_plural = "العملاء"
        ordering = ['name']

    def __str__(self):
        return self.name


class CulledSale(models.Model):
    """نموذج لتسجيل مبيعات الكتاكيت الفرزة"""

    customer = models.ForeignKey(
        Customer,
        on_delete=models.PROTECT,
        related_name='culled_sales',
        verbose_name="اسم العميل"
    )
    hatching = models.ForeignKey(
        BatchHatching,
        on_delete=models.PROTECT,
        related_name='culled_sales',
        verbose_name="دفعة الخروج"
    )
    invoice_date = models.DateField(default=timezone.now, verbose_name="تاريخ الفاتورة")
    quantity = models.PositiveIntegerField(verbose_name="عدد الكتاكيت الفرزة")
    price_per_unit = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="السعر للوحدة")
    paid_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="المبلغ المدفوع")
    notes = models.TextField(blank=True, null=True, verbose_name="ملاحظات")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإنشاء")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاريخ التحديث")

    class Meta:
        verbose_name = "بيع فرزة"
        verbose_name_plural = "مبيعات الفرزة"
        ordering = ['-invoice_date']

    def __str__(self):
        return f"{self.customer} - {self.invoice_date} - {self.quantity}"

    @property
    def total_amount(self):
        """حساب إجمالي المبلغ"""
        return self.quantity * self.price_per_unit

    @property
    def remaining_amount(self):
        """حساب المبلغ المتبقي"""
        return self.total_amount - self.paid_amount

    def clean(self):
        from django.core.exceptions import ValidationError

        # التحقق من أن عدد الكتاكيت الفرزة المباعة لا يتجاوز العدد المتاح
        available = self.hatching.available_culled_count
        if self.pk:  # إذا كان هذا تحديثًا لسجل موجود
            # استثناء الكمية الحالية من الحساب
            current = CulledSale.objects.get(pk=self.pk)
            available += current.quantity

        if self.quantity > available:
            raise ValidationError(f"عدد الكتاكيت الفرزة المتاحة للبيع هو {available} فقط.")


class DisinfectantCategory(models.Model):
    """نموذج لتصنيفات المطهرات"""

    name = models.CharField(max_length=100, unique=True, verbose_name="اسم التصنيف")
    description = models.TextField(blank=True, null=True, verbose_name="وصف التصنيف")
    is_active = models.BooleanField(default=True, verbose_name="نشط")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإنشاء")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاريخ التحديث")

    class Meta:
        verbose_name = "تصنيف مطهر"
        verbose_name_plural = "تصنيفات المطهرات"
        ordering = ['name']

    def __str__(self):
        return self.name


class DisinfectantInventory(models.Model):
    """نموذج لمخزون المطهرات"""

    category = models.ForeignKey(
        DisinfectantCategory,
        on_delete=models.PROTECT,
        related_name='inventory_items',
        verbose_name="تصنيف المطهر"
    )
    name = models.CharField(max_length=100, verbose_name="اسم المطهر")
    supplier = models.CharField(max_length=100, blank=True, null=True, verbose_name="المورد")
    unit = models.CharField(max_length=50, verbose_name="وحدة القياس")
    current_stock = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="المخزون الحالي")
    minimum_stock = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="الحد الأدنى للمخزون")
    notes = models.TextField(blank=True, null=True, verbose_name="ملاحظات")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإنشاء")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاريخ التحديث")

    class Meta:
        verbose_name = "مخزون مطهر"
        verbose_name_plural = "مخزون المطهرات"
        ordering = ['category', 'name']

    def __str__(self):
        return f"{self.name} ({self.category})"

    @property
    def is_low_stock(self):
        """التحقق مما إذا كان المخزون منخفضًا"""
        return self.current_stock <= self.minimum_stock


class DisinfectantTransaction(models.Model):
    """نموذج لحركات المطهرات (استلام أو صرف)"""

    TRANSACTION_TYPES = (
        ('receive', 'استلام'),
        ('dispense', 'صرف'),
    )

    disinfectant = models.ForeignKey(
        DisinfectantInventory,
        on_delete=models.PROTECT,
        related_name='transactions',
        verbose_name="المطهر"
    )
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES, verbose_name="نوع الحركة")
    transaction_date = models.DateField(default=timezone.now, verbose_name="تاريخ الحركة")
    quantity = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="الكمية")
    notes = models.TextField(blank=True, null=True, verbose_name="ملاحظات")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإنشاء")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاريخ التحديث")

    class Meta:
        verbose_name = "حركة مطهر"
        verbose_name_plural = "حركات المطهرات"
        ordering = ['-transaction_date', '-created_at']

    def __str__(self):
        transaction_type_display = dict(self.TRANSACTION_TYPES)[self.transaction_type]
        return f"{self.disinfectant} - {transaction_type_display} - {self.transaction_date}"

    def save(self, *args, **kwargs):
        # تحديث المخزون الحالي للمطهر
        if self.transaction_type == 'receive':
            self.disinfectant.current_stock += self.quantity
        else:  # صرف
            self.disinfectant.current_stock -= self.quantity

        self.disinfectant.save()
        super().save(*args, **kwargs)


class BatchDistribution(models.Model):
    """نموذج لتوزيع الدفعات على العملاء"""

    hatching = models.ForeignKey(
        BatchHatching,
        on_delete=models.PROTECT,
        related_name='distributions',
        verbose_name="دفعة الخروج"
    )
    distribution_date = models.DateField(default=timezone.now, verbose_name="تاريخ التوزيع")
    notes = models.TextField(blank=True, null=True, verbose_name="ملاحظات")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإنشاء")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاريخ التحديث")

    class Meta:
        verbose_name = "توزيع دفعة"
        verbose_name_plural = "توزيعات الدفعات"
        ordering = ['-distribution_date']

    def __str__(self):
        return f"{self.hatching.incubation.batch_entry.batch_name} - {self.distribution_date}"

    @property
    def total_distributed_count(self):
        """حساب إجمالي عدد الكتاكيت الموزعة"""
        return sum(item.chicks_count for item in self.distribution_items.all())

    @property
    def total_paid_amount(self):
        """حساب إجمالي المبلغ المدفوع"""
        return sum(item.paid_amount for item in self.distribution_items.all())

    @property
    def remaining_chicks(self):
        """حساب عدد الكتاكيت المتبقية بعد التوزيع"""
        return self.hatching.chicks_count - self.total_distributed_count


class BatchDistributionItem(models.Model):
    """نموذج لعناصر توزيع الدفعات على العملاء"""

    distribution = models.ForeignKey(
        BatchDistribution,
        on_delete=models.CASCADE,
        related_name='distribution_items',
        verbose_name="توزيع الدفعة"
    )
    customer = models.ForeignKey(
        Customer,
        on_delete=models.PROTECT,
        related_name='distribution_items',
        verbose_name="العميل"
    )
    chicks_count = models.PositiveIntegerField(verbose_name="عدد الكتاكيت")
    price_per_unit = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="السعر للوحدة")
    paid_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="المبلغ المدفوع")
    notes = models.TextField(blank=True, null=True, verbose_name="ملاحظات")

    class Meta:
        verbose_name = "عنصر توزيع"
        verbose_name_plural = "عناصر التوزيع"

    def __str__(self):
        return f"{self.customer} - {self.chicks_count} كتكوت"

    @property
    def total_amount(self):
        """حساب إجمالي المبلغ"""
        return self.chicks_count * self.price_per_unit

    @property
    def remaining_amount(self):
        """حساب المبلغ المتبقي"""
        return self.total_amount - self.paid_amount
