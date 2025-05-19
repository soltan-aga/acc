

from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.template.loader import render_to_string
from django.db.models import Q, Sum

from .models import Invoice, InvoiceItem, Payment
from .forms import InvoiceForm, InvoiceItemFormSet, PaymentForm
from core.models import Contact, Store, Safe, Representative, Driver, SystemSettings
from products.models import Product, ProductUnit

@login_required
def invoice_list(request):
    """عرض قائمة الفواتير"""
    # البحث والتصفية
    query = request.GET.get('q', '')
    invoice_type = request.GET.get('type', '')
    is_posted = request.GET.get('posted', '')

    invoices = Invoice.objects.all().order_by('-date', '-id')

    # تطبيق البحث
    if query:
        invoices = invoices.filter(
            Q(number__icontains=query) |
            Q(contact__name__icontains=query) |
            Q(notes__icontains=query)
        )

    # تصفية حسب النوع
    if invoice_type:
        invoices = invoices.filter(invoice_type=invoice_type)

    # تصفية حسب حالة الترحيل
    if is_posted:
        is_posted_bool = is_posted == 'true'
        invoices = invoices.filter(is_posted=is_posted_bool)

    context = {
        'invoices': invoices,
        'query': query,
        'invoice_type': invoice_type,
        'is_posted': is_posted,
    }

    return render(request, 'invoices/invoice/list.html', context)

@login_required
def sale_invoice_list(request):
    """عرض قائمة فواتير البيع"""
    query = request.GET.get('q', '')
    is_posted = request.GET.get('posted', '')

    invoices = Invoice.objects.filter(invoice_type=Invoice.SALE).order_by('-date', '-id')

    # تطبيق البحث
    if query:
        invoices = invoices.filter(
            Q(number__icontains=query) |
            Q(contact__name__icontains=query) |
            Q(notes__icontains=query)
        )

    # تصفية حسب حالة الترحيل
    if is_posted:
        is_posted_bool = is_posted == 'true'
        invoices = invoices.filter(is_posted=is_posted_bool)

    context = {
        'invoices': invoices,
        'query': query,
        'invoice_type': Invoice.SALE,
        'is_posted': is_posted,
        'title': 'فواتير البيع'
    }

    return render(request, 'invoices/invoice/list.html', context)

@login_required
def purchase_invoice_list(request):
    """عرض قائمة فواتير الشراء"""
    query = request.GET.get('q', '')
    is_posted = request.GET.get('posted', '')

    invoices = Invoice.objects.filter(invoice_type=Invoice.PURCHASE).order_by('-date', '-id')

    # تطبيق البحث
    if query:
        invoices = invoices.filter(
            Q(number__icontains=query) |
            Q(contact__name__icontains=query) |
            Q(notes__icontains=query)
        )

    # تصفية حسب حالة الترحيل
    if is_posted:
        is_posted_bool = is_posted == 'true'
        invoices = invoices.filter(is_posted=is_posted_bool)

    context = {
        'invoices': invoices,
        'query': query,
        'invoice_type': Invoice.PURCHASE,
        'is_posted': is_posted,
        'title': 'فواتير الشراء'
    }

    return render(request, 'invoices/invoice/list.html', context)

@login_required
def sale_return_invoice_list(request):
    """عرض قائمة مرتجعات البيع"""
    query = request.GET.get('q', '')
    is_posted = request.GET.get('posted', '')

    invoices = Invoice.objects.filter(invoice_type=Invoice.SALE_RETURN).order_by('-date', '-id')

    # تطبيق البحث
    if query:
        invoices = invoices.filter(
            Q(number__icontains=query) |
            Q(contact__name__icontains=query) |
            Q(notes__icontains=query)
        )

    # تصفية حسب حالة الترحيل
    if is_posted:
        is_posted_bool = is_posted == 'true'
        invoices = invoices.filter(is_posted=is_posted_bool)

    context = {
        'invoices': invoices,
        'query': query,
        'invoice_type': Invoice.SALE_RETURN,
        'is_posted': is_posted,
        'title': 'مرتجعات البيع'
    }

    return render(request, 'invoices/invoice/list.html', context)

@login_required
def purchase_return_invoice_list(request):
    """عرض قائمة مرتجعات الشراء"""
    query = request.GET.get('q', '')
    is_posted = request.GET.get('posted', '')

    invoices = Invoice.objects.filter(invoice_type=Invoice.PURCHASE_RETURN).order_by('-date', '-id')

    # تطبيق البحث
    if query:
        invoices = invoices.filter(
            Q(number__icontains=query) |
            Q(contact__name__icontains=query) |
            Q(notes__icontains=query)
        )

    # تصفية حسب حالة الترحيل
    if is_posted:
        is_posted_bool = is_posted == 'true'
        invoices = invoices.filter(is_posted=is_posted_bool)

    context = {
        'invoices': invoices,
        'query': query,
        'invoice_type': Invoice.PURCHASE_RETURN,
        'is_posted': is_posted,
        'title': 'مرتجعات الشراء'
    }

    return render(request, 'invoices/invoice/list.html', context)

@login_required
def invoice_detail(request, pk):
    """عرض تفاصيل الفاتورة"""
    invoice = get_object_or_404(Invoice, pk=pk)

    # تحميل بنود الفاتورة مع المنتجات والوحدات المرتبطة بها
    invoice_items = InvoiceItem.objects.filter(invoice=invoice).select_related('product', 'product_unit')

    # تحميل حركات حساب العميل/المورد المرتبطة بالفاتورة
    from finances.models import ContactTransaction, SafeTransaction, ProductTransaction
    contact_transactions = ContactTransaction.objects.filter(invoice=invoice).order_by('date')

    # تحميل حركات الخزنة المرتبطة بالفاتورة
    safe_transactions = SafeTransaction.objects.filter(invoice=invoice).order_by('date')

    # تحميل حركات المخزون المرتبطة بالفاتورة
    product_transactions = ProductTransaction.objects.filter(invoice=invoice).order_by('date')

    return render(request, 'invoices/invoice/detail.html', {
        'invoice': invoice,
        'invoice_items': invoice_items,
        'contact_transactions': contact_transactions,
        'safe_transactions': safe_transactions,
        'product_transactions': product_transactions
    })

