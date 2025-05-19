from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django.http import HttpResponseRedirect
from django.contrib import messages
from .models import Invoice, InvoiceItem, Payment

class InvoiceItemInline(admin.TabularInline):
    model = InvoiceItem
    extra = 1

@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('number', 'date', 'invoice_type', 'payment_type', 'contact', 'store',
                   'total_amount', 'discount_amount', 'tax_amount', 'net_amount', 'paid_amount',
                   'remaining_amount', 'is_posted', 'get_post_actions')
    list_filter = ('invoice_type', 'payment_type', 'store', 'date', 'is_posted')
    search_fields = ('number', 'contact__name', 'notes')
    date_hierarchy = 'date'
    readonly_fields = ('get_post_actions',)
    inlines = [InvoiceItemInline]

    actions = ['post_multiple_invoices', 'unpost_multiple_invoices']

    def get_form(self, request, obj=None, **kwargs):
        """تعديل النموذج لإضافة رقم فاتورة تلقائي"""
        form = super().get_form(request, obj, **kwargs)
        if obj is None:  # فقط عند إنشاء فاتورة جديدة
            # إنشاء رقم فاتورة جديد
            last_invoice = Invoice.objects.order_by('-id').first()
            if not last_invoice:
                new_number = "1"  # أول فاتورة في النظام
            else:
                # استخراج الرقم من آخر فاتورة
                try:
                    if '-' in last_invoice.number:
                        last_number = int(last_invoice.number.split('-')[1])
                    else:
                        last_number = int(last_invoice.number)
                    new_number = str(last_number + 1)  # زيادة الرقم بمقدار 1
                except (ValueError, IndexError):
                    # في حالة حدوث خطأ في تحليل الرقم، استخدم الرقم 1
                    new_number = "1"

            # تعيين القيمة الافتراضية لحقل رقم الفاتورة
            form.base_fields['number'].initial = new_number
        return form

    def get_readonly_fields(self, request, obj=None):
        """جعل بعض الحقول للقراءة فقط بناءً على حالة الكائن"""
        readonly_fields = list(self.readonly_fields)
        if obj:  # فقط عند تحرير فاتورة موجودة
            if obj.is_posted:
                # إذا كانت الفاتورة مرحلة، اجعل معظم الحقول للقراءة فقط
                readonly_fields.extend(['invoice_type', 'payment_type', 'contact', 'store',
                                      'safe', 'is_posted', 'number'])
        else:
            # عند إنشاء فاتورة جديدة
            readonly_fields.append('is_posted')

        return readonly_fields

    def get_post_actions(self, obj):
        """عرض أزرار الترحيل وإلغاء الترحيل في قائمة الفواتير"""
        if obj.pk:
            if obj.is_posted:
                # إذا كانت الفاتورة مرحلة، اعرض زر إلغاء الترحيل
                return format_html(
                    '<a class="button" style="background-color: #ff6b6b; color: white; padding: 3px 10px; border-radius: 4px;" href="{}">إلغاء الترحيل</a>',
                    reverse('admin:unpost_invoice', args=[obj.pk])
                )
            else:
                # إذا كانت الفاتورة غير مرحلة، اعرض زر الترحيل
                return format_html(
                    '<a class="button" style="background-color: #4CAF50; color: white; padding: 3px 10px; border-radius: 4px;" href="{}">ترحيل</a>',
                    reverse('admin:post_invoice', args=[obj.pk])
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
                self.admin_site.admin_view(self.post_invoice_view),
                name='post_invoice',
            ),
            path(
                '<path:object_id>/unpost/',
                self.admin_site.admin_view(self.unpost_invoice_view),
                name='unpost_invoice',
            ),
        ]
        return custom_urls + urls

    def post_invoice_view(self, request, object_id):
        """عرض لترحيل الفاتورة"""
        invoice = self.get_object(request, object_id)
        success = invoice.post_invoice()

        if success:
            messages.success(request, f'تم ترحيل الفاتورة {invoice.number} بنجاح وإنشاء المعاملات المالية والمخزنية.')
        else:
            messages.error(request, f'لم يتم ترحيل الفاتورة {invoice.number}. قد تكون مرحلة بالفعل.')

        return HttpResponseRedirect(reverse('admin:invoices_invoice_changelist'))

    def unpost_invoice_view(self, request, object_id):
        """عرض لإلغاء ترحيل الفاتورة"""
        invoice = self.get_object(request, object_id)
        success = invoice.unpost_invoice()

        if success:
            messages.success(request, f'تم إلغاء ترحيل الفاتورة {invoice.number} بنجاح وحذف المعاملات المالية والمخزنية.')
        else:
            messages.error(request, f'لم يتم إلغاء ترحيل الفاتورة {invoice.number}. قد تكون غير مرحلة بالفعل.')

        return HttpResponseRedirect(reverse('admin:invoices_invoice_changelist'))

    def post_multiple_invoices(self, request, queryset):
        """ترحيل فواتير متعددة من خلال القائمة"""
        posted_count = 0
        for invoice in queryset:
            if invoice.post_invoice():
                posted_count += 1

        if posted_count:
            messages.success(request, f'تم ترحيل {posted_count} فاتورة بنجاح.')
        else:
            messages.warning(request, 'لم يتم ترحيل أي فاتورة. ربما تكون الفواتير مرحلة بالفعل.')

    post_multiple_invoices.short_description = _("ترحيل الفواتير المحددة")

    def unpost_multiple_invoices(self, request, queryset):
        """إلغاء ترحيل فواتير متعددة من خلال القائمة"""
        unposted_count = 0
        for invoice in queryset:
            if invoice.unpost_invoice():
                unposted_count += 1

        if unposted_count:
            messages.success(request, f'تم إلغاء ترحيل {unposted_count} فاتورة بنجاح.')
        else:
            messages.warning(request, 'لم يتم إلغاء ترحيل أي فاتورة. ربما تكون الفواتير غير مرحلة بالفعل.')

    unpost_multiple_invoices.short_description = _("إلغاء ترحيل الفواتير المحددة")

    def response_add(self, request, obj, post_url_continue=None):
        """إضافة رسالة بعد إنشاء الفاتورة"""
        response = super().response_add(request, obj, post_url_continue)
        if obj:
            messages.info(request, f'تم إنشاء الفاتورة {obj.number} بنجاح. لا تنس ترحيل الفاتورة بعد إضافة بنود الفاتورة لإنشاء المعاملات المالية والمخزنية المرتبطة.')
        return response

