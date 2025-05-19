from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.db.models import Q, Sum
from django.utils import timezone

from ..models import ProductTransaction
from ..forms import ProductTransactionForm
from core.models import Store
from products.models import Product, ProductUnit, Category

@login_required
def product_transaction_list(request):
    """عرض قائمة حركات المنتجات"""
    transactions = ProductTransaction.objects.all().order_by('-date')

    # تصفية حسب المنتج
    product_id = request.GET.get('product')
    if product_id:
        transactions = transactions.filter(product_id=product_id)

    # تصفية حسب المخزن
    store_id = request.GET.get('store')
    if store_id:
        transactions = transactions.filter(store_id=store_id)

    # تصفية حسب نوع الحركة
    transaction_type = request.GET.get('transaction_type')
    if transaction_type:
        transactions = transactions.filter(transaction_type=transaction_type)

    # تصفية حسب التاريخ
    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')

    if from_date:
        try:
            from_date_obj = timezone.datetime.strptime(from_date, '%Y-%m-%d').replace(hour=0, minute=0, second=0)
            transactions = transactions.filter(date__gte=from_date_obj)
        except ValueError:
            messages.error(request, 'تنسيق تاريخ البداية غير صحيح. يرجى استخدام التنسيق YYYY-MM-DD')
            from_date = None

    if to_date:
        try:
            to_date_obj = timezone.datetime.strptime(to_date, '%Y-%m-%d').replace(hour=23, minute=59, second=59)
            transactions = transactions.filter(date__lte=to_date_obj)
        except ValueError:
            messages.error(request, 'تنسيق تاريخ النهاية غير صحيح. يرجى استخدام التنسيق YYYY-MM-DD')
            to_date = None

    # البحث
    search_query = request.GET.get('q')
    if search_query:
        transactions = transactions.filter(
            Q(product__name__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(reference_number__icontains=search_query) |
            Q(store__name__icontains=search_query)
        )

    # قوائم للتصفية
    products = Product.objects.all()
    stores = Store.objects.all()

    return render(request, 'finances/product_transaction/list.html', {
        'transactions': transactions,
        'products': products,
        'stores': stores,
        'transaction_types': ProductTransaction.TRANSACTION_TYPE_CHOICES,
        'selected_product': product_id,
        'selected_store': store_id,
        'selected_type': transaction_type,
        'from_date': from_date,
        'to_date': to_date,
        'search_query': search_query
    })

@login_required
def product_transaction_add(request):
    """إضافة حركة منتج جديدة"""
    if request.method == 'POST':
        form = ProductTransactionForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                # حساب الكمية بالوحدة الأساسية
                product = form.cleaned_data['product']
                product_unit = form.cleaned_data['product_unit']
                quantity = form.cleaned_data['quantity']
                transaction_type = form.cleaned_data['transaction_type']

                base_quantity = quantity * product_unit.conversion_factor

                # الحصول على الرصيد الحالي للمنتج
                current_balance = product.current_balance

                # حساب الرصيد بعد العملية
                if transaction_type in [ProductTransaction.PURCHASE, ProductTransaction.INVENTORY_ADDITION, ProductTransaction.PURCHASE_RETURN_INVOICE]:
                    # حركات تزيد الرصيد
                    balance_after = current_balance + base_quantity
                else:
                    # حركات تنقص الرصيد
                    balance_after = current_balance - base_quantity

                # إنشاء الحركة
                transaction = form.save(commit=False)
                transaction.base_quantity = base_quantity
                transaction.balance_before = current_balance
                transaction.balance_after = balance_after
                transaction.save()

                # تحديث رصيد المنتج
                product.current_balance = balance_after
                product.save()

                messages.success(request, 'تم إضافة حركة المنتج بنجاح')
                return redirect('product_transaction_list')
    else:
        form = ProductTransactionForm()

    return render(request, 'finances/product_transaction/form.html', {
        'form': form,
        'title': 'إضافة حركة منتج جديدة'
    })

@login_required
def product_transaction_detail(request, pk):
    """عرض تفاصيل حركة منتج"""
    transaction = get_object_or_404(ProductTransaction, pk=pk)

    return render(request, 'finances/product_transaction/detail.html', {
        'transaction': transaction
    })

@login_required
def product_transaction_edit(request, pk):
    """تعديل حركة منتج"""
    transaction_obj = get_object_or_404(ProductTransaction, pk=pk)

    if request.method == 'POST':
        form = ProductTransactionForm(request.POST, instance=transaction_obj)
        if form.is_valid():
            with transaction.atomic():
                # حساب الكمية بالوحدة الأساسية
                product = form.cleaned_data['product']
                product_unit = form.cleaned_data['product_unit']
                quantity = form.cleaned_data['quantity']
                transaction_type = form.cleaned_data['transaction_type']

                base_quantity = quantity * product_unit.conversion_factor

                # الحصول على الرصيد الحالي للمنتج
                current_balance = product.current_balance

                # حساب الرصيد بعد العملية
                if transaction_type in [ProductTransaction.PURCHASE, ProductTransaction.INVENTORY_ADDITION, ProductTransaction.PURCHASE_RETURN_INVOICE]:
                    # حركات تزيد الرصيد
                    balance_after = current_balance + base_quantity
                else:
                    # حركات تنقص الرصيد
                    balance_after = current_balance - base_quantity

                # تحديث الحركة
                transaction_obj = form.save(commit=False)
                transaction_obj.base_quantity = base_quantity
                transaction_obj.balance_before = current_balance
                transaction_obj.balance_after = balance_after
                transaction_obj.save()

                # تحديث رصيد المنتج
                product.current_balance = balance_after
                product.save()

                messages.success(request, 'تم تعديل حركة المنتج بنجاح')
                return redirect('product_transaction_list')
    else:
        form = ProductTransactionForm(instance=transaction_obj)

    return render(request, 'finances/product_transaction/form.html', {
        'form': form,
        'title': 'تعديل حركة منتج'
    })

@login_required
def product_transaction_post(request, pk):
    """ترحيل حركة منتج"""
    transaction_obj = get_object_or_404(ProductTransaction, pk=pk)

    # تنفيذ عملية الترحيل
    # (يمكن إضافة المنطق الخاص بالترحيل هنا)

    messages.success(request, 'تم ترحيل حركة المنتج بنجاح')
    return redirect('product_transaction_detail', pk=pk)

@login_required
def product_transaction_unpost(request, pk):
    """إلغاء ترحيل حركة منتج"""
    transaction_obj = get_object_or_404(ProductTransaction, pk=pk)

    # تنفيذ عملية إلغاء الترحيل
    # (يمكن إضافة المنطق الخاص بإلغاء الترحيل هنا)

    messages.success(request, 'تم إلغاء ترحيل حركة المنتج بنجاح')
    return redirect('product_transaction_detail', pk=pk)

@login_required
def product_movement_report(request, product_id):
    """عرض تقرير حركة منتج محدد"""
    product = get_object_or_404(Product, pk=product_id)

    # الحصول على جميع حركات المنتج
    movements = ProductTransaction.objects.filter(product=product).order_by('-date')

    # تصفية حسب المخزن
    store_id = request.GET.get('store')
    if store_id:
        movements = movements.filter(store_id=store_id)

    # تصفية حسب نوع الحركة
    transaction_type = request.GET.get('transaction_type')
    if transaction_type:
        movements = movements.filter(transaction_type=transaction_type)

    # تصفية حسب التاريخ
    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')

    if from_date:
        try:
            from_date_obj = timezone.datetime.strptime(from_date, '%Y-%m-%d').replace(hour=0, minute=0, second=0)
            movements = movements.filter(date__gte=from_date_obj)
        except ValueError:
            messages.error(request, 'تنسيق تاريخ البداية غير صحيح. يرجى استخدام التنسيق YYYY-MM-DD')
            from_date = None

    if to_date:
        try:
            to_date_obj = timezone.datetime.strptime(to_date, '%Y-%m-%d').replace(hour=23, minute=59, second=59)
            movements = movements.filter(date__lte=to_date_obj)
        except ValueError:
            messages.error(request, 'تنسيق تاريخ النهاية غير صحيح. يرجى استخدام التنسيق YYYY-MM-DD')
            to_date = None

    # قوائم للتصفية
    stores = Store.objects.all()

    return render(request, 'finances/product_transaction/movement_report.html', {
        'product': product,
        'movements': movements,
        'stores': stores,
        'transaction_types': ProductTransaction.TRANSACTION_TYPE_CHOICES,
        'selected_store': store_id,
        'selected_type': transaction_type,
        'from_date': from_date,
        'to_date': to_date
    })

@login_required
def product_transaction_delete(request, pk):
    """حذف حركة منتج"""
    transaction = get_object_or_404(ProductTransaction, pk=pk)

    if request.method == 'POST':
        with transaction.atomic():
            # الحصول على المنتج
            product = transaction.product

            # حذف الحركة
            transaction.delete()

            # إعادة حساب أرصدة المنتج
            ProductTransaction.recalculate_balances(product)

            messages.success(request, 'تم حذف حركة المنتج بنجاح')
            return redirect('product_transaction_list')

    return render(request, 'finances/product_transaction/delete.html', {
        'transaction': transaction
    })

@login_required
def product_inventory(request):
    """عرض تقرير المخزون الحالي"""
    products = Product.objects.all().order_by('name')

    # تصفية حسب التصنيف
    category_id = request.GET.get('category')
    if category_id:
        products = products.filter(category_id=category_id)

    # تصفية حسب المخزن
    store_id = request.GET.get('store')

    # البحث
    search_query = request.GET.get('q')
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) |
            Q(code__icontains=search_query) |
            Q(barcode__icontains=search_query)
        )

    # الحصول على حركات المنتجات حسب المخزن إذا تم تحديده
    product_movements = {}
    if store_id:
        for product in products:
            # الحصول على آخر حركة للمنتج في المخزن المحدد
            last_movement = ProductTransaction.objects.filter(
                product=product,
                store_id=store_id
            ).order_by('-date').first()

            if last_movement:
                product_movements[product.id] = {
                    'store_balance': last_movement.balance_after,
                    'last_movement_date': last_movement.date
                }
            else:
                product_movements[product.id] = {
                    'store_balance': 0,
                    'last_movement_date': None
                }

    # قوائم للتصفية
    categories = Category.objects.all()
    stores = Store.objects.all()

    return render(request, 'finances/product_transaction/inventory.html', {
        'products': products,
        'categories': categories,
        'stores': stores,
        'selected_category': category_id,
        'selected_store': store_id,
        'search_query': search_query,
        'product_movements': product_movements
    })
