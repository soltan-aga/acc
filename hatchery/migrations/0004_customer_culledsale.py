# Generated by Django 5.2.1 on 2025-05-09 23:18

import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("hatchery", "0003_batchhatching"),
    ]

    operations = [
        migrations.CreateModel(
            name="Customer",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=255, verbose_name="اسم العميل")),
                (
                    "phone",
                    models.CharField(
                        blank=True, max_length=20, null=True, verbose_name="رقم الهاتف"
                    ),
                ),
                (
                    "address",
                    models.TextField(blank=True, null=True, verbose_name="العنوان"),
                ),
                ("is_active", models.BooleanField(default=True, verbose_name="نشط")),
                (
                    "notes",
                    models.TextField(blank=True, null=True, verbose_name="ملاحظات"),
                ),
                (
                    "created_at",
                    models.DateTimeField(
                        auto_now_add=True, verbose_name="تاريخ الإنشاء"
                    ),
                ),
                (
                    "updated_at",
                    models.DateTimeField(auto_now=True, verbose_name="تاريخ التحديث"),
                ),
            ],
            options={
                "verbose_name": "عميل",
                "verbose_name_plural": "العملاء",
                "ordering": ["name"],
            },
        ),
        migrations.CreateModel(
            name="CulledSale",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "invoice_date",
                    models.DateField(
                        default=django.utils.timezone.now, verbose_name="تاريخ الفاتورة"
                    ),
                ),
                (
                    "quantity",
                    models.PositiveIntegerField(verbose_name="عدد الكتاكيت الفرزة"),
                ),
                (
                    "price_per_unit",
                    models.DecimalField(
                        decimal_places=2, max_digits=10, verbose_name="السعر للوحدة"
                    ),
                ),
                (
                    "paid_amount",
                    models.DecimalField(
                        decimal_places=2,
                        default=0,
                        max_digits=10,
                        verbose_name="المبلغ المدفوع",
                    ),
                ),
                (
                    "notes",
                    models.TextField(blank=True, null=True, verbose_name="ملاحظات"),
                ),
                (
                    "created_at",
                    models.DateTimeField(
                        auto_now_add=True, verbose_name="تاريخ الإنشاء"
                    ),
                ),
                (
                    "updated_at",
                    models.DateTimeField(auto_now=True, verbose_name="تاريخ التحديث"),
                ),
                (
                    "hatching",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="culled_sales",
                        to="hatchery.batchhatching",
                        verbose_name="دفعة الخروج",
                    ),
                ),
                (
                    "customer",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="culled_sales",
                        to="hatchery.customer",
                        verbose_name="اسم العميل",
                    ),
                ),
            ],
            options={
                "verbose_name": "بيع فرزة",
                "verbose_name_plural": "مبيعات الفرزة",
                "ordering": ["-invoice_date"],
            },
        ),
    ]