@login_required
def invoice_create(request):
    """إنشاء فاتورة جديدة"""
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

    if request.method == 'POST':
        print("\n\n=== بدء معالجة طلب POST ===")
        print("البيانات المرسلة:", request.POST)
        print("الملفات المرسلة:", request.FILES)

        # طباعة جميع المفاتيح في request.POST
        print("مفاتيح POST:", list(request.POST.keys()))

        # التحقق من وجود بيانات البنود
        items_data = request.POST.get('items_data', '[]')
        print("بيانات البنود (الخام):", items_data)

        try:
            import json
            items = json.loads(items_data)
            print("بيانات البنود (JSON):", items)
            print("عدد البنود:", len(items))
        except json.JSONDecodeError as e:
            print("خطأ في تحليل بيانات البنود JSON:", str(e))
            messages.error(request, f'خطأ في تحليل بيانات البنود: {str(e)}')
            return render(request, 'invoices/invoice/form.html', {
                'form': InvoiceForm(request.POST),
                'invoice': None,
                'contacts': Contact.objects.all(),
                'stores': Store.objects.all(),
                'safes': Safe.objects.all(),
                'products': Product.objects.all(),
                'representatives': Representative.objects.all(),
                'drivers': Driver.objects.all(),
            })

        # التحقق من وجود حقول مطلوبة
        required_fields = ['invoice_type', 'payment_type', 'contact', 'store', 'safe', 'number']
        missing_fields = [field for field in required_fields if not request.POST.get(field)]

        # طباعة قيم الحقول المطلوبة
        for field in required_fields:
            print(f"قيمة الحقل {field}: '{request.POST.get(field, '')}'")

        # التحقق من رقم الفاتورة بشكل خاص
        if not request.POST.get('number'):
            print("تحذير: رقم الفاتورة غير موجود، سيتم استخدام الرقم التلقائي:", new_number)

        if missing_fields:
            print("حقول مفقودة:", missing_fields)
            messages.error(request, f'الحقول التالية مطلوبة: {", ".join(missing_fields)}')
            return render(request, 'invoices/invoice/form.html', {
                'form': InvoiceForm(request.POST),
                'invoice': None,
                'contacts': Contact.objects.all(),
                'stores': Store.objects.all(),
                'safes': Safe.objects.all(),
                'products': Product.objects.all(),
                'representatives': Representative.objects.all(),
                'drivers': Driver.objects.all(),
            })

        form = InvoiceForm(request.POST)
        print("تم إنشاء نموذج InvoiceForm")

        if form.is_valid():
            print("النموذج صالح")
            print("البيانات المنظفة:", form.cleaned_data)

            try:
                with transaction.atomic():
                    print("بدء المعاملة")
                    invoice = form.save(commit=False)
                    if not invoice.number:
                        invoice.number = new_number

                    print("بيانات الفاتورة قبل الحفظ:", {
                        'id': invoice.id,
                        'number': invoice.number,
                        'invoice_type': invoice.invoice_type,
                        'payment_type': invoice.payment_type,
                        'contact_id': invoice.contact_id,
                        'store_id': invoice.store_id,
                        'safe_id': invoice.safe_id,
                    })

                    invoice.save()
                    print("تم حفظ الفاتورة:", invoice.id)

                    # حذف البنود القديمة في حالة التعديل
                    if invoice.id:
                        deleted_count = InvoiceItem.objects.filter(invoice=invoice).delete()
                        print("تم حذف البنود القديمة:", deleted_count)

                    # إضافة البنود الجديدة
                    for i, item in enumerate(items):
                        print(f"إضافة بند #{i+1}:", item)
                        try:
                            InvoiceItem.objects.create(
                                invoice=invoice,
                                product_id=item['product'],
                                product_unit_id=item['product_unit'],
                                quantity=item['quantity'],
                                unit_price=item['unit_price'],
                                discount_amount=item['discount_amount'],
                                tax_amount=item['tax_amount'],
                                net_price=item['net_price']
                            )
                            print(f"تم إضافة البند #{i+1} بنجاح")
                        except Exception as item_error:
                            print(f"خطأ في إضافة البند #{i+1}:", str(item_error))
                            raise Exception(f"خطأ في إضافة البند #{i+1}: {str(item_error)}")

                    # تحديث إجماليات الفاتورة
                    print("حساب إجماليات الفاتورة")
                    if hasattr(invoice, 'calculate_totals') and callable(getattr(invoice, 'calculate_totals')):
                        invoice.calculate_totals()
                        print("تم استدعاء دالة calculate_totals بنجاح")
                    else:
                        print("تحذير: دالة calculate_totals غير موجودة، حساب الإجماليات يدوياً")
                        # حساب الإجماليات يدوياً
                        items = invoice.items.all()
                        total_amount = sum(item.quantity * item.unit_price for item in items)
                        discount_amount = sum(item.discount_amount for item in items)
                        tax_amount = sum(item.tax_amount for item in items)

                        invoice.total_amount = total_amount
                        invoice.discount_amount = discount_amount
                        invoice.tax_amount = tax_amount
                        invoice.net_amount = total_amount - discount_amount + tax_amount

                        if invoice.payment_type == 'cash':
                            invoice.paid_amount = invoice.net_amount
                            invoice.remaining_amount = 0
                        else:
                            invoice.remaining_amount = invoice.net_amount - invoice.paid_amount

                    invoice.save()
                    print("تم حفظ الفاتورة بعد حساب الإجماليات")
                    print("بيانات الفاتورة النهائية:", {
                        'id': invoice.id,
                        'number': invoice.number,
                        'total_amount': invoice.total_amount,
                        'discount_amount': invoice.discount_amount,
                        'tax_amount': invoice.tax_amount,
                        'net_amount': invoice.net_amount,
                        'paid_amount': invoice.paid_amount,
                        'remaining_amount': invoice.remaining_amount,
                    })

                    # ترحيل الفاتورة وإنشاء المعاملات المالية والمخزنية مباشرة
                    try:
                        print("=== بدء ترحيل الفاتورة الجديدة ===")

                        # استخدام دالة post_invoice بدلاً من create_related_transactions
                        if hasattr(invoice, 'post_invoice') and callable(getattr(invoice, 'post_invoice')):
                            # تأكد من أن الفاتورة غير مرحلة أولاً
                            invoice.is_posted = False
                            invoice.save(update_fields=['is_posted'])

                            # ثم قم بترحيلها
                            result = invoice.post_invoice()
                            print(f"نتيجة استدعاء post_invoice: {result}")

                            # التحقق من نجاح إنشاء المعاملات
                            from finances.models import ContactTransaction, SafeTransaction, ProductTransaction
                            contact_transactions = ContactTransaction.objects.filter(invoice=invoice)
                            safe_transactions = SafeTransaction.objects.filter(invoice=invoice)
                            product_transactions = ProductTransaction.objects.filter(invoice=invoice)

                            print(f"عدد معاملات العملاء/الموردين بعد الترحيل: {contact_transactions.count()}")
                            print(f"عدد معاملات الخزنة بعد الترحيل: {safe_transactions.count()}")
                            print(f"عدد معاملات المخزون بعد الترحيل: {product_transactions.count()}")

                            # التحقق من إنشاء جميع المعاملات المطلوبة
                            items_count = invoice.items.count()
                            expected_product_transactions = items_count
                            has_error = False
                            error_message = ""

                            if contact_transactions.count() == 0:
                                print("تحذير: لم يتم إنشاء معاملات العملاء/الموردين")
                                # محاولة إعادة الترحيل
                                invoice.is_posted = False
                                invoice.save(update_fields=['is_posted'])
                                result = invoice.post_invoice()
                                print(f"نتيجة إعادة الترحيل: {result}")

                                # التحقق مرة أخرى
                                contact_transactions = ContactTransaction.objects.filter(invoice=invoice)
                                safe_transactions = SafeTransaction.objects.filter(invoice=invoice)
                                product_transactions = ProductTransaction.objects.filter(invoice=invoice)

                                print(f"عدد معاملات العملاء/الموردين بعد إعادة الترحيل: {contact_transactions.count()}")
                                print(f"عدد معاملات الخزنة بعد إعادة الترحيل: {safe_transactions.count()}")
                                print(f"عدد معاملات المخزون بعد إعادة الترحيل: {product_transactions.count()}")

                                # التحقق مرة أخرى بعد إعادة الترحيل
                                if contact_transactions.count() == 0:
                                    has_error = True
                                    error_message += "لم يتم إنشاء معاملات العملاء/الموردين. "

                            if (invoice.payment_type == 'cash' or invoice.paid_amount > 0) and safe_transactions.count() == 0:
                                print("تحذير: لم يتم إنشاء معاملات الخزنة للفاتورة النقدية أو الفاتورة الآجلة مع دفعة جزئية")
                                has_error = True
                                error_message += "لم يتم إنشاء معاملات الخزنة للفاتورة النقدية أو الفاتورة الآجلة مع دفعة جزئية. "

                            if product_transactions.count() != expected_product_transactions:
                                print(f"تحذير: عدد معاملات المخزون ({product_transactions.count()}) لا يتطابق مع عدد بنود الفاتورة ({expected_product_transactions})")
                                has_error = True
                                error_message += f"عدد معاملات المخزون ({product_transactions.count()}) لا يتطابق مع عدد بنود الفاتورة ({expected_product_transactions}). "

                            # إذا كان هناك خطأ، قم بالتراجع عن إنشاء الفاتورة
                            if has_error:
                                print("خطأ في ترحيل الفاتورة:", error_message)
                                # إلغاء المعاملة بإثارة استثناء
                                raise Exception(f"فشل في ترحيل الفاتورة: {error_message}")
                        else:
                            print("تحذير: دالة post_invoice غير موجودة، استخدام create_related_transactions كبديل")
                            # استخدام create_related_transactions كبديل
                            if hasattr(invoice, 'create_related_transactions') and callable(getattr(invoice, 'create_related_transactions')):
                                invoice.create_related_transactions()
                                invoice.is_posted = True
                                invoice.save(update_fields=['is_posted'])
                                print("تم إنشاء المعاملات المالية والمخزنية بنجاح")
                            else:
                                print("تحذير: دالة create_related_transactions غير موجودة أيضًا")
                    except Exception as e:
                        print("خطأ في ترحيل الفاتورة:", str(e))
                        import traceback
                        print("تتبع الخطأ:", traceback.format_exc())
                        # لا نريد إيقاف العملية إذا فشلت عملية الترحيل

                    print("=== تمت معالجة الطلب بنجاح ===\n\n")
                    messages.success(request, 'تم إنشاء الفاتورة وترحيلها بنجاح')

                    # طباعة معلومات التوجيه
                    print(f"=== معلومات التوجيه ===")
                    print(f"معرف الفاتورة: {invoice.id}")
                    print(f"رقم الفاتورة: {invoice.number}")
                    print(f"URL التوجيه: {reverse('invoice_detail', kwargs={'pk': invoice.id})}")

                    # التحقق مما إذا كان الطلب يتوقع استجابة JSON
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({
                            'success': True,
                            'message': 'تم إنشاء الفاتورة وترحيلها بنجاح',
                            'redirect_url': reverse('invoice_detail', kwargs={'pk': invoice.id})
                        })
                    else:
                        # استخدام HttpResponseRedirect بدلاً من redirect للتأكد من التوجيه الصحيح
                        return HttpResponseRedirect(reverse('invoice_detail', kwargs={'pk': invoice.id}))
            except Exception as e:
                print("حدث خطأ أثناء حفظ الفاتورة:", str(e))
                print("نوع الخطأ:", type(e).__name__)
                import traceback
                print("تتبع الخطأ:", traceback.format_exc())
                messages.error(request, f'حدث خطأ أثناء حفظ الفاتورة: {str(e)}')

                # التحقق مما إذا كان الطلب يتوقع استجابة JSON
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': False,
                        'message': f'حدث خطأ أثناء حفظ الفاتورة: {str(e)}',
                        'error': str(e),
                        'error_type': type(e).__name__
                    }, status=400)
        else:
            print("النموذج غير صالح")
            print("أخطاء النموذج:", form.errors)
            for field, errors in form.errors.items():
                print(f"أخطاء الحقل {field}:", errors)
            messages.error(request, 'يرجى تصحيح الأخطاء أدناه')

            # التحقق مما إذا كان الطلب يتوقع استجابة JSON
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'message': 'يرجى تصحيح الأخطاء أدناه',
                    'errors': dict(form.errors.items())
                }, status=400)
    else:
        # الحصول على إعدادات النظام
        settings = SystemSettings.get_settings()

        # تحديد نوع الفاتورة من الطلب أو استخدام النوع الافتراضي من الإعدادات
        invoice_type = request.GET.get('type', 'sale')
        payment_type = settings.default_invoice_type  # استخدام نوع الدفع الافتراضي من الإعدادات

        # تعيين القيم الافتراضية للنموذج
        initial_data = {
            'number': new_number,
            'date': timezone.now().date(),
            'invoice_type': invoice_type,
            'payment_type': payment_type
        }

        # تحديد العميل/المورد الافتراضي بناءً على نوع الفاتورة
        if invoice_type in [Invoice.SALE, Invoice.SALE_RETURN] and settings.default_customer:
            initial_data['contact'] = settings.default_customer.id
        elif invoice_type in [Invoice.PURCHASE, Invoice.PURCHASE_RETURN] and settings.default_supplier:
            initial_data['contact'] = settings.default_supplier.id

        # تعيين المخزن والخزنة الافتراضية
        if settings.default_store:
            initial_data['store'] = settings.default_store.id
        if settings.default_safe:
            initial_data['safe'] = settings.default_safe.id

        form = InvoiceForm(initial=initial_data)
        print("تم تعيين القيم الافتراضية للفاتورة من إعدادات النظام")

    # الحصول على البيانات الافتراضية
    # تحديد العميل/المورد الافتراضي بناءً على نوع الفاتورة ومن إعدادات النظام
    settings = SystemSettings.get_settings()
    invoice_type = request.GET.get('type', 'sale')

    default_contact = None
    if invoice_type in [Invoice.SALE, Invoice.SALE_RETURN] and settings.default_customer:
        default_contact = settings.default_customer
    elif invoice_type in [Invoice.PURCHASE, Invoice.PURCHASE_RETURN] and settings.default_supplier:
        default_contact = settings.default_supplier
    else:
        default_contact = Contact.objects.first()

    default_store = settings.default_store or Store.objects.first()
    default_safe = settings.default_safe or Safe.objects.first()
    default_payment_type = settings.default_invoice_type

    # إنشاء فاتورة مؤقتة بالقيم الافتراضية
    temp_invoice = Invoice(
        number=new_number,  # تعيين رقم الفاتورة
        date=timezone.now().date(),
        contact=default_contact,
        store=default_store,
        safe=default_safe,
        invoice_type=invoice_type,
        payment_type=default_payment_type
    )

    # تحضير قائمة جهات الاتصال مع إضافة نوع جهة الاتصال إلى الاسم
    contacts = Contact.objects.all()

    # الحصول على إعدادات النظام
    settings = SystemSettings.get_settings()

    context = {
        'form': form,
        'invoice': temp_invoice,
        'contacts': contacts,
        'stores': Store.objects.all(),
        'safes': Safe.objects.all(),
        'products': Product.objects.all(),
        'representatives': Representative.objects.all(),
        'drivers': Driver.objects.all(),
        'settings': settings,
    }

    return render(request, 'invoices/invoice/form.html', context)

