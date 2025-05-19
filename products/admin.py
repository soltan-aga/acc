from django.contrib import admin
from .models import Category, Unit, Product, ProductUnit

class ProductUnitInline(admin.TabularInline):
    model = ProductUnit
    extra = 1

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'parent', 'description')
    list_filter = ('parent',)
    search_fields = ('name', 'description')

@admin.register(Unit)
class UnitAdmin(admin.ModelAdmin):
    list_display = ('name', 'symbol')
    search_fields = ('name', 'symbol')

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'category', 'default_store', 'initial_balance', 'current_balance', 'is_active')
    list_filter = ('category', 'default_store', 'is_active')
    search_fields = ('name', 'code', 'barcode', 'description')
    inlines = [ProductUnitInline]

@admin.register(ProductUnit)
class ProductUnitAdmin(admin.ModelAdmin):
    list_display = ('product', 'unit', 'conversion_factor', 'purchase_price', 'selling_price', 
                   'is_default_purchase', 'is_default_sale')
    list_filter = ('unit', 'is_default_purchase', 'is_default_sale')
    search_fields = ('product__name', 'unit__name')
