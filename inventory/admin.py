from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Supplier,
    DisinfectantCategory,
    Disinfectant,
    DisinfectantReceived,
    DisinfectantIssued
)

# Register your models here.

@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ('name', 'contact_person', 'phone', 'email', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'contact_person', 'phone', 'email', 'address', 'notes')
    ordering = ('name',)


@admin.register(DisinfectantCategory)
class DisinfectantCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name', 'description')
    ordering = ('name',)


class DisinfectantReceivedInline(admin.TabularInline):
    model = DisinfectantReceived
    extra = 0
    fields = ('date', 'supplier', 'quantity', 'unit_price', 'invoice_number', 'expiry_date')
    autocomplete_fields = ['supplier']


class DisinfectantIssuedInline(admin.TabularInline):
    model = DisinfectantIssued
    extra = 0
    fields = ('date', 'quantity', 'issued_to', 'purpose')


@admin.register(Disinfectant)
class DisinfectantAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'unit', 'current_stock_display', 'minimum_stock', 'stock_status_display', 'is_active')
    list_filter = ('category', 'is_active')
    search_fields = ('name', 'description', 'notes')
    ordering = ('name',)
    autocomplete_fields = ['category']
    readonly_fields = ('current_stock_display', 'stock_status_display')
    inlines = [DisinfectantReceivedInline, DisinfectantIssuedInline]

    def current_stock_display(self, obj):
        return f"{obj.current_stock} {obj.unit}"

    def stock_status_display(self, obj):
        status = obj.stock_status
        if status == "نفذ":
            return format_html('<span style="color: red; font-weight: bold;">نفذ</span>')
        elif status == "منخفض":
            return format_html('<span style="color: orange; font-weight: bold;">منخفض</span>')
        else:
            return format_html('<span style="color: green;">طبيعي</span>')

    current_stock_display.short_description = "الرصيد الحالي"
    stock_status_display.short_description = "حالة المخزون"


@admin.register(DisinfectantReceived)
class DisinfectantReceivedAdmin(admin.ModelAdmin):
    list_display = ('disinfectant', 'supplier', 'date', 'quantity', 'unit_price', 'total_price_display', 'invoice_number', 'expiry_date')
    list_filter = ('date', 'supplier', 'disinfectant')
    search_fields = ('disinfectant__name', 'supplier__name', 'invoice_number', 'notes')
    date_hierarchy = 'date'
    ordering = ('-date',)
    autocomplete_fields = ['disinfectant', 'supplier']
    readonly_fields = ('total_price_display',)

    def total_price_display(self, obj):
        return obj.total_price

    total_price_display.short_description = "إجمالي السعر"


@admin.register(DisinfectantIssued)
class DisinfectantIssuedAdmin(admin.ModelAdmin):
    list_display = ('disinfectant', 'date', 'quantity', 'issued_to', 'purpose')
    list_filter = ('date', 'disinfectant', 'issued_to')
    search_fields = ('disinfectant__name', 'issued_to', 'purpose', 'notes')
    date_hierarchy = 'date'
    ordering = ('-date',)
    autocomplete_fields = ['disinfectant']