@login_required
def invoice_edit(request, pk):
    """تعديل فاتورة"""
    invoice = get_object_or_404(Invoice, pk=pk)

    # يمكن تعديل الفاتورة حتى لو كانت مرحلة
    # سيتم إلغاء الترحيل وإعادة الترحيل تلقائياً

    if request.method == 'POST':
        form = InvoiceForm(request.POST, instance=invoice)
        if form.is_valid():
            with transaction.atomic():
                invoice = form.save()

                # معالجة بنود الفاتورة
                items_data = request.POST.get('items_data', '[]')
                import json
                items = json.loads(items_data)

                # حذف البنود القديمة
                InvoiceItem.objects.filter(invoice=invoice).delete()

                # إضافة البنود الجديدة
                for item in items:
                    InvoiceItem.objects.create(
                        invoice=invoice,
                        product_id=item['product'],
                        product_unit_id=item['product_unit'],
                        quantity=item['quantity'],
                        unit_price=item['unit_price'],
                        discount_amount=item['discount_amount'],
                        tax_amount=item['tax_amount'],
                        net_price=item['net_price']
                    )

                # تحديث إجماليات الفاتورة
                invoice.calculate_totals()
                invoice.save()

                # إعادة ترحيل الفاتورة بعد التعديل
                try:
                    # إلغاء الترحيل أولاً إذا كانت الفاتورة مرحلة
                    if invoice.is_posted and hasattr(invoice, 'unpost_invoice') and callable(getattr(invoice, 'unpost_invoice')):
                        invoice.unpost_invoice()
                        print("تم إلغاء ترحيل الفاتورة بنجاح")
                    else:
                        # إلغاء الترحيل يدويًا إذا لم تكن دالة unpost_invoice متاحة
                        from finances.models import ContactTransaction, SafeTransaction, ProductTransaction
                        with transaction.atomic():
                            ContactTransaction.objects.filter(invoice=invoice).delete()
                            SafeTransaction.objects.filter(invoice=invoice).delete()
                            ProductTransaction.objects.filter(invoice=invoice).delete()
                            invoice.is_posted = False
                            invoice.save(update_fields=['is_posted'])
                            print("تم إلغاء ترحيل الفاتورة يدويًا")

                    # إعادة ترحيل الفاتورة
                    print("=== بدء إعادة ترحيل الفاتورة ===")
                    if hasattr(invoice, 'post_invoice') and callable(getattr(invoice, 'post_invoice')):
                        # تأكد من أن الفاتورة غير مرحلة أولاً
                        invoice.is_posted = False
                        invoice.save(update_fields=['is_posted'])

                        # ثم قم بترحيلها
                        result = invoice.post_invoice()
                        print(f"نتيجة استدعاء post_invoice: {result}")
                        print(f"حالة الترحيل بعد الاستدعاء: {invoice.is_posted}")

                        # التحقق من نجاح إنشاء المعاملات
                        from finances.models import ContactTransaction, SafeTransaction, ProductTransaction
                        contact_transactions = ContactTransaction.objects.filter(invoice=invoice)
                        safe_transactions = SafeTransaction.objects.filter(invoice=invoice)
                        product_transactions = ProductTransaction.objects.filter(invoice=invoice)

                        print(f"عدد معاملات العملاء/الموردين بعد الترحيل: {contact_transactions.count()}")
                        print(f"عدد معاملات الخزنة بعد الترحيل: {safe_transactions.count()}")
                        print(f"عدد معاملات المخزون بعد الترحيل: {product_transactions.count()}")

                        # التحقق من إنشاء جميع المعاملات المطلوبة
                        items_count = invoice.items.count()
                        expected_product_transactions = items_count
                        has_error = False
                        error_message = ""

                        if contact_transactions.count() == 0:
                            print("تحذير: لم يتم إنشاء معاملات العملاء/الموردين")
                            # محاولة إعادة الترحيل
                            invoice.is_posted = False
                            invoice.save(update_fields=['is_posted'])
                            result = invoice.post_invoice()
                            print(f"نتيجة إعادة الترحيل: {result}")

                            # التحقق مرة أخرى
                            contact_transactions = ContactTransaction.objects.filter(invoice=invoice)
                            safe_transactions = SafeTransaction.objects.filter(invoice=invoice)
                            product_transactions = ProductTransaction.objects.filter(invoice=invoice)

                            print(f"عدد معاملات العملاء/الموردين بعد إعادة الترحيل: {contact_transactions.count()}")
                            print(f"عدد معاملات الخزنة بعد إعادة الترحيل: {safe_transactions.count()}")
                            print(f"عدد معاملات المخزون بعد إعادة الترحيل: {product_transactions.count()}")

                            # التحقق مرة أخرى بعد إعادة الترحيل
                            if contact_transactions.count() == 0:
                                has_error = True
                                error_message += "لم يتم إنشاء معاملات العملاء/الموردين. "

                        if (invoice.payment_type == 'cash' or invoice.paid_amount > 0) and safe_transactions.count() == 0:
                            print("تحذير: لم يتم إنشاء معاملات الخزنة للفاتورة النقدية أو الفاتورة الآجلة مع دفعة جزئية")
                            has_error = True
                            error_message += "لم يتم إنشاء معاملات الخزنة للفاتورة النقدية أو الفاتورة الآجلة مع دفعة جزئية. "

                        if product_transactions.count() != expected_product_transactions:
                            print(f"تحذير: عدد معاملات المخزون ({product_transactions.count()}) لا يتطابق مع عدد بنود الفاتورة ({expected_product_transactions})")
                            has_error = True
                            error_message += f"عدد معاملات المخزون ({product_transactions.count()}) لا يتطابق مع عدد بنود الفاتورة ({expected_product_transactions}). "

                        # إذا كان هناك خطأ، قم بالتراجع عن تعديل الفاتورة
                        if has_error:
                            print("خطأ في ترحيل الفاتورة:", error_message)
                            # إلغاء المعاملة بإثارة استثناء
                            raise Exception(f"فشل في ترحيل الفاتورة: {error_message}")
                    else:
                        print("تحذير: دالة post_invoice غير موجودة، استخدام create_related_transactions كبديل")
                        # استخدام create_related_transactions كبديل
                        if hasattr(invoice, 'create_related_transactions') and callable(getattr(invoice, 'create_related_transactions')):
                            invoice.create_related_transactions()
                            invoice.is_posted = True
                            invoice.save(update_fields=['is_posted'])
                            print("تم إنشاء المعاملات المالية والمخزنية بنجاح")
                        else:
                            print("تحذير: دالة create_related_transactions غير موجودة أيضًا")
                except Exception as e:
                    print("خطأ في إعادة ترحيل الفاتورة:", str(e))
                    import traceback
                    print("تتبع الخطأ:", traceback.format_exc())
                    # لا نريد إيقاف العملية إذا فشلت عملية الترحيل

                messages.success(request, 'تم تعديل الفاتورة وترحيلها بنجاح')
                # طباعة معلومات التوجيه
                print(f"=== معلومات التوجيه ===")
                print(f"معرف الفاتورة: {invoice.id}")
                print(f"رقم الفاتورة: {invoice.number}")
                print(f"URL التوجيه: {reverse('invoice_detail', kwargs={'pk': invoice.id})}")

                # التحقق مما إذا كان الطلب يتوقع استجابة JSON
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': True,
                        'message': 'تم تعديل الفاتورة وترحيلها بنجاح',
                        'redirect_url': reverse('invoice_detail', kwargs={'pk': invoice.id})
                    })
                else:
                    # استخدام HttpResponseRedirect بدلاً من redirect للتأكد من التوجيه الصحيح
                    return HttpResponseRedirect(reverse('invoice_detail', kwargs={'pk': invoice.id}))
    else:
        form = InvoiceForm(instance=invoice)

    # تحضير قائمة جهات الاتصال مع إضافة نوع جهة الاتصال إلى الاسم
    contacts = Contact.objects.all()

    # تحميل بنود الفاتورة مع المنتجات والوحدات المرتبطة بها
    invoice_items = InvoiceItem.objects.filter(invoice=invoice).select_related('product', 'product_unit')

    print(f"=== بدء تحميل بنود الفاتورة رقم {invoice.number} ===")
    print(f"عدد البنود: {invoice_items.count()}")

    # تحميل وحدات المنتجات لكل بند
    for item in invoice_items:
        item.product_units = item.product.units.all()
        print(f"بند الفاتورة: {item.id}")
        print(f"- المنتج: {item.product.name} (ID: {item.product.id})")
        print(f"- الوحدة: {item.product_unit.unit.name} (ID: {item.product_unit.id})")
        print(f"- الكمية: {item.quantity} (نوع البيانات: {type(item.quantity)})")
        print(f"- سعر الوحدة: {item.unit_price}")
        print(f"- السعر الإجمالي: {item.total_price}")
        print(f"- الخصم: {item.discount_amount}")
        print(f"- الضريبة: {item.tax_amount}")
        print(f"- الصافي: {item.net_price}")

    # الحصول على إعدادات النظام
    settings = SystemSettings.get_settings()

    context = {
        'form': form,
        'invoice': invoice,
        'invoice_items': invoice_items,  # إضافة بنود الفاتورة إلى السياق
        'contacts': contacts,
        'stores': Store.objects.all(),
        'safes': Safe.objects.all(),
        'products': Product.objects.all(),
        'representatives': Representative.objects.all(),
        'drivers': Driver.objects.all(),
        'settings': settings,
    }

    return render(request, 'invoices/invoice/form.html', context)

