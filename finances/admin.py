from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.contrib import messages
from .models import (
    SafeTransaction, ContactTransaction, ProductTransaction,
    ExpenseCategory, IncomeCategory, Expense, Income, SafeDeposit, SafeWithdrawal,
    StorePermit, StorePermitItem
)

@admin.register(SafeTransaction)
class SafeTransactionAdmin(admin.ModelAdmin):
    list_display = ('safe', 'date', 'get_transaction_type_colored', 'amount', 'description',
                   'invoice_link', 'contact_link', 'balance_before', 'balance_after')
    list_filter = ('transaction_type', 'safe', 'date')
    search_fields = ('description', 'reference_number', 'invoice__number', 'contact__name')
    date_hierarchy = 'date'
    readonly_fields = ('balance_before', 'balance_after')

    def get_transaction_type_colored(self, obj):
        """عرض نوع العملية بألوان مختلفة حسب النوع"""
        colors = {
            'sale_invoice': '#4CAF50',  # أخضر
            'purchase_invoice': '#f44336',  # أحمر
            'sale_return_invoice': '#ff9800',  # برتقالي
            'purchase_return_invoice': '#2196F3',  # أزرق
            'collection': '#9C27B0',  # بنفسجي
            'payment': '#795548',  # بني
            'deposit': '#3F51B5',  # أزرق داكن
            'withdrawal': '#FF5722',  # برتقالي داكن
            'expense': '#E91E63',  # وردي
            'income': '#009688',  # فيروزي
        }

        color = colors.get(obj.transaction_type, '#000000')  # لون أسود افتراضي
        return format_html('<span style="color: {}; font-weight: bold;">{}</span>',
                          color, obj.get_transaction_type_display())

    get_transaction_type_colored.short_description = _("نوع العملية")
    get_transaction_type_colored.admin_order_field = 'transaction_type'

    def invoice_link(self, obj):
        """رابط للفاتورة المرتبطة بالحركة"""
        if obj.invoice:
            return format_html('<a href="{}">{} - {}</a>',
                             f'/admin/invoices/invoice/{obj.invoice.id}/change/',
                             obj.invoice.number,
                             obj.invoice.get_invoice_type_display())
        return "-"

    invoice_link.short_description = _("الفاتورة")
    invoice_link.admin_order_field = 'invoice'

    def contact_link(self, obj):
        """رابط لجهة الاتصال المرتبطة بالحركة"""
        if obj.contact:
            return format_html('<a href="{}">{} - {}</a>',
                             f'/admin/core/contact/{obj.contact.id}/change/',
                             obj.contact.name,
                             obj.contact.get_contact_type_display())
        return "-"

    contact_link.short_description = _("جهة الاتصال")
    contact_link.admin_order_field = 'contact'

@admin.register(ContactTransaction)
class ContactTransactionAdmin(admin.ModelAdmin):
    list_display = ('contact', 'date', 'get_transaction_type_colored', 'amount', 'invoice_link',
                   'description', 'balance_before', 'balance_after')
    list_filter = ('transaction_type', 'contact__contact_type', 'date')
    search_fields = ('description', 'reference_number', 'invoice__number', 'contact__name')
    date_hierarchy = 'date'
    readonly_fields = ('balance_before', 'balance_after')

    def get_transaction_type_colored(self, obj):
        """عرض نوع العملية بألوان مختلفة حسب النوع"""
        colors = {
            'sale_invoice': '#4CAF50',  # أخضر
            'purchase_invoice': '#f44336',  # أحمر
            'sale_return_invoice': '#ff9800',  # برتقالي
            'purchase_return_invoice': '#2196F3',  # أزرق
            'collection': '#9C27B0',  # بنفسجي
            'payment': '#795548',  # بني
        }

        color = colors.get(obj.transaction_type, '#000000')  # لون أسود افتراضي
        return format_html('<span style="color: {}; font-weight: bold;">{}</span>',
                          color, obj.get_transaction_type_display())

    get_transaction_type_colored.short_description = _("نوع العملية")
    get_transaction_type_colored.admin_order_field = 'transaction_type'

    def invoice_link(self, obj):
        """رابط للفاتورة المرتبطة بالحركة"""
        if obj.invoice:
            return format_html('<a href="{}">{} - {}</a>',
                             f'/admin/invoices/invoice/{obj.invoice.id}/change/',
                             obj.invoice.number,
                             obj.invoice.get_invoice_type_display())
        return "-"

    invoice_link.short_description = _("الفاتورة")
    invoice_link.admin_order_field = 'invoice'