@admin.register(InvoiceItem)
class InvoiceItemAdmin(admin.ModelAdmin):
    list_display = ('invoice', 'product', 'product_unit', 'quantity', 'unit_price',
                   'total_price', 'discount_amount', 'tax_amount', 'net_price')
    list_filter = ('invoice__invoice_type', 'product__category')
    search_fields = ('invoice__number', 'product__name')

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('number', 'date', 'get_payment_type_colored', 'contact', 'amount',
                  'safe', 'invoice_link', 'is_posted', 'get_post_actions')
    list_filter = ('payment_type', 'is_posted', 'date')
    search_fields = ('number', 'contact__name', 'reference_number', 'notes')
    date_hierarchy = 'date'
    readonly_fields = ('is_posted', 'get_post_actions')

    actions = ['post_multiple_payments', 'unpost_multiple_payments']

    def get_form(self, request, obj=None, **kwargs):
        """تعديل النموذج لإضافة رقم مستند تلقائي"""
        form = super().get_form(request, obj, **kwargs)
        if obj is None:  # فقط عند إنشاء مستند جديد
            # إنشاء رقم مستند جديد
            last_payment = Payment.objects.order_by('-id').first()
            if not last_payment:
                new_number = "1"  # أول مستند في النظام
            else:
                # استخراج الرقم من آخر مستند
                try:
                    if '-' in last_payment.number:
                        last_number = int(last_payment.number.split('-')[1])
                    else:
                        last_number = int(last_payment.number)
                    new_number = str(last_number + 1)  # زيادة الرقم بمقدار 1
                except (ValueError, IndexError):
                    # في حالة حدوث خطأ في تحليل الرقم، استخدم الرقم 1
                    new_number = "1"

            # تعيين القيمة الافتراضية لحقل رقم المستند
            form.base_fields['number'].initial = new_number
        return form

    def get_payment_type_colored(self, obj):
        """عرض نوع العملية بألوان مختلفة حسب النوع"""
        colors = {
            'receipt': '#4CAF50',  # أخضر للتحصيل (زيادة في الخزنة)
            'payment': '#f44336',  # أحمر للدفع (نقص في الخزنة)
        }

        color = colors.get(obj.payment_type, '#000000')  # لون أسود افتراضي
        return format_html('<span style="color: {}; font-weight: bold;">{}</span>',
                          color, obj.get_payment_type_display())

    get_payment_type_colored.short_description = _("نوع العملية")
    get_payment_type_colored.admin_order_field = 'payment_type'

    def invoice_link(self, obj):
        """رابط للفاتورة المرتبطة بالسند إن وجدت"""
        if obj.invoice:
            return format_html('<a href="{}">{} - {}</a>',
                             f'/admin/invoices/invoice/{obj.invoice.id}/change/',
                             obj.invoice.number,
                             obj.invoice.get_invoice_type_display())
        return "-"

    invoice_link.short_description = _("الفاتورة المرتبطة")
    invoice_link.admin_order_field = 'invoice'

    def get_post_actions(self, obj):
        """عرض أزرار الترحيل وإلغاء الترحيل في قائمة السندات"""
        if obj.pk:
            if obj.is_posted:
                # إذا كان السند مرحل، اعرض زر إلغاء الترحيل
                return format_html(
                    '<a class="button" style="background-color: #ff6b6b; color: white; padding: 3px 10px; border-radius: 4px;" href="{}">إلغاء الترحيل</a>',
                    reverse('admin:unpost_payment', args=[obj.pk])
                )
            else:
                # إذا كان السند غير مرحل، اعرض زر الترحيل
                return format_html(
                    '<a class="button" style="background-color: #4CAF50; color: white; padding: 3px 10px; border-radius: 4px;" href="{}">ترحيل</a>',
                    reverse('admin:post_payment', args=[obj.pk])
                )
        return "-"

    get_post_actions.short_description = _("الترحيل")
    get_post_actions.allow_tags = True

    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()
        custom_urls = [
            path(
                '<path:object_id>/post/',
                self.admin_site.admin_view(self.post_payment_view),
                name='post_payment',
            ),
            path(
                '<path:object_id>/unpost/',
                self.admin_site.admin_view(self.unpost_payment_view),
                name='unpost_payment',
            ),
        ]
        return custom_urls + urls

    def post_payment_view(self, request, object_id):
        """عرض لترحيل سند القبض/الصرف"""
        payment = self.get_object(request, object_id)
        success = payment.post_payment()

        if success:
            messages.success(request, f'تم ترحيل السند {payment.number} بنجاح وإنشاء المعاملات المالية المرتبطة.')
        else:
            messages.error(request, f'لم يتم ترحيل السند {payment.number}. قد يكون مرحل بالفعل.')

        return HttpResponseRedirect(reverse('admin:invoices_payment_changelist'))

    def unpost_payment_view(self, request, object_id):
        """عرض لإلغاء ترحيل سند القبض/الصرف"""
        payment = self.get_object(request, object_id)
        success = payment.unpost_payment()

        if success:
            messages.success(request, f'تم إلغاء ترحيل السند {payment.number} بنجاح وحذف المعاملات المالية المرتبطة.')
        else:
            messages.error(request, f'لم يتم إلغاء ترحيل السند {payment.number}. قد يكون غير مرحل بالفعل.')

        return HttpResponseRedirect(reverse('admin:invoices_payment_changelist'))

    def post_multiple_payments(self, request, queryset):
        """ترحيل سندات متعددة من خلال القائمة"""
        posted_count = 0
        for payment in queryset:
            if payment.post_payment():
                posted_count += 1

        if posted_count:
            messages.success(request, f'تم ترحيل {posted_count} سند بنجاح.')
        else:
            messages.warning(request, 'لم يتم ترحيل أي سند. ربما تكون السندات مرحلة بالفعل.')

    post_multiple_payments.short_description = _("ترحيل السندات المحددة")

    def unpost_multiple_payments(self, request, queryset):
        """إلغاء ترحيل سندات متعددة من خلال القائمة"""
        unposted_count = 0
        for payment in queryset:
            if payment.unpost_payment():
                unposted_count += 1

        if unposted_count:
            messages.success(request, f'تم إلغاء ترحيل {unposted_count} سند بنجاح.')
        else:
            messages.warning(request, 'لم يتم إلغاء ترحيل أي سند. ربما تكون السندات غير مرحلة بالفعل.')

    unpost_multiple_payments.short_description = _("إلغاء ترحيل السندات المحددة")