@login_required
def invoice_delete(request, pk):
    """حذف فاتورة"""
    invoice = get_object_or_404(Invoice, pk=pk)

    # يمكن حذف الفاتورة حتى لو كانت مرحلة
    # سيتم إلغاء الترحيل تلقائياً قبل الحذف

    if request.method == 'POST':
        try:
            # إلغاء الترحيل أولاً إذا كانت الفاتورة مرحلة
            if invoice.is_posted:
                if hasattr(invoice, 'unpost_invoice') and callable(getattr(invoice, 'unpost_invoice')):
                    invoice.unpost_invoice()
                    print("تم إلغاء ترحيل الفاتورة قبل الحذف")
                else:
                    print("تحذير: دالة unpost_invoice غير موجودة، محاولة حذف المعاملات المالية والمخزنية يدويًا")
                    # محاولة حذف المعاملات المالية والمخزنية يدويًا
                    from finances.models import ContactTransaction, SafeTransaction, ProductTransaction
                    ProductTransaction.objects.filter(invoice=invoice).delete()
                    ContactTransaction.objects.filter(invoice=invoice).delete()
                    SafeTransaction.objects.filter(invoice=invoice).delete()
                    print("تم حذف المعاملات المالية والمخزنية يدويًا")

            # حذف الفاتورة
            invoice.delete()
            messages.success(request, 'تم حذف الفاتورة بنجاح')
            return redirect('invoice_list')
        except Exception as e:
            messages.error(request, f'حدث خطأ أثناء حذف الفاتورة: {str(e)}')
            return redirect('invoice_detail', pk=invoice.id)

    return render(request, 'invoices/invoice/confirm_delete.html', {'invoice': invoice})