@admin.register(ProductTransaction)
class ProductTransactionAdmin(admin.ModelAdmin):
    list_display = ('product', 'date', 'get_transaction_type_colored', 'quantity', 'product_unit',
                   'quantity_display', 'base_quantity', 'invoice_link', 'balance_before', 'balance_after', 'balance_display')
    list_filter = ('transaction_type', 'product__category', 'date')
    search_fields = ('description', 'reference_number', 'invoice__number', 'product__name')
    date_hierarchy = 'date'
    readonly_fields = ('balance_before', 'balance_after', 'base_quantity', 'quantity_display', 'balance_display')

    def get_transaction_type_colored(self, obj):
        """عرض نوع العملية بألوان مختلفة حسب النوع"""
        colors = {
            'sale': '#f44336',  # أحمر (لأنه يقلل المخزون)
            'purchase': '#4CAF50',  # أخضر (لأنه يزيد المخزون)
            'sale_return': '#4CAF50',  # أخضر (لأنه يزيد المخزون)
            'purchase_return': '#f44336',  # أحمر (لأنه يقلل المخزون)
            'adjustment': '#2196F3',  # أزرق
        }

        color = colors.get(obj.transaction_type, '#000000')  # لون أسود افتراضي
        return format_html('<span style="color: {}; font-weight: bold;">{}</span>',
                          color, obj.get_transaction_type_display())

    get_transaction_type_colored.short_description = _("نوع العملية")
    get_transaction_type_colored.admin_order_field = 'transaction_type'

    def invoice_link(self, obj):
        """رابط للفاتورة المرتبطة بالحركة"""
        if obj.invoice:
            return format_html('<a href="{}">{} - {}</a>',
                             f'/admin/invoices/invoice/{obj.invoice.id}/change/',
                             obj.invoice.number,
                             obj.invoice.get_invoice_type_display())
        return "-"

    invoice_link.short_description = _("الفاتورة")
    invoice_link.admin_order_field = 'invoice'

# تسجيل أقسام المصروفات والإيرادات
@admin.register(ExpenseCategory)
class ExpenseCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'parent', 'description')
    list_filter = ('parent',)
    search_fields = ('name', 'description')

@admin.register(IncomeCategory)
class IncomeCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'parent', 'description')
    list_filter = ('parent',)
    search_fields = ('name', 'description')

