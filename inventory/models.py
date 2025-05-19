from django.db import models
from django.utils import timezone
from django.db.models import Sum, F
from django.core.exceptions import ValidationError

# Create your models here.

class Supplier(models.Model):
    """نموذج لتسجيل بيانات الشركات الموردة للمطهرات"""

    name = models.CharField(max_length=255, verbose_name="اسم الشركة")
    contact_person = models.CharField(max_length=255, blank=True, null=True, verbose_name="الشخص المسؤول")
    phone = models.CharField(max_length=20, blank=True, null=True, verbose_name="رقم الهاتف")
    email = models.EmailField(blank=True, null=True, verbose_name="البريد الإلكتروني")
    address = models.TextField(blank=True, null=True, verbose_name="العنوان")
    is_active = models.BooleanField(default=True, verbose_name="نشط")
    notes = models.TextField(blank=True, null=True, verbose_name="ملاحظات")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإنشاء")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاريخ التحديث")

    class Meta:
        verbose_name = "مورد"
        verbose_name_plural = "الموردين"
        ordering = ['name']

    def __str__(self):
        return self.name


class DisinfectantCategory(models.Model):
    """نموذج لتصنيفات المطهرات"""

    name = models.CharField(max_length=255, verbose_name="اسم التصنيف")
    description = models.TextField(blank=True, null=True, verbose_name="وصف التصنيف")

    class Meta:
        verbose_name = "تصنيف مطهر"
        verbose_name_plural = "تصنيفات المطهرات"
        ordering = ['name']

    def __str__(self):
        return self.name


class Disinfectant(models.Model):
    """نموذج لتسجيل بيانات المطهرات"""

    name = models.CharField(max_length=255, verbose_name="اسم المطهر")
    category = models.ForeignKey(
        DisinfectantCategory,
        on_delete=models.PROTECT,
        related_name='disinfectants',
        verbose_name="التصنيف"
    )
    unit = models.CharField(max_length=50, verbose_name="وحدة القياس")
    minimum_stock = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name="الحد الأدنى للمخزون"
    )
    description = models.TextField(blank=True, null=True, verbose_name="وصف المطهر")
    is_active = models.BooleanField(default=True, verbose_name="نشط")
    notes = models.TextField(blank=True, null=True, verbose_name="ملاحظات")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإنشاء")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاريخ التحديث")

    class Meta:
        verbose_name = "مطهر"
        verbose_name_plural = "المطهرات"
        ordering = ['name']

    def __str__(self):
        return self.name

    @property
    def current_stock(self):
        """حساب الرصيد الحالي للمطهر"""
        received = self.received_items.aggregate(total=Sum('quantity'))['total'] or 0
        issued = self.issued_items.aggregate(total=Sum('quantity'))['total'] or 0
        return received - issued

    @property
    def stock_status(self):
        """حالة المخزون (طبيعي، منخفض، نفذ)"""
        current = self.current_stock
        if current <= 0:
            return "نفذ"
        elif current < self.minimum_stock:
            return "منخفض"
        else:
            return "طبيعي"


class DisinfectantReceived(models.Model):
    """نموذج لتسجيل المطهرات الواردة من الشركات الموردة"""

    disinfectant = models.ForeignKey(
        Disinfectant,
        on_delete=models.PROTECT,
        related_name='received_items',
        verbose_name="المطهر"
    )
    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.PROTECT,
        related_name='supplied_items',
        verbose_name="المورد"
    )
    date = models.DateField(default=timezone.now, verbose_name="تاريخ الاستلام")
    quantity = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="الكمية")
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="سعر الوحدة")
    invoice_number = models.CharField(max_length=100, blank=True, null=True, verbose_name="رقم الفاتورة")
    expiry_date = models.DateField(blank=True, null=True, verbose_name="تاريخ انتهاء الصلاحية")
    notes = models.TextField(blank=True, null=True, verbose_name="ملاحظات")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإنشاء")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاريخ التحديث")

    class Meta:
        verbose_name = "وارد مطهر"
        verbose_name_plural = "واردات المطهرات"
        ordering = ['-date']

    def __str__(self):
        return f"{self.disinfectant} - {self.date} - {self.quantity}"

    @property
    def total_price(self):
        """حساب إجمالي السعر"""
        return self.quantity * self.unit_price


class DisinfectantIssued(models.Model):
    """نموذج لتسجيل المطهرات المنصرفة للمعمل"""

    disinfectant = models.ForeignKey(
        Disinfectant,
        on_delete=models.PROTECT,
        related_name='issued_items',
        verbose_name="المطهر"
    )
    date = models.DateField(default=timezone.now, verbose_name="تاريخ الصرف")
    quantity = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="الكمية")
    issued_to = models.CharField(max_length=255, verbose_name="صرف إلى")
    purpose = models.TextField(blank=True, null=True, verbose_name="الغرض من الصرف")
    notes = models.TextField(blank=True, null=True, verbose_name="ملاحظات")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإنشاء")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاريخ التحديث")

    class Meta:
        verbose_name = "صرف مطهر"
        verbose_name_plural = "صرفيات المطهرات"
        ordering = ['-date']

    def __str__(self):
        return f"{self.disinfectant} - {self.date} - {self.quantity}"

    def clean(self):
        """التحقق من أن الكمية المنصرفة لا تتجاوز الرصيد المتاح"""
        if self.pk:  # إذا كان هذا تحديثًا لسجل موجود
            # استثناء الكمية الحالية من الحساب
            current = DisinfectantIssued.objects.get(pk=self.pk)
            if current.disinfectant == self.disinfectant:
                # نفس المطهر، نحسب الفرق
                available = self.disinfectant.current_stock + current.quantity
            else:
                # تغيير المطهر، نحسب الرصيد الكامل للمطهر الجديد
                available = self.disinfectant.current_stock
        else:
            # سجل جديد
            available = self.disinfectant.current_stock

        if self.quantity > available:
            raise ValidationError(f"الكمية المتاحة من المطهر {self.disinfectant} هي {available} {self.disinfectant.unit} فقط.")