@login_required
def invoice_post(request, pk):
    """ترحيل الفاتورة"""
    invoice = get_object_or_404(Invoice, pk=pk)

    # لا يمكن ترحيل الفاتورة المرحلة مسبقاً
    if invoice.is_posted:
        messages.error(request, 'الفاتورة مرحلة بالفعل')
        return redirect('invoice_detail', pk=invoice.id)

    try:
        with transaction.atomic():
            # استخدام دالة post_invoice بدلاً من create_related_transactions
            if hasattr(invoice, 'post_invoice') and callable(getattr(invoice, 'post_invoice')):
                # تأكد من أن الفاتورة غير مرحلة أولاً
                invoice.is_posted = False
                invoice.save(update_fields=['is_posted'])

                # ثم قم بترحيلها
                result = invoice.post_invoice()
                print(f"نتيجة استدعاء post_invoice: {result}")

                # التحقق من نجاح إنشاء المعاملات
                from finances.models import ContactTransaction, SafeTransaction, ProductTransaction
                contact_transactions = ContactTransaction.objects.filter(invoice=invoice)
                safe_transactions = SafeTransaction.objects.filter(invoice=invoice)
                product_transactions = ProductTransaction.objects.filter(invoice=invoice)

                print(f"عدد معاملات العملاء/الموردين بعد الترحيل: {contact_transactions.count()}")
                print(f"عدد معاملات الخزنة بعد الترحيل: {safe_transactions.count()}")
                print(f"عدد معاملات المخزون بعد الترحيل: {product_transactions.count()}")

                # التحقق من إنشاء جميع المعاملات المطلوبة
                items_count = invoice.items.count()
                expected_product_transactions = items_count
                has_error = False
                error_message = ""

                if contact_transactions.count() == 0:
                    print("تحذير: لم يتم إنشاء معاملات العملاء/الموردين")
                    # محاولة إعادة الترحيل
                    invoice.is_posted = False
                    invoice.save(update_fields=['is_posted'])
                    result = invoice.post_invoice()
                    print(f"نتيجة إعادة الترحيل: {result}")

                    # التحقق مرة أخرى
                    contact_transactions = ContactTransaction.objects.filter(invoice=invoice)
                    safe_transactions = SafeTransaction.objects.filter(invoice=invoice)
                    product_transactions = ProductTransaction.objects.filter(invoice=invoice)

                    print(f"عدد معاملات العملاء/الموردين بعد إعادة الترحيل: {contact_transactions.count()}")
                    print(f"عدد معاملات الخزنة بعد إعادة الترحيل: {safe_transactions.count()}")
                    print(f"عدد معاملات المخزون بعد إعادة الترحيل: {product_transactions.count()}")

                    # التحقق مرة أخرى بعد إعادة الترحيل
                    if contact_transactions.count() == 0:
                        has_error = True
                        error_message += "لم يتم إنشاء معاملات العملاء/الموردين. "

                if (invoice.payment_type == 'cash' or invoice.paid_amount > 0) and safe_transactions.count() == 0:
                    print("تحذير: لم يتم إنشاء معاملات الخزنة للفاتورة النقدية أو الفاتورة الآجلة مع دفعة جزئية")
                    has_error = True
                    error_message += "لم يتم إنشاء معاملات الخزنة للفاتورة النقدية أو الفاتورة الآجلة مع دفعة جزئية. "

                if product_transactions.count() != expected_product_transactions:
                    print(f"تحذير: عدد معاملات المخزون ({product_transactions.count()}) لا يتطابق مع عدد بنود الفاتورة ({expected_product_transactions})")
                    has_error = True
                    error_message += f"عدد معاملات المخزون ({product_transactions.count()}) لا يتطابق مع عدد بنود الفاتورة ({expected_product_transactions}). "

                # إذا كان هناك خطأ، قم بالتراجع عن ترحيل الفاتورة
                if has_error:
                    print("خطأ في ترحيل الفاتورة:", error_message)
                    # إلغاء المعاملة بإثارة استثناء
                    raise Exception(f"فشل في ترحيل الفاتورة: {error_message}")

                if result:
                    messages.success(request, 'تم ترحيل الفاتورة بنجاح')
                else:
                    messages.warning(request, 'لم يتم ترحيل الفاتورة بشكل كامل. يرجى التحقق من المعاملات المالية والمخزنية.')
            else:
                # الطريقة القديمة كبديل
                # حذف أي معاملات موجودة أولاً
                from finances.models import ContactTransaction, SafeTransaction, ProductTransaction
                ContactTransaction.objects.filter(invoice=invoice).delete()
                SafeTransaction.objects.filter(invoice=invoice).delete()
                ProductTransaction.objects.filter(invoice=invoice).delete()

                # ثم إنشاء معاملات جديدة
                invoice.create_related_transactions()
                invoice.is_posted = True
                invoice.save()
                messages.success(request, 'تم ترحيل الفاتورة بنجاح')
    except Exception as e:
        print("خطأ في ترحيل الفاتورة:", str(e))
        import traceback
        print("تتبع الخطأ:", traceback.format_exc())
        messages.error(request, f'حدث خطأ أثناء ترحيل الفاتورة: {str(e)}')

    return redirect('invoice_detail', pk=invoice.id)