# تسجيل نموذج المصروفات
@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ('number', 'date', 'category', 'payee', 'amount', 'safe', 'is_posted', 'get_post_actions')
    list_filter = ('category', 'safe', 'date', 'is_posted')
    search_fields = ('number', 'payee', 'notes', 'reference_number')
    date_hierarchy = 'date'
    readonly_fields = ('is_posted', 'get_post_actions')

    actions = ['post_multiple_expenses', 'unpost_multiple_expenses']

    def get_post_actions(self, obj):
        """عرض أزرار الترحيل وإلغاء الترحيل في قائمة المصروفات"""
        if obj.pk:
            if obj.is_posted:
                # إذا كان المصروف مرحل، اعرض زر إلغاء الترحيل
                return format_html(
                    '<a class="button" style="background-color: #ff6b6b; color: white; padding: 3px 10px; border-radius: 4px;" href="{}">إلغاء الترحيل</a>',
                    reverse('admin:unpost_expense', args=[obj.pk])
                )
            else:
                # إذا كان المصروف غير مرحل، اعرض زر الترحيل
                return format_html(
                    '<a class="button" style="background-color: #4CAF50; color: white; padding: 3px 10px; border-radius: 4px;" href="{}">ترحيل</a>',
                    reverse('admin:post_expense', args=[obj.pk])
                )
        return "-"

    get_post_actions.short_description = _("ترحيل")
    get_post_actions.allow_tags = True

    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()
        custom_urls = [
            path(
                '<path:object_id>/post/',
                self.admin_site.admin_view(self.post_expense_view),
                name='post_expense',
            ),
            path(
                '<path:object_id>/unpost/',
                self.admin_site.admin_view(self.unpost_expense_view),
                name='unpost_expense',
            ),
        ]
        return custom_urls + urls

    def post_expense_view(self, request, object_id):
        """عرض لترحيل المصروف"""
        expense = self.get_object(request, object_id)
        success = expense.post_expense()

        if success:
            messages.success(request, f'تم ترحيل المصروف {expense.number} بنجاح وإنشاء حركة الخزنة المرتبطة.')
        else:
            messages.error(request, f'لم يتم ترحيل المصروف {expense.number}. قد يكون مرحل بالفعل.')

        return HttpResponseRedirect(reverse('admin:finances_expense_changelist'))

    def unpost_expense_view(self, request, object_id):
        """عرض لإلغاء ترحيل المصروف"""
        expense = self.get_object(request, object_id)
        success = expense.unpost_expense()

        if success:
            messages.success(request, f'تم إلغاء ترحيل المصروف {expense.number} بنجاح وحذف حركة الخزنة المرتبطة.')
        else:
            messages.error(request, f'لم يتم إلغاء ترحيل المصروف {expense.number}. قد يكون غير مرحل بالفعل.')

        return HttpResponseRedirect(reverse('admin:finances_expense_changelist'))

    def post_multiple_expenses(self, request, queryset):
        """ترحيل مصروفات متعددة من خلال القائمة"""
        posted_count = 0
        for expense in queryset:
            if expense.post_expense():
                posted_count += 1

        if posted_count:
            messages.success(request, f'تم ترحيل {posted_count} مصروف بنجاح.')
        else:
            messages.warning(request, 'لم يتم ترحيل أي مصروف. ربما تكون المصروفات مرحلة بالفعل.')

    post_multiple_expenses.short_description = _("ترحيل المصروفات المحددة")

    def unpost_multiple_expenses(self, request, queryset):
        """إلغاء ترحيل مصروفات متعددة من خلال القائمة"""
        unposted_count = 0
        for expense in queryset:
            if expense.unpost_expense():
                unposted_count += 1

        if unposted_count:
            messages.success(request, f'تم إلغاء ترحيل {unposted_count} مصروف بنجاح.')
        else:
            messages.warning(request, 'لم يتم إلغاء ترحيل أي مصروف. ربما تكون المصروفات غير مرحلة بالفعل.')

    unpost_multiple_expenses.short_description = _("إلغاء ترحيل المصروفات المحددة")

# تسجيل نموذج الإيرادات
@admin.register(Income)
class IncomeAdmin(admin.ModelAdmin):
    list_display = ('number', 'date', 'category', 'payer', 'amount', 'safe', 'is_posted', 'get_post_actions')
    list_filter = ('category', 'safe', 'date', 'is_posted')
    search_fields = ('number', 'payer', 'notes', 'reference_number')
    date_hierarchy = 'date'
    readonly_fields = ('is_posted', 'get_post_actions')

    actions = ['post_multiple_incomes', 'unpost_multiple_incomes']

    def get_post_actions(self, obj):
        """عرض أزرار الترحيل وإلغاء الترحيل في قائمة الإيرادات"""
        if obj.pk:
            if obj.is_posted:
                # إذا كان الإيراد مرحل، اعرض زر إلغاء الترحيل
                return format_html(
                    '<a class="button" style="background-color: #ff6b6b; color: white; padding: 3px 10px; border-radius: 4px;" href="{}">إلغاء الترحيل</a>',
                    reverse('admin:unpost_income', args=[obj.pk])
                )
            else:
                # إذا كان الإيراد غير مرحل، اعرض زر الترحيل
                return format_html(
                    '<a class="button" style="background-color: #4CAF50; color: white; padding: 3px 10px; border-radius: 4px;" href="{}">ترحيل</a>',
                    reverse('admin:post_income', args=[obj.pk])
                )
        return "-"

    get_post_actions.short_description = _("ترحيل")
    get_post_actions.allow_tags = True

    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()
        custom_urls = [
            path(
                '<path:object_id>/post/',
                self.admin_site.admin_view(self.post_income_view),
                name='post_income',
            ),
            path(
                '<path:object_id>/unpost/',
                self.admin_site.admin_view(self.unpost_income_view),
                name='unpost_income',
            ),
        ]
        return custom_urls + urls

    def post_income_view(self, request, object_id):
        """عرض لترحيل الإيراد"""
        income = self.get_object(request, object_id)
        success = income.post_income()

        if success:
            messages.success(request, f'تم ترحيل الإيراد {income.number} بنجاح وإنشاء حركة الخزنة المرتبطة.')
        else:
            messages.error(request, f'لم يتم ترحيل الإيراد {income.number}. قد يكون مرحل بالفعل.')

        return HttpResponseRedirect(reverse('admin:finances_income_changelist'))

    def unpost_income_view(self, request, object_id):
        """عرض لإلغاء ترحيل الإيراد"""
        income = self.get_object(request, object_id)
        success = income.unpost_income()

        if success:
            messages.success(request, f'تم إلغاء ترحيل الإيراد {income.number} بنجاح وحذف حركة الخزنة المرتبطة.')
        else:
            messages.error(request, f'لم يتم إلغاء ترحيل الإيراد {income.number}. قد يكون غير مرحل بالفعل.')

        return HttpResponseRedirect(reverse('admin:finances_income_changelist'))

    def post_multiple_incomes(self, request, queryset):
        """ترحيل إيرادات متعددة من خلال القائمة"""
        posted_count = 0
        for income in queryset:
            if income.post_income():
                posted_count += 1

        if posted_count:
            messages.success(request, f'تم ترحيل {posted_count} إيراد بنجاح.')
        else:
            messages.warning(request, 'لم يتم ترحيل أي إيراد. ربما تكون الإيرادات مرحلة بالفعل.')

    post_multiple_incomes.short_description = _("ترحيل الإيرادات المحددة")

    def unpost_multiple_incomes(self, request, queryset):
        """إلغاء ترحيل إيرادات متعددة من خلال القائمة"""
        unposted_count = 0
        for income in queryset:
            if income.unpost_income():
                unposted_count += 1

        if unposted_count:
            messages.success(request, f'تم إلغاء ترحيل {unposted_count} إيراد بنجاح.')
        else:
            messages.warning(request, 'لم يتم إلغاء ترحيل أي إيراد. ربما تكون الإيرادات غير مرحلة بالفعل.')

    unpost_multiple_incomes.short_description = _("إلغاء ترحيل الإيرادات المحددة")

