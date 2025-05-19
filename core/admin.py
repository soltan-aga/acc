from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import Company, Branch, Store, Safe, Representative, Driver, Contact, SystemSettings

@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'email', 'tax_number')
    search_fields = ('name', 'phone', 'email', 'tax_number')

@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ('name', 'company', 'phone', 'manager')
    list_filter = ('company',)
    search_fields = ('name', 'phone', 'manager')

@admin.register(Store)
class StoreAdmin(admin.ModelAdmin):
    list_display = ('name', 'branch', 'keeper')
    list_filter = ('branch__company', 'branch')
    search_fields = ('name', 'keeper')

@admin.register(Safe)
class SafeAdmin(admin.ModelAdmin):
    list_display = ('name', 'branch', 'initial_balance', 'current_balance')
    list_filter = ('branch__company', 'branch')
    search_fields = ('name',)

@admin.register(Representative)
class RepresentativeAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'commission_percentage')
    search_fields = ('name', 'phone', 'id_number')

@admin.register(Driver)
class DriverAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'license_number')
    search_fields = ('name', 'phone', 'id_number', 'license_number')

@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ('name', 'contact_type', 'phone', 'current_balance', 'credit_limit')
    list_filter = ('contact_type',)
    search_fields = ('name', 'phone', 'email', 'tax_number')


@admin.register(SystemSettings)
class SystemSettingsAdmin(admin.ModelAdmin):
    """إدارة إعدادات النظام"""
    fieldsets = (
        (_('إعدادات الفواتير'), {
            'fields': (
                'default_invoice_type', 'update_purchase_price', 'update_sale_price',
                'alert_below_sale_price', 'alert_below_purchase_price',
                'allow_duplicate_items', 'auto_increase_quantity',
                'default_customer', 'default_supplier', 'default_safe', 'default_store'
            ),
        }),
        (_('إعدادات طباعة الفاتورة'), {
            'fields': (
                'hide_company_info', 'show_previous_balance',
                'invoice_header_text', 'invoice_footer_text'
            ),
        }),
        (_('إعدادات طباعة تقرير الأذونات المخزنية'), {
            'fields': (
                'show_driver_in_permit_report', 'show_representative_in_permit_report'
            ),
        }),
    )

    def has_add_permission(self, request):
        # منع إضافة إعدادات جديدة إذا كان هناك إعدادات موجودة بالفعل
        return not SystemSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        # منع حذف الإعدادات
        return False