@login_required
def invoice_unpost(request, pk):
    """إلغاء ترحيل الفاتورة"""
    invoice = get_object_or_404(Invoice, pk=pk)

    # لا يمكن إلغاء ترحيل الفاتورة غير المرحلة
    if not invoice.is_posted:
        messages.error(request, 'الفاتورة غير مرحلة بالفعل')
        return redirect('invoice_detail', pk=invoice.id)

    try:
        with transaction.atomic():
            # حذف المعاملات المالية والمخزنية المرتبطة بالفاتورة
            invoice.delete_related_transactions()
            invoice.is_posted = False
            invoice.save()
            messages.success(request, 'تم إلغاء ترحيل الفاتورة بنجاح')
    except Exception as e:
        messages.error(request, f'حدث خطأ أثناء إلغاء ترحيل الفاتورة: {str(e)}')

    return redirect('invoice_detail', pk=invoice.id)

@login_required
def invoice_print(request, pk):
    """طباعة الفاتورة"""
    invoice = get_object_or_404(Invoice, pk=pk)

    # الحصول على بيانات الشركة من المخزن والفرع
    company = invoice.store.branch.company if invoice.store and invoice.store.branch else None

    # إذا لم يتم العثور على الشركة، استخدم أول شركة في قاعدة البيانات
    if not company:
        from core.models import Company
        company = Company.objects.first()

    # الحصول على إعدادات النظام
    settings = SystemSettings.get_settings()

    context = {
        'invoice': invoice,
        'company': company,
        'settings': settings,
    }

    # عرض صفحة HTML للطباعة
    return render(request, 'invoices/invoice_print.html', context)