# تسجيل نموذج الإيداع في الخزنة
@admin.register(SafeDeposit)
class SafeDepositAdmin(admin.ModelAdmin):
    list_display = ('number', 'date', 'source', 'amount', 'safe', 'is_posted', 'get_post_actions')
    list_filter = ('safe', 'date', 'is_posted')
    search_fields = ('number', 'source', 'notes', 'reference_number')
    date_hierarchy = 'date'
    readonly_fields = ('is_posted', 'get_post_actions')

    actions = ['post_multiple_deposits', 'unpost_multiple_deposits']

    def get_post_actions(self, obj):
        """عرض أزرار الترحيل وإلغاء الترحيل في قائمة الإيداعات"""
        if obj.pk:
            if obj.is_posted:
                # إذا كان الإيداع مرحل، اعرض زر إلغاء الترحيل
                return format_html(
                    '<a class="button" style="background-color: #ff6b6b; color: white; padding: 3px 10px; border-radius: 4px;" href="{}">إلغاء الترحيل</a>',
                    reverse('admin:unpost_deposit', args=[obj.pk])
                )
            else:
                # إذا كان الإيداع غير مرحل، اعرض زر الترحيل
                return format_html(
                    '<a class="button" style="background-color: #4CAF50; color: white; padding: 3px 10px; border-radius: 4px;" href="{}">ترحيل</a>',
                    reverse('admin:post_deposit', args=[obj.pk])
                )
        return "-"

    get_post_actions.short_description = _("ترحيل")
    get_post_actions.allow_tags = True

    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()
        custom_urls = [
            path(
                '<path:object_id>/post/',
                self.admin_site.admin_view(self.post_deposit_view),
                name='post_deposit',
            ),
            path(
                '<path:object_id>/unpost/',
                self.admin_site.admin_view(self.unpost_deposit_view),
                name='unpost_deposit',
            ),
        ]
        return custom_urls + urls

    def post_deposit_view(self, request, object_id):
        """عرض لترحيل الإيداع"""
        deposit = self.get_object(request, object_id)
        success = deposit.post_deposit()

        if success:
            messages.success(request, f'تم ترحيل الإيداع {deposit.number} بنجاح وإنشاء حركة الخزنة المرتبطة.')
        else:
            messages.error(request, f'لم يتم ترحيل الإيداع {deposit.number}. قد يكون مرحل بالفعل.')

        return HttpResponseRedirect(reverse('admin:finances_safedeposit_changelist'))

    def unpost_deposit_view(self, request, object_id):
        """عرض لإلغاء ترحيل الإيداع"""
        deposit = self.get_object(request, object_id)
        success = deposit.unpost_deposit()

        if success:
            messages.success(request, f'تم إلغاء ترحيل الإيداع {deposit.number} بنجاح وحذف حركة الخزنة المرتبطة.')
        else:
            messages.error(request, f'لم يتم إلغاء ترحيل الإيداع {deposit.number}. قد يكون غير مرحل بالفعل.')

        return HttpResponseRedirect(reverse('admin:finances_safedeposit_changelist'))

    def post_multiple_deposits(self, request, queryset):
        """ترحيل إيداعات متعددة من خلال القائمة"""
        posted_count = 0
        for deposit in queryset:
            if deposit.post_deposit():
                posted_count += 1

        if posted_count:
            messages.success(request, f'تم ترحيل {posted_count} إيداع بنجاح.')
        else:
            messages.warning(request, 'لم يتم ترحيل أي إيداع. ربما تكون الإيداعات مرحلة بالفعل.')

    post_multiple_deposits.short_description = _("ترحيل الإيداعات المحددة")

    def unpost_multiple_deposits(self, request, queryset):
        """إلغاء ترحيل إيداعات متعددة من خلال القائمة"""
        unposted_count = 0
        for deposit in queryset:
            if deposit.unpost_deposit():
                unposted_count += 1

        if unposted_count:
            messages.success(request, f'تم إلغاء ترحيل {unposted_count} إيداع بنجاح.')
        else:
            messages.warning(request, 'لم يتم إلغاء ترحيل أي إيداع. ربما تكون الإيداعات غير مرحلة بالفعل.')

    unpost_multiple_deposits.short_description = _("إلغاء ترحيل الإيداعات المحددة")

