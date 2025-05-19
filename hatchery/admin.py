from django.contrib import admin
from django.utils import timezone
from django.utils.html import format_html
from .models import BatchName, BatchEntry, BatchIncubation, BatchHatching, Customer, CulledSale

# Register your models here.

@admin.register(BatchName)
class BatchNameAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'description')
    ordering = ('name',)


class BatchIncubationInline(admin.TabularInline):
    model = BatchIncubation
    extra = 0
    fields = ('incubation_date', 'incubation_quantity', 'damaged_quantity', 'expected_hatch_date')
    readonly_fields = ('expected_hatch_date',)


@admin.register(BatchEntry)
class BatchEntryAdmin(admin.ModelAdmin):
    list_display = ('batch_name', 'date', 'quantity', 'driver')
    list_filter = ('date', 'batch_name')
    search_fields = ('batch_name__name', 'driver', 'notes')
    date_hierarchy = 'date'
    ordering = ('-date',)
    autocomplete_fields = ['batch_name']
    inlines = [BatchIncubationInline]


class BatchHatchingInline(admin.StackedInline):
    model = BatchHatching
    extra = 0
    fields = ('hatch_date', 'chicks_count', 'culled_count', 'dead_count', 'fertility_rate', 'hatch_rate', 'notes')


@admin.register(BatchIncubation)
class BatchIncubationAdmin(admin.ModelAdmin):
    list_display = ('batch_entry', 'incubation_date', 'incubation_quantity', 'damaged_quantity', 'expected_hatch_date', 'is_ready_to_hatch')
    list_filter = ('incubation_date', 'expected_hatch_date', 'batch_entry__batch_name')
    search_fields = ('batch_entry__batch_name__name', 'notes')
    date_hierarchy = 'incubation_date'
    ordering = ('-incubation_date',)
    autocomplete_fields = ['batch_entry']
    readonly_fields = ('expected_hatch_date', 'is_ready_to_hatch')
    inlines = [BatchHatchingInline]

    def is_ready_to_hatch(self, obj):
        today = timezone.now().date()
        is_ready = obj.expected_hatch_date <= today
        return is_ready

    is_ready_to_hatch.boolean = True
    is_ready_to_hatch.short_description = "جاهز للخروج"


class CulledSaleInline(admin.TabularInline):
    model = CulledSale
    extra = 0
    fields = ('customer', 'invoice_date', 'quantity', 'price_per_unit', 'paid_amount')
    autocomplete_fields = ['customer']


@admin.register(BatchHatching)
class BatchHatchingAdmin(admin.ModelAdmin):
    list_display = ('incubation', 'hatch_date', 'chicks_count', 'culled_count', 'dead_count', 'wasted_count', 'fertility_rate', 'hatch_rate', 'available_culled_count')
    list_filter = ('hatch_date',)
    search_fields = ('incubation__batch_entry__batch_name__name', 'notes')
    date_hierarchy = 'hatch_date'
    ordering = ('-hatch_date',)
    autocomplete_fields = ['incubation']
    readonly_fields = ('wasted_count', 'available_culled_count')
    inlines = [CulledSaleInline]

    def available_culled_count(self, obj):
        return obj.available_culled_count

    available_culled_count.short_description = "الفرزة المتاحة للبيع"

    def wasted_count(self, obj):
        return obj.wasted_count

    wasted_count.short_description = "عدد المعدم"


class CulledSaleInline(admin.TabularInline):
    model = CulledSale
    extra = 0
    fields = ('customer', 'invoice_date', 'quantity', 'price_per_unit', 'paid_amount')
    autocomplete_fields = ['customer']


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'address', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'phone', 'address', 'notes')
    ordering = ('name',)


@admin.register(CulledSale)
class CulledSaleAdmin(admin.ModelAdmin):
    list_display = ('customer', 'hatching', 'invoice_date', 'quantity', 'price_per_unit', 'total_amount', 'paid_amount', 'remaining_amount', 'payment_status')
    list_filter = ('invoice_date', 'customer', 'hatching__incubation__batch_entry__batch_name')
    search_fields = ('customer__name', 'hatching__incubation__batch_entry__batch_name__name', 'notes')
    date_hierarchy = 'invoice_date'
    ordering = ('-invoice_date',)
    autocomplete_fields = ['customer', 'hatching']
    readonly_fields = ('total_amount', 'remaining_amount')

    def total_amount(self, obj):
        return obj.total_amount

    def remaining_amount(self, obj):
        return obj.remaining_amount

    def payment_status(self, obj):
        if obj.remaining_amount <= 0:
            return format_html('<span style="color: green;">مدفوع بالكامل</span>')
        elif obj.paid_amount > 0:
            return format_html('<span style="color: orange;">مدفوع جزئيًا</span>')
        else:
            return format_html('<span style="color: red;">غير مدفوع</span>')

    total_amount.short_description = "الإجمالي"
    remaining_amount.short_description = "المتبقي"
    payment_status.short_description = "حالة الدفع"