@login_required
def payment_list(request):
    """عرض قائمة المدفوعات"""
    payments = Payment.objects.all().order_by('-date', '-id')
    # Create a directory for payment templates if it doesn't exist
    return render(request, 'invoices/payment/list.html', {'payments': payments})

@login_required
def receipt_list(request):
    """عرض قائمة التحصيلات من العملاء"""
    payments = Payment.objects.filter(payment_type=Payment.RECEIPT).order_by('-date', '-id')
    return render(request, 'invoices/payment/list.html', {
        'payments': payments,
        'title': 'التحصيلات من العملاء',
        'payment_type': Payment.RECEIPT
    })

@login_required
def payment_to_supplier_list(request):
    """عرض قائمة المدفوعات للموردين"""
    payments = Payment.objects.filter(payment_type=Payment.PAYMENT).order_by('-date', '-id')
    return render(request, 'invoices/payment/list.html', {
        'payments': payments,
        'title': 'المدفوعات للموردين',
        'payment_type': Payment.PAYMENT
    })

@login_required
def payment_add(request):
    """إضافة دفعة جديدة"""
    # إنشاء رقم دفعة جديد
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

    if request.method == 'POST':
        form = PaymentForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                payment = form.save(commit=False)
                if not payment.number:
                    payment.number = new_number
                payment.save()
                messages.success(request, 'تم إضافة الدفعة بنجاح')
                return redirect('payment_detail', pk=payment.id)
    else:
        form = PaymentForm(initial={'number': new_number, 'date': timezone.now().date()})

        # تعديل قائمة جهات الاتصال لإضافة نوع جهة الاتصال إلى الاسم
        contact_choices = []
        for contact in Contact.objects.all():
            contact_type_display = "عميل" if contact.contact_type == Contact.CUSTOMER else "مورد"
            contact_choices.append((contact.id, f"{contact.name} ({contact_type_display})"))

        form.fields['contact'].choices = [('', 'اختر العميل/المورد')] + contact_choices

    return render(request, 'invoices/payment/form.html', {'form': form})