# تسجيل نموذج السحب من الخزنة
@admin.register(SafeWithdrawal)
class SafeWithdrawalAdmin(admin.ModelAdmin):
    list_display = ('number', 'date', 'destination', 'amount', 'safe', 'is_posted', 'get_post_actions')
    list_filter = ('safe', 'date', 'is_posted')
    search_fields = ('number', 'destination', 'notes', 'reference_number')
    date_hierarchy = 'date'
    readonly_fields = ('is_posted', 'get_post_actions')

    actions = ['post_multiple_withdrawals', 'unpost_multiple_withdrawals']

    def get_post_actions(self, obj):
        """عرض أزرار الترحيل وإلغاء الترحيل في قائمة السحوبات"""
        if obj.pk:
            if obj.is_posted:
                # إذا كان السحب مرحل، اعرض زر إلغاء الترحيل
                return format_html(
                    '<a class="button" style="background-color: #ff6b6b; color: white; padding: 3px 10px; border-radius: 4px;" href="{}">إلغاء الترحيل</a>',
                    reverse('admin:unpost_withdrawal', args=[obj.pk])
                )
            else:
                # إذا كان السحب غير مرحل، اعرض زر الترحيل
                return format_html(
                    '<a class="button" style="background-color: #4CAF50; color: white; padding: 3px 10px; border-radius: 4px;" href="{}">ترحيل</a>',
                    reverse('admin:post_withdrawal', args=[obj.pk])
                )
        return "-"

    get_post_actions.short_description = _("ترحيل")
    get_post_actions.allow_tags = True

    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()
        custom_urls = [
            path(
                '<path:object_id>/post/',
                self.admin_site.admin_view(self.post_withdrawal_view),
                name='post_withdrawal',
            ),
            path(
                '<path:object_id>/unpost/',
                self.admin_site.admin_view(self.unpost_withdrawal_view),
                name='unpost_withdrawal',
            ),
        ]
        return custom_urls + urls

    def post_withdrawal_view(self, request, object_id):
        """عرض لترحيل السحب"""
        withdrawal = self.get_object(request, object_id)
        success = withdrawal.post_withdrawal()

        if success:
            messages.success(request, f'تم ترحيل السحب {withdrawal.number} بنجاح وإنشاء حركة الخزنة المرتبطة.')
        else:
            messages.error(request, f'لم يتم ترحيل السحب {withdrawal.number}. قد يكون مرحل بالفعل.')

        return HttpResponseRedirect(reverse('admin:finances_safewithdrawal_changelist'))

    def unpost_withdrawal_view(self, request, object_id):
        """عرض لإلغاء ترحيل السحب"""
        withdrawal = self.get_object(request, object_id)
        success = withdrawal.unpost_withdrawal()

        if success:
            messages.success(request, f'تم إلغاء ترحيل السحب {withdrawal.number} بنجاح وحذف حركة الخزنة المرتبطة.')
        else:
            messages.error(request, f'لم يتم إلغاء ترحيل السحب {withdrawal.number}. قد يكون غير مرحل بالفعل.')

        return HttpResponseRedirect(reverse('admin:finances_safewithdrawal_changelist'))

    def post_multiple_withdrawals(self, request, queryset):
        """ترحيل سحوبات متعددة من خلال القائمة"""
        posted_count = 0
        for withdrawal in queryset:
            if withdrawal.post_withdrawal():
                posted_count += 1

        if posted_count:
            messages.success(request, f'تم ترحيل {posted_count} سحب بنجاح.')
        else:
            messages.warning(request, 'لم يتم ترحيل أي سحب. ربما تكون السحوبات مرحلة بالفعل.')

    post_multiple_withdrawals.short_description = _("ترحيل السحوبات المحددة")

    def unpost_multiple_withdrawals(self, request, queryset):
        """إلغاء ترحيل سحوبات متعددة من خلال القائمة"""
        unposted_count = 0
        for withdrawal in queryset:
            if withdrawal.unpost_withdrawal():
                unposted_count += 1

        if unposted_count:
            messages.success(request, f'تم إلغاء ترحيل {unposted_count} سحب بنجاح.')
        else:
            messages.warning(request, 'لم يتم إلغاء ترحيل أي سحب. ربما تكون السحوبات غير مرحلة بالفعل.')

    unpost_multiple_withdrawals.short_description = _("إلغاء ترحيل السحوبات المحددة")