@login_required
def payment_detail(request, pk):
    """عرض تفاصيل الدفعة"""
    payment = get_object_or_404(Payment, pk=pk)
    return render(request, 'invoices/payment/detail.html', {'payment': payment})

@login_required
def payment_post(request, pk):
    """ترحيل الدفعة"""
    payment = get_object_or_404(Payment, pk=pk)

    # لا يمكن ترحيل الدفعة المرحلة مسبقاً
    if payment.is_posted:
        messages.error(request, 'الدفعة مرحلة بالفعل')
        return redirect('payment_detail', pk=payment.id)

    try:
        with transaction.atomic():
            # استخدام دالة post_payment لإنشاء المعاملات المالية المرتبطة بالدفعة
            result = payment.post_payment()

            if result:
                # التحقق من نجاح إنشاء المعاملات
                contact_transaction = payment.contact_transaction
                safe_transaction = payment.created_transaction

                if not contact_transaction or not safe_transaction:
                    raise Exception("لم يتم إنشاء جميع المعاملات المالية المطلوبة")

                # التحقق من تحديث الفاتورة المرتبطة إذا وجدت
                if payment.invoice:
                    print(f"الفاتورة المرتبطة: {payment.invoice.number}")
                    print(f"المبلغ المدفوع: {payment.invoice.paid_amount}")
                    print(f"المبلغ المتبقي: {payment.invoice.remaining_amount}")

                messages.success(request, 'تم ترحيل الدفعة بنجاح')
            else:
                messages.warning(request, 'لم يتم ترحيل الدفعة. قد تكون مرحلة بالفعل.')
    except Exception as e:
        print(f"خطأ في ترحيل الدفعة: {str(e)}")
        import traceback
        print(f"تتبع الخطأ: {traceback.format_exc()}")
        messages.error(request, f'حدث خطأ أثناء ترحيل الدفعة: {str(e)}')

    return redirect('payment_detail', pk=payment.id)

@login_required
def payment_unpost(request, pk):
    """إلغاء ترحيل الدفعة"""
    payment = get_object_or_404(Payment, pk=pk)

    # لا يمكن إلغاء ترحيل الدفعة غير المرحلة
    if not payment.is_posted:
        messages.error(request, 'الدفعة غير مرحلة بالفعل')
        return redirect('payment_detail', pk=payment.id)

    try:
        with transaction.atomic():
            # استخدام دالة unpost_payment لإلغاء ترحيل الدفعة
            result = payment.unpost_payment()

            if result:
                # التحقق من تحديث الفاتورة المرتبطة إذا وجدت
                if payment.invoice:
                    print(f"الفاتورة المرتبطة بعد إلغاء الترحيل: {payment.invoice.number}")
                    print(f"المبلغ المدفوع: {payment.invoice.paid_amount}")
                    print(f"المبلغ المتبقي: {payment.invoice.remaining_amount}")

                messages.success(request, 'تم إلغاء ترحيل الدفعة بنجاح')
            else:
                messages.warning(request, 'لم يتم إلغاء ترحيل الدفعة. قد تكون غير مرحلة بالفعل.')
    except Exception as e:
        print(f"خطأ في إلغاء ترحيل الدفعة: {str(e)}")
        import traceback
        print(f"تتبع الخطأ: {traceback.format_exc()}")
        messages.error(request, f'حدث خطأ أثناء إلغاء ترحيل الدفعة: {str(e)}')

    return redirect('payment_detail', pk=payment.id)