class StorePermitItemInline(admin.TabularInline):
    model = StorePermitItem
    extra = 1
    fields = ('product', 'product_unit', 'quantity', 'notes')


@admin.register(StorePermit)
class StorePermitAdmin(admin.ModelAdmin):
    list_display = ('get_permit_type_display', 'number', 'date', 'store', 'person_name', 'driver', 'representative', 'is_posted')
    list_filter = ('permit_type', 'store', 'is_posted', 'date')
    search_fields = ('number', 'person_name', 'notes', 'reference_number')
    readonly_fields = ('is_posted',)
    inlines = [StorePermitItemInline]
    actions = ['post_permit_action', 'unpost_permit_action']

    def get_permit_type_display(self, obj):
        """عرض نوع الإذن بألوان مختلفة"""
        if obj.permit_type == StorePermit.ISSUE:
            return format_html('<span style="color: #f44336; font-weight: bold;">إذن صرف</span>')
        else:
            return format_html('<span style="color: #4CAF50; font-weight: bold;">إذن استلام</span>')

    get_permit_type_display.short_description = _("نوع الإذن")
    get_permit_type_display.admin_order_field = 'permit_type'

    def post_permit_action(self, request, queryset):
        """ترحيل الأذونات المحددة"""
        posted_count = 0
        for permit in queryset:
            if not permit.is_posted:
                success = permit.post_permit()
                if success:
                    posted_count += 1

        if posted_count > 0:
            messages.success(request, f'تم ترحيل {posted_count} إذن بنجاح.')
        else:
            messages.warning(request, 'لم يتم ترحيل أي أذونات. قد تكون مرحلة بالفعل أو لا تحتوي على بنود.')

    post_permit_action.short_description = "ترحيل الأذونات المحددة"

    def unpost_permit_action(self, request, queryset):
        """إلغاء ترحيل الأذونات المحددة"""
        unposted_count = 0
        for permit in queryset:
            if permit.is_posted:
                success = permit.unpost_permit()
                if success:
                    unposted_count += 1

        if unposted_count > 0:
            messages.success(request, f'تم إلغاء ترحيل {unposted_count} إذن بنجاح.')
        else:
            messages.warning(request, 'لم يتم إلغاء ترحيل أي أذونات. قد تكون غير مرحلة بالفعل.')

    unpost_permit_action.short_description = "إلغاء ترحيل الأذونات المحددة"
