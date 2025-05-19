from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Sum
from django.http import HttpResponse, JsonResponse
from django.template.loader import get_template
from django.conf import settings
import os
import io
import xlsxwriter
from datetime import datetime
import arabic_reshaper
from bidi.algorithm import get_display
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
# لا نحتاج إلى استيراد pdfmetrics و TTFont لأننا نستخدم الخطوط المدمجة
from .models import (
    BatchName, BatchEntry, BatchIncubation, BatchHatching,
    Customer, CulledSale, DisinfectantCategory, DisinfectantInventory,
    DisinfectantTransaction, BatchDistribution, BatchDistributionItem
)
from .forms import (
    BatchNameForm, BatchEntryForm, BatchIncubationForm, BatchHatchingForm,
    CustomerForm, CulledSaleForm, DisinfectantCategoryForm,
    DisinfectantInventoryForm, DisinfectantTransactionForm,
    BatchDistributionForm, BatchDistributionItemForm, BatchDistributionItemFormSet
)

@login_required
def home(request):
    """الصفحة الرئيسية لتطبيق المفرخة"""
    # إحصائيات عامة
    batch_count = BatchEntry.objects.count()
    incubation_count = BatchIncubation.objects.count()
    hatching_count = BatchHatching.objects.count()
    sales_count = CulledSale.objects.count()

    # الدفعات الجاهزة للخروج (تاريخ الخروج المتوقع هو اليوم أو قبله)
    today = timezone.now().date()
    ready_to_hatch = BatchIncubation.objects.filter(
        expected_hatch_date__lte=today
    ).exclude(
        hatching__isnull=False  # استبعاد الدفعات التي خرجت بالفعل
    ).order_by('expected_hatch_date')[:5]

    context = {
        'batch_count': batch_count,
        'incubation_count': incubation_count,
        'hatching_count': hatching_count,
        'sales_count': sales_count,
        'ready_to_hatch': ready_to_hatch,
    }

    return render(request, 'hatchery/home.html', context)

# Create your views here.

# BatchName views
@login_required
def batch_name_list(request):
    """عرض قائمة أسماء الدفعات"""
    batch_names = BatchName.objects.all().order_by('name')
    return render(request, 'hatchery/batch_name_list.html', {'batch_names': batch_names})

@login_required
def batch_name_create(request):
    """إنشاء اسم دفعة جديد"""
    if request.method == 'POST':
        form = BatchNameForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'تم إنشاء اسم الدفعة بنجاح')
            return redirect('hatchery:batch_name_list')
    else:
        form = BatchNameForm()

    return render(request, 'hatchery/batch_name_form.html', {'form': form})

@login_required
def batch_name_update(request, pk):
    """تعديل اسم دفعة"""
    batch_name = get_object_or_404(BatchName, pk=pk)

    if request.method == 'POST':
        form = BatchNameForm(request.POST, instance=batch_name)
        if form.is_valid():
            form.save()
            messages.success(request, 'تم تحديث اسم الدفعة بنجاح')
            return redirect('hatchery:batch_name_list')
    else:
        form = BatchNameForm(instance=batch_name)

    return render(request, 'hatchery/batch_name_form.html', {'form': form})

@login_required
def batch_name_delete(request, pk):
    """حذف اسم دفعة"""
    batch_name = get_object_or_404(BatchName, pk=pk)

    if request.method == 'POST':
        try:
            batch_name.delete()
            messages.success(request, 'تم حذف اسم الدفعة بنجاح')
        except Exception as e:
            messages.error(request, f'لا يمكن حذف اسم الدفعة: {str(e)}')
        return redirect('hatchery:batch_name_list')

    return render(request, 'hatchery/batch_name_confirm_delete.html', {'batch_name': batch_name})

# Placeholder views for hatchery app
# These will be implemented with actual functionality later

@login_required
def batch_list(request):
    """عرض قائمة الدفعات الواردة"""
    batches = BatchEntry.objects.all().order_by('-date')
    return render(request, 'hatchery/batch_list.html', {'batches': batches})

@login_required
def batch_create(request):
    """إنشاء دفعة جديدة"""
    if request.method == 'POST':
        form = BatchEntryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'تم إنشاء الدفعة بنجاح')
            return redirect('hatchery:batch_list')
    else:
        form = BatchEntryForm()

    return render(request, 'hatchery/batch_form.html', {'form': form})

@login_required
def batch_detail(request, pk):
    """عرض تفاصيل دفعة"""
    batch = get_object_or_404(BatchEntry, pk=pk)
    return render(request, 'hatchery/batch_detail.html', {'batch': batch})

@login_required
def batch_update(request, pk):
    """تحديث بيانات دفعة"""
    batch = get_object_or_404(BatchEntry, pk=pk)

    if request.method == 'POST':
        form = BatchEntryForm(request.POST, instance=batch)
        if form.is_valid():
            form.save()
            messages.success(request, 'تم تحديث بيانات الدفعة بنجاح')
            return redirect('hatchery:batch_detail', pk=pk)
    else:
        form = BatchEntryForm(instance=batch)

    return render(request, 'hatchery/batch_form.html', {'form': form})

@login_required
def batch_delete(request, pk):
    """حذف دفعة"""
    # Placeholder - will be implemented later
    messages.success(request, 'تم حذف الدفعة بنجاح')
    return redirect('hatchery:batch_list')

@login_required
def incubation_list(request):
    """عرض قائمة تسكين الدفعات"""
    incubations = BatchIncubation.objects.all().order_by('-incubation_date')

    # الحصول على الدفعات المتاحة للتسكين
    # نحصل على الدفعات التي لم يتم تسكينها بعد

    # أولاً، نحصل على قائمة الدفعات التي تم تسكينها بالفعل
    incubated_batch_ids = BatchIncubation.objects.values_list('batch_entry_id', flat=True)

    # ثم نحصل على الدفعات النشطة التي لم يتم تسكينها بعد
    available_batches = BatchEntry.objects.filter(
        batch_name__is_active=True  # الدفعات النشطة فقط
    ).exclude(
        id__in=incubated_batch_ids  # استبعاد الدفعات التي تم تسكينها بالفعل
    ).order_by('-date')

    return render(request, 'hatchery/incubation_list.html', {
        'incubations': incubations,
        'available_batches': available_batches
    })

@login_required
def incubation_create(request, batch_id):
    """إنشاء تسكين جديد لدفعة"""
    batch = get_object_or_404(BatchEntry, pk=batch_id)

    if request.method == 'POST':
        form = BatchIncubationForm(request.POST, batch_id=batch_id)
        if form.is_valid():
            form.save()
            messages.success(request, 'تم تسجيل تسكين الدفعة بنجاح')
            return redirect('hatchery:incubation_list')
    else:
        form = BatchIncubationForm(batch_id=batch_id)

    return render(request, 'hatchery/incubation_form.html', {'form': form, 'batch': batch})

@login_required
def incubation_detail(request, pk):
    """عرض تفاصيل تسكين"""
    incubation = get_object_or_404(BatchIncubation, pk=pk)
    return render(request, 'hatchery/incubation_detail.html', {'incubation': incubation})

@login_required
def incubation_update(request, pk):
    """تحديث بيانات تسكين"""
    incubation = get_object_or_404(BatchIncubation, pk=pk)

    if request.method == 'POST':
        form = BatchIncubationForm(request.POST, instance=incubation, batch_id=incubation.batch_entry.id)
        if form.is_valid():
            form.save()
            messages.success(request, 'تم تحديث بيانات التسكين بنجاح')
            return redirect('hatchery:incubation_detail', pk=pk)
    else:
        form = BatchIncubationForm(instance=incubation, batch_id=incubation.batch_entry.id)

    return render(request, 'hatchery/incubation_form.html', {'form': form})

@login_required
def incubation_delete(request, pk):
    """حذف تسكين"""
    incubation = get_object_or_404(BatchIncubation, pk=pk)

    if request.method == 'POST':
        try:
            incubation.delete()
            messages.success(request, 'تم حذف التسكين بنجاح')
        except Exception as e:
            messages.error(request, f'لا يمكن حذف التسكين: {str(e)}')
        return redirect('hatchery:incubation_list')

    return render(request, 'hatchery/incubation_confirm_delete.html', {'incubation': incubation})

@login_required
def hatching_list(request):
    """عرض قائمة خروج الدفعات"""
    hatchings = BatchHatching.objects.all().order_by('-hatch_date')

    # الحصول على الدفعات الجاهزة للخروج
    # نحصل على الدفعات المسكنة التي حان موعد خروجها ولم يتم تسجيل خروجها بعد
    today = timezone.now().date()

    # الدفعات التي تم تسجيل خروجها بالفعل
    hatched_incubation_ids = BatchHatching.objects.values_list('incubation_id', flat=True)

    # الدفعات الجاهزة للخروج (حان موعد خروجها ولم يتم تسجيل خروجها بعد)
    ready_incubations = BatchIncubation.objects.filter(
        expected_hatch_date__lte=today  # حان موعد خروجها
    ).exclude(
        id__in=hatched_incubation_ids  # لم يتم تسجيل خروجها بعد
    ).order_by('expected_hatch_date')

    return render(request, 'hatchery/hatching_list.html', {
        'hatchings': hatchings,
        'ready_incubations': ready_incubations
    })

@login_required
def hatching_create(request, incubation_id):
    """إنشاء خروج جديد لدفعة"""
    incubation = get_object_or_404(BatchIncubation, pk=incubation_id)

    if request.method == 'POST':
        form = BatchHatchingForm(request.POST, incubation_id=incubation_id)
        if form.is_valid():
            form.save()
            messages.success(request, 'تم تسجيل خروج الدفعة بنجاح')
            return redirect('hatchery:hatching_list')
    else:
        form = BatchHatchingForm(incubation_id=incubation_id)

    return render(request, 'hatchery/hatching_form.html', {'form': form, 'incubation': incubation})

@login_required
def hatching_detail(request, pk):
    """عرض تفاصيل خروج"""
    hatching = get_object_or_404(BatchHatching, pk=pk)
    return render(request, 'hatchery/hatching_detail.html', {'hatching': hatching})

@login_required
def hatching_update(request, pk):
    """تحديث بيانات خروج"""
    hatching = get_object_or_404(BatchHatching, pk=pk)

    if request.method == 'POST':
        form = BatchHatchingForm(request.POST, instance=hatching, incubation_id=hatching.incubation.id)
        if form.is_valid():
            form.save()
            messages.success(request, 'تم تحديث بيانات الخروج بنجاح')
            return redirect('hatchery:hatching_detail', pk=pk)
    else:
        form = BatchHatchingForm(instance=hatching, incubation_id=hatching.incubation.id)

    return render(request, 'hatchery/hatching_form.html', {'form': form, 'incubation': hatching.incubation})

@login_required
def hatching_delete(request, pk):
    """حذف خروج"""
    hatching = get_object_or_404(BatchHatching, pk=pk)

    if request.method == 'POST':
        try:
            hatching.delete()
            messages.success(request, 'تم حذف الخروج بنجاح')
        except Exception as e:
            messages.error(request, f'لا يمكن حذف الخروج: {str(e)}')
        return redirect('hatchery:hatching_list')

    return render(request, 'hatchery/hatching_confirm_delete.html', {'hatching': hatching})

@login_required
def customer_list(request):
    """عرض قائمة العملاء"""
    customers = Customer.objects.all().order_by('name')
    return render(request, 'hatchery/customer_list.html', {'customers': customers})

@login_required
def customer_create(request):
    """إنشاء عميل جديد"""
    if request.method == 'POST':
        form = CustomerForm(request.POST)
        if form.is_valid():
            customer = form.save()
            messages.success(request, 'تم إنشاء العميل بنجاح')

            # التحقق مما إذا كان الطلب من نافذة منبثقة
            if request.GET.get('is_popup'):
                return render(request, 'hatchery/customer_popup_response.html', {'customer': customer})

            return redirect('hatchery:customer_list')
    else:
        form = CustomerForm()

    context = {
        'form': form,
        'is_popup': request.GET.get('is_popup', False)
    }

    if request.GET.get('is_popup'):
        return render(request, 'hatchery/customer_popup_form.html', context)

    return render(request, 'hatchery/customer_form.html', context)

@login_required
def customer_detail(request, pk):
    """عرض تفاصيل عميل"""
    customer = get_object_or_404(Customer, pk=pk)
    return render(request, 'hatchery/customer_detail.html', {'customer': customer})

@login_required
def customer_update(request, pk):
    """تحديث بيانات عميل"""
    # Placeholder - will be implemented later
    messages.success(request, 'تم تحديث بيانات العميل بنجاح')
    return redirect('hatchery:customer_detail', pk=pk)

@login_required
def customer_delete(request, pk):
    """حذف عميل"""
    # Placeholder - will be implemented later
    messages.success(request, 'تم حذف العميل بنجاح')
    return redirect('hatchery:customer_list')

@login_required
def culled_sale_list(request):
    """عرض قائمة مبيعات الفرزة"""
    sales = CulledSale.objects.all().order_by('-invoice_date')

    # الحصول على الدفعات التي لديها كتاكيت فرزة متاحة للبيع
    available_hatchings = BatchHatching.objects.filter(
        culled_count__gt=0  # لديها كتاكيت فرزة
    ).exclude(
        culled_count=0  # استبعاد الدفعات التي ليس لديها فرزة
    ).order_by('-hatch_date')

    # تصفية الدفعات التي لديها فرزة متاحة للبيع
    available_hatchings = [h for h in available_hatchings if h.available_culled_count > 0]

    return render(request, 'hatchery/culled_sale_list.html', {
        'sales': sales,
        'available_hatchings': available_hatchings
    })

@login_required
def culled_sale_create(request, hatching_id):
    """إنشاء عملية بيع جديدة"""
    hatching = get_object_or_404(BatchHatching, pk=hatching_id)

    if request.method == 'POST':
        form = CulledSaleForm(request.POST, hatching_id=hatching_id)
        if form.is_valid():
            form.save()
            messages.success(request, 'تم تسجيل عملية البيع بنجاح')
            return redirect('hatchery:culled_sale_list')
    else:
        form = CulledSaleForm(hatching_id=hatching_id)

    return render(request, 'hatchery/culled_sale_form.html', {'form': form, 'hatching': hatching})

@login_required
def culled_sale_detail(request, pk):
    """عرض تفاصيل عملية بيع"""
    sale = get_object_or_404(CulledSale, pk=pk)
    return render(request, 'hatchery/culled_sale_detail.html', {'sale': sale})

@login_required
def culled_sale_update(request, pk):
    """تحديث بيانات عملية بيع"""
    sale = get_object_or_404(CulledSale, pk=pk)

    if request.method == 'POST':
        form = CulledSaleForm(request.POST, instance=sale, hatching_id=sale.hatching.id)
        if form.is_valid():
            form.save()
            messages.success(request, 'تم تحديث بيانات عملية البيع بنجاح')
            return redirect('hatchery:culled_sale_detail', pk=pk)
    else:
        form = CulledSaleForm(instance=sale, hatching_id=sale.hatching.id)

    return render(request, 'hatchery/culled_sale_form.html', {'form': form, 'hatching': sale.hatching})

@login_required
def culled_sale_delete(request, pk):
    """حذف عملية بيع"""
    sale = get_object_or_404(CulledSale, pk=pk)

    if request.method == 'POST':
        try:
            sale.delete()
            messages.success(request, 'تم حذف عملية البيع بنجاح')
        except Exception as e:
            messages.error(request, f'لا يمكن حذف عملية البيع: {str(e)}')
        return redirect('hatchery:culled_sale_list')

    return render(request, 'hatchery/culled_sale_confirm_delete.html', {'sale': sale})


# DisinfectantCategory views
@login_required
def disinfectant_category_list(request):
    """عرض قائمة تصنيفات المطهرات"""
    categories = DisinfectantCategory.objects.all().order_by('name')
    return render(request, 'hatchery/disinfectant_category_list.html', {'categories': categories})

@login_required
def disinfectant_category_create(request):
    """إنشاء تصنيف مطهر جديد"""
    if request.method == 'POST':
        form = DisinfectantCategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'تم إنشاء تصنيف المطهر بنجاح')
            return redirect('hatchery:disinfectant_category_list')
    else:
        form = DisinfectantCategoryForm()

    return render(request, 'hatchery/disinfectant_category_form.html', {'form': form})

@login_required
def disinfectant_category_update(request, pk):
    """تحديث بيانات تصنيف مطهر"""
    category = get_object_or_404(DisinfectantCategory, pk=pk)

    if request.method == 'POST':
        form = DisinfectantCategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, 'تم تحديث بيانات تصنيف المطهر بنجاح')
            return redirect('hatchery:disinfectant_category_list')
    else:
        form = DisinfectantCategoryForm(instance=category)

    return render(request, 'hatchery/disinfectant_category_form.html', {'form': form})

@login_required
def disinfectant_category_delete(request, pk):
    """حذف تصنيف مطهر"""
    category = get_object_or_404(DisinfectantCategory, pk=pk)

    if request.method == 'POST':
        try:
            category.delete()
            messages.success(request, 'تم حذف تصنيف المطهر بنجاح')
        except Exception as e:
            messages.error(request, f'لا يمكن حذف تصنيف المطهر: {str(e)}')
        return redirect('hatchery:disinfectant_category_list')

    return render(request, 'hatchery/disinfectant_category_confirm_delete.html', {'category': category})


# DisinfectantInventory views
@login_required
def disinfectant_inventory_list(request):
    """عرض قائمة مخزون المطهرات"""
    inventory_items = DisinfectantInventory.objects.all().order_by('category', 'name')
    return render(request, 'hatchery/disinfectant_inventory_list.html', {'inventory_items': inventory_items})

@login_required
def disinfectant_inventory_create(request):
    """إنشاء مطهر جديد في المخزون"""
    if request.method == 'POST':
        form = DisinfectantInventoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'تم إضافة المطهر للمخزون بنجاح')
            return redirect('hatchery:disinfectant_inventory_list')
    else:
        form = DisinfectantInventoryForm()

    return render(request, 'hatchery/disinfectant_inventory_form.html', {'form': form})

@login_required
def disinfectant_inventory_detail(request, pk):
    """عرض تفاصيل مطهر في المخزون"""
    inventory_item = get_object_or_404(DisinfectantInventory, pk=pk)
    transactions = inventory_item.transactions.all().order_by('-transaction_date')

    return render(request, 'hatchery/disinfectant_inventory_detail.html', {
        'inventory_item': inventory_item,
        'transactions': transactions
    })

@login_required
def disinfectant_inventory_update(request, pk):
    """تحديث بيانات مطهر في المخزون"""
    inventory_item = get_object_or_404(DisinfectantInventory, pk=pk)

    if request.method == 'POST':
        form = DisinfectantInventoryForm(request.POST, instance=inventory_item)
        if form.is_valid():
            form.save()
            messages.success(request, 'تم تحديث بيانات المطهر بنجاح')
            return redirect('hatchery:disinfectant_inventory_detail', pk=pk)
    else:
        form = DisinfectantInventoryForm(instance=inventory_item)

    return render(request, 'hatchery/disinfectant_inventory_form.html', {'form': form})

@login_required
def disinfectant_inventory_delete(request, pk):
    """حذف مطهر من المخزون"""
    inventory_item = get_object_or_404(DisinfectantInventory, pk=pk)

    if request.method == 'POST':
        try:
            inventory_item.delete()
            messages.success(request, 'تم حذف المطهر من المخزون بنجاح')
        except Exception as e:
            messages.error(request, f'لا يمكن حذف المطهر: {str(e)}')
        return redirect('hatchery:disinfectant_inventory_list')

    return render(request, 'hatchery/disinfectant_inventory_confirm_delete.html', {'inventory_item': inventory_item})


# DisinfectantTransaction views
@login_required
def disinfectant_transaction_list(request):
    """عرض قائمة حركات المطهرات"""
    transactions = DisinfectantTransaction.objects.all().order_by('-transaction_date')
    return render(request, 'hatchery/disinfectant_transaction_list.html', {'transactions': transactions})

@login_required
def disinfectant_transaction_create(request, disinfectant_id=None, transaction_type=None):
    """إنشاء حركة جديدة للمطهرات (استلام أو صرف)"""
    if disinfectant_id:
        disinfectant = get_object_or_404(DisinfectantInventory, pk=disinfectant_id)
    else:
        disinfectant = None

    if request.method == 'POST':
        form = DisinfectantTransactionForm(request.POST, disinfectant_id=disinfectant_id, transaction_type=transaction_type)
        if form.is_valid():
            form.save()
            messages.success(request, 'تم تسجيل حركة المطهر بنجاح')
            if disinfectant_id:
                return redirect('hatchery:disinfectant_inventory_detail', pk=disinfectant_id)
            else:
                return redirect('hatchery:disinfectant_transaction_list')
    else:
        form = DisinfectantTransactionForm(disinfectant_id=disinfectant_id, transaction_type=transaction_type)

    context = {
        'form': form,
        'disinfectant': disinfectant,
        'transaction_type': transaction_type
    }

    return render(request, 'hatchery/disinfectant_transaction_form.html', context)

@login_required
def disinfectant_transaction_detail(request, pk):
    """عرض تفاصيل حركة مطهر"""
    transaction = get_object_or_404(DisinfectantTransaction, pk=pk)
    return render(request, 'hatchery/disinfectant_transaction_detail.html', {'transaction': transaction})

@login_required
def disinfectant_transaction_update(request, pk):
    """تحديث بيانات حركة مطهر"""
    transaction = get_object_or_404(DisinfectantTransaction, pk=pk)

    # حفظ القيم القديمة للحركة
    old_quantity = transaction.quantity
    old_transaction_type = transaction.transaction_type

    if request.method == 'POST':
        form = DisinfectantTransactionForm(request.POST, instance=transaction)
        if form.is_valid():
            # إلغاء تأثير الحركة القديمة على المخزون
            if old_transaction_type == 'receive':
                transaction.disinfectant.current_stock -= old_quantity
            else:  # صرف
                transaction.disinfectant.current_stock += old_quantity

            # حفظ الحركة الجديدة
            transaction = form.save(commit=False)

            # تطبيق تأثير الحركة الجديدة على المخزون
            if transaction.transaction_type == 'receive':
                transaction.disinfectant.current_stock += transaction.quantity
            else:  # صرف
                transaction.disinfectant.current_stock -= transaction.quantity

            transaction.disinfectant.save()
            transaction.save()

            messages.success(request, 'تم تحديث بيانات حركة المطهر بنجاح')
            return redirect('hatchery:disinfectant_transaction_detail', pk=pk)
    else:
        form = DisinfectantTransactionForm(instance=transaction)

    return render(request, 'hatchery/disinfectant_transaction_form.html', {'form': form, 'transaction': transaction})

@login_required
def disinfectant_transaction_delete(request, pk):
    """حذف حركة مطهر"""
    transaction = get_object_or_404(DisinfectantTransaction, pk=pk)

    if request.method == 'POST':
        try:
            # إلغاء تأثير الحركة على المخزون
            if transaction.transaction_type == 'receive':
                transaction.disinfectant.current_stock -= transaction.quantity
            else:  # صرف
                transaction.disinfectant.current_stock += transaction.quantity

            transaction.disinfectant.save()
            transaction.delete()

            messages.success(request, 'تم حذف حركة المطهر بنجاح')
        except Exception as e:
            messages.error(request, f'لا يمكن حذف حركة المطهر: {str(e)}')

        return redirect('hatchery:disinfectant_transaction_list')

    return render(request, 'hatchery/disinfectant_transaction_confirm_delete.html', {'transaction': transaction})


# BatchDistribution views
@login_required
def distribution_list(request):
    """عرض قائمة توزيعات الدفعات"""
    distributions = BatchDistribution.objects.all().order_by('-distribution_date')

    # الحصول على الدفعات التي خرجت اليوم
    today = timezone.now().date()
    today_hatchings = BatchHatching.objects.filter(
        hatch_date=today
    ).order_by('-hatch_date')

    return render(request, 'hatchery/distribution_list.html', {
        'distributions': distributions,
        'today_hatchings': today_hatchings
    })

@login_required
def distribution_create(request, hatching_id=None):
    """إنشاء توزيع جديد للدفعة"""
    if hatching_id:
        hatching = get_object_or_404(BatchHatching, pk=hatching_id)
    else:
        hatching = None

    if request.method == 'POST':
        form = BatchDistributionForm(request.POST, hatching_id=hatching_id)
        if form.is_valid():
            distribution = form.save()

            # إنشاء نموذج مجموعة لعناصر التوزيع
            formset = BatchDistributionItemFormSet(request.POST, instance=distribution)
            if formset.is_valid():
                formset.save()
                messages.success(request, 'تم تسجيل توزيع الدفعة بنجاح')
                return redirect('hatchery:distribution_detail', pk=distribution.id)
            else:
                # إذا كان هناك خطأ في نموذج المجموعة، نحذف التوزيع ونعرض الأخطاء
                distribution.delete()
        else:
            formset = BatchDistributionItemFormSet(request.POST)
    else:
        form = BatchDistributionForm(hatching_id=hatching_id)
        formset = BatchDistributionItemFormSet()

    return render(request, 'hatchery/distribution_form.html', {
        'form': form,
        'formset': formset,
        'hatching': hatching
    })

@login_required
def distribution_detail(request, pk):
    """عرض تفاصيل توزيع الدفعة"""
    distribution = get_object_or_404(BatchDistribution, pk=pk)
    items = distribution.distribution_items.all()

    return render(request, 'hatchery/distribution_detail.html', {
        'distribution': distribution,
        'items': items
    })

@login_required
def distribution_update(request, pk):
    """تحديث بيانات توزيع الدفعة"""
    distribution = get_object_or_404(BatchDistribution, pk=pk)

    if request.method == 'POST':
        form = BatchDistributionForm(request.POST, instance=distribution)
        if form.is_valid():
            distribution = form.save()

            # تحديث نموذج مجموعة لعناصر التوزيع
            formset = BatchDistributionItemFormSet(request.POST, instance=distribution)
            if formset.is_valid():
                formset.save()
                messages.success(request, 'تم تحديث بيانات توزيع الدفعة بنجاح')
                return redirect('hatchery:distribution_detail', pk=distribution.id)
        else:
            formset = BatchDistributionItemFormSet(request.POST, instance=distribution)
    else:
        form = BatchDistributionForm(instance=distribution)
        formset = BatchDistributionItemFormSet(instance=distribution)

    return render(request, 'hatchery/distribution_form.html', {
        'form': form,
        'formset': formset,
        'distribution': distribution
    })

@login_required
def distribution_delete(request, pk):
    """حذف توزيع الدفعة"""
    distribution = get_object_or_404(BatchDistribution, pk=pk)

    if request.method == 'POST':
        try:
            distribution.delete()
            messages.success(request, 'تم حذف توزيع الدفعة بنجاح')
        except Exception as e:
            messages.error(request, f'لا يمكن حذف توزيع الدفعة: {str(e)}')
        return redirect('hatchery:distribution_list')

    return render(request, 'hatchery/distribution_confirm_delete.html', {'distribution': distribution})


# API views
@login_required
def customer_api_create(request):
    """API لإنشاء عميل جديد بسرعة"""
    if request.method == 'POST':
        form = CustomerForm(request.POST)
        if form.is_valid():
            customer = form.save()
            return JsonResponse({
                'success': True,
                'id': customer.id,
                'name': customer.name,
                'message': 'تم إنشاء العميل بنجاح'
            })
        else:
            errors = {field: error[0] for field, error in form.errors.items()}
            return JsonResponse({
                'success': False,
                'errors': errors,
                'message': 'فشل إنشاء العميل'
            }, status=400)

    return JsonResponse({'success': False, 'message': 'طريقة غير مسموح بها'}, status=405)

@login_required
def incubation_api(request, pk):
    """API للحصول على بيانات الدفعة المسكنة"""
    try:
        incubation = BatchIncubation.objects.get(pk=pk)
        data = {
            'id': incubation.id,
            'incubation_quantity': incubation.incubation_quantity,
            'damaged_quantity': incubation.damaged_quantity,
            'expected_hatch_date': incubation.expected_hatch_date.strftime('%Y-%m-%d'),
        }
        return JsonResponse(data)
    except BatchIncubation.DoesNotExist:
        return JsonResponse({'error': 'Incubation not found'}, status=404)

# Daily Report view
@login_required
def daily_report(request):
    """عرض التقرير اليومي"""
    # الحصول على التاريخ المطلوب (اليوم افتراضيًا أو التاريخ المحدد في الطلب)
    report_date = request.GET.get('date')
    if report_date:
        try:
            report_date = timezone.datetime.strptime(report_date, '%Y-%m-%d').date()
        except ValueError:
            report_date = timezone.now().date()
    else:
        report_date = timezone.now().date()

    # الدفعات الواردة المسجلة اليوم (بغض النظر عن تاريخ الدخول)
    today_entries = BatchEntry.objects.filter(
        created_at__date=report_date
    ).order_by('-date')

    # الدفعات التي تم تسكينها اليوم
    today_incubations = BatchIncubation.objects.filter(
        incubation_date=report_date
    ).order_by('-incubation_date')

    # الدفعات التي خرجت اليوم
    today_hatchings = BatchHatching.objects.filter(
        hatch_date=report_date
    ).order_by('-hatch_date')

    # توزيعات الدفعات اليوم
    today_distributions = BatchDistribution.objects.filter(
        distribution_date=report_date
    ).order_by('-distribution_date')

    # المطهرات الواردة اليوم
    today_received_disinfectants = DisinfectantTransaction.objects.filter(
        transaction_date=report_date,
        transaction_type='receive'
    ).order_by('-transaction_date')

    # المطهرات المنصرفة اليوم
    today_dispensed_disinfectants = DisinfectantTransaction.objects.filter(
        transaction_date=report_date,
        transaction_type='dispense'
    ).order_by('-transaction_date')

    # مبيعات الكتاكيت الفرزة اليوم
    today_culled_sales = CulledSale.objects.filter(
        invoice_date=report_date
    ).order_by('-invoice_date')

    # إحصائيات إضافية

    # إجمالي عدد الكتاكيت الواردة اليوم
    total_entries_count = today_entries.aggregate(total=Sum('quantity'))['total'] or 0

    # إجمالي عدد الكتاكيت المسكنة اليوم
    total_incubations_count = today_incubations.aggregate(total=Sum('incubation_quantity'))['total'] or 0

    # إجمالي عدد الكتاكيت الخارجة اليوم
    total_hatchings_count = today_hatchings.aggregate(
        total_chicks=Sum('chicks_count'),
        total_culled=Sum('culled_count'),
        total_dead=Sum('dead_count')
    )

    # حساب إجمالي المعدم (wasted_count هو خاصية وليس حقلاً)
    total_wasted = sum(hatching.wasted_count for hatching in today_hatchings)
    if total_hatchings_count:
        total_hatchings_count['total_wasted'] = total_wasted

    # إجمالي عدد الكتاكيت الموزعة اليوم
    total_distributed_count = sum(d.total_distributed_count for d in today_distributions)

    # إجمالي عدد الكتاكيت الفرزة المباعة اليوم
    total_culled_sales_count = today_culled_sales.aggregate(total=Sum('quantity'))['total'] or 0

    # إجمالي المبالغ المحصلة من مبيعات الفرزة اليوم
    total_culled_sales_amount = today_culled_sales.aggregate(total=Sum('paid_amount'))['total'] or 0

    # إجمالي المبالغ المحصلة من توزيعات الدفعات اليوم
    total_distributions_amount = sum(d.total_paid_amount for d in today_distributions)

    context = {
        'report_date': report_date,
        'today_entries': today_entries,
        'today_incubations': today_incubations,
        'today_hatchings': today_hatchings,
        'today_distributions': today_distributions,
        'today_received_disinfectants': today_received_disinfectants,
        'today_dispensed_disinfectants': today_dispensed_disinfectants,
        'today_culled_sales': today_culled_sales,
        'total_entries_count': total_entries_count,
        'total_incubations_count': total_incubations_count,
        'total_hatchings_count': total_hatchings_count,
        'total_distributed_count': total_distributed_count,
        'total_culled_sales_count': total_culled_sales_count,
        'total_culled_sales_amount': total_culled_sales_amount,
        'total_distributions_amount': total_distributions_amount,
    }

    # التحقق من نوع الطلب (عرض عادي أو تصدير)
    export_type = request.GET.get('export')
    if export_type == 'excel':
        return export_daily_report_excel(context)
    elif export_type == 'pdf':
        return export_daily_report_pdf(context)
    elif export_type == 'print':
        # إضافة التاريخ والوقت الحاليين إلى السياق
        context['current_datetime'] = timezone.now()

        # إضافة إعدادات الطباعة إلى السياق
        context['show_created_today'] = request.GET.get('show_created_today') == '1'
        context['show_price_in_distribution'] = request.GET.get('show_price_in_distribution') == '1'
        context['show_price_in_culled_sales'] = request.GET.get('show_price_in_culled_sales') == '1'

        # حساب إجمالي المبلغ المدفوع من مبيعات الفرزة
        context['total_culled_sales_paid'] = today_culled_sales.aggregate(total=Sum('paid_amount'))['total'] or 0

        return render(request, 'hatchery/daily_report_print.html', context)

    return render(request, 'hatchery/daily_report.html', context)


def export_daily_report_excel(context):
    """تصدير التقرير اليومي بصيغة Excel"""
    # إنشاء ملف Excel في الذاكرة
    output = io.BytesIO()
    workbook = xlsxwriter.Workbook(output)
    worksheet = workbook.add_worksheet('التقرير اليومي')

    # تنسيق العناوين
    header_format = workbook.add_format({
        'bold': True,
        'align': 'center',
        'valign': 'vcenter',
        'bg_color': '#4472C4',
        'font_color': 'white',
        'border': 1
    })

    # تنسيق الخلايا
    cell_format = workbook.add_format({
        'align': 'center',
        'valign': 'vcenter',
        'border': 1
    })

    # تنسيق العناوين الفرعية
    subheader_format = workbook.add_format({
        'bold': True,
        'align': 'right',
        'valign': 'vcenter',
        'bg_color': '#D9E1F2',
        'border': 1
    })

    # تنسيق التاريخ
    date_format = workbook.add_format({
        'num_format': 'yyyy-mm-dd',
        'align': 'center',
        'valign': 'vcenter',
        'border': 1
    })

    # عنوان التقرير
    worksheet.merge_range('A1:H1', f'التقرير اليومي - {context["report_date"].strftime("%Y-%m-%d")}', header_format)
    worksheet.set_column('A:H', 15)  # تعيين عرض الأعمدة

    # بدء من الصف الثاني مباشرة
    row = 2

    # الدفعات الواردة
    worksheet.merge_range(f'A{row}:H{row}', 'الدفعات الواردة المسجلة اليوم', subheader_format)
    row += 1

    # عناوين جدول الدفعات الواردة
    worksheet.write(f'A{row}', 'اسم الدفعة', header_format)
    worksheet.write(f'B{row}', 'تاريخ الدخول', header_format)
    worksheet.write(f'C{row}', 'الكمية', header_format)
    worksheet.write(f'D{row}', 'اسم السائق', header_format)
    worksheet.write(f'E{row}', 'ملاحظات', header_format)
    worksheet.merge_range(f'F{row}:H{row}', '', header_format)
    row += 1

    # بيانات الدفعات الواردة
    for entry in context['today_entries']:
        worksheet.write(f'A{row}', entry.batch_name.name, cell_format)
        worksheet.write(f'B{row}', entry.date, date_format)
        worksheet.write(f'C{row}', entry.quantity, cell_format)
        worksheet.write(f'D{row}', entry.driver or '-', cell_format)
        worksheet.write(f'E{row}', entry.notes or '-', cell_format)
        worksheet.merge_range(f'F{row}:H{row}', '', cell_format)
        row += 1

    if not context['today_entries']:
        worksheet.merge_range(f'A{row}:H{row}', 'لا توجد دفعات واردة مسجلة اليوم', cell_format)
        row += 1

    row += 1

    # الدفعات المسكنة
    worksheet.merge_range(f'A{row}:H{row}', 'الدفعات التي تم تسكينها اليوم', subheader_format)
    row += 1

    # عناوين جدول الدفعات المسكنة
    worksheet.write(f'A{row}', 'اسم الدفعة', header_format)
    worksheet.write(f'B{row}', 'تاريخ التسكين', header_format)
    worksheet.write(f'C{row}', 'كمية التسكين', header_format)
    worksheet.write(f'D{row}', 'المعدم', header_format)
    worksheet.write(f'E{row}', 'تاريخ الخروج المتوقع', header_format)
    worksheet.merge_range(f'F{row}:H{row}', '', header_format)
    row += 1

    # بيانات الدفعات المسكنة
    for incubation in context['today_incubations']:
        worksheet.write(f'A{row}', incubation.batch_entry.batch_name.name, cell_format)
        worksheet.write(f'B{row}', incubation.incubation_date, date_format)
        worksheet.write(f'C{row}', incubation.incubation_quantity, cell_format)
        worksheet.write(f'D{row}', incubation.damaged_quantity, cell_format)
        worksheet.write(f'E{row}', incubation.expected_hatch_date, date_format)
        worksheet.merge_range(f'F{row}:H{row}', '', cell_format)
        row += 1

    if not context['today_incubations']:
        worksheet.merge_range(f'A{row}:H{row}', 'لا توجد دفعات تم تسكينها اليوم', cell_format)
        row += 1

    row += 1

    # الدفعات الخارجة
    worksheet.merge_range(f'A{row}:I{row}', 'الدفعات التي خرجت اليوم', subheader_format)
    row += 1

    # عناوين جدول الدفعات الخارجة
    worksheet.write(f'A{row}', 'اسم الدفعة', header_format)
    worksheet.write(f'B{row}', 'تاريخ الوارد', header_format)
    worksheet.write(f'C{row}', 'تاريخ الخروج', header_format)
    worksheet.write(f'D{row}', 'الكتاكيت', header_format)
    worksheet.write(f'E{row}', 'الفرزة', header_format)
    worksheet.write(f'F{row}', 'الفاطس', header_format)
    worksheet.write(f'G{row}', 'المعدم', header_format)
    worksheet.write(f'H{row}', 'نسبة الإخصاب', header_format)
    worksheet.write(f'I{row}', 'نسبة الفقس', header_format)
    row += 1

    # بيانات الدفعات الخارجة
    for hatching in context['today_hatchings']:
        worksheet.write(f'A{row}', hatching.incubation.batch_entry.batch_name.name, cell_format)
        worksheet.write(f'B{row}', hatching.incubation.batch_entry.date, date_format)
        worksheet.write(f'C{row}', hatching.hatch_date, date_format)
        worksheet.write(f'D{row}', hatching.chicks_count, cell_format)
        worksheet.write(f'E{row}', hatching.culled_count, cell_format)
        worksheet.write(f'F{row}', hatching.dead_count, cell_format)
        worksheet.write(f'G{row}', hatching.wasted_count, cell_format)
        worksheet.write(f'H{row}', f"{hatching.fertility_rate}%", cell_format)
        worksheet.write(f'I{row}', f"{hatching.hatch_rate}%", cell_format)
        row += 1

    if not context['today_hatchings']:
        worksheet.merge_range(f'A{row}:I{row}', 'لا توجد دفعات خرجت اليوم', cell_format)
        row += 1

    row += 1

    # توزيعات الدفعات
    worksheet.merge_range(f'A{row}:H{row}', 'توزيعات الدفعات اليوم', subheader_format)
    row += 1

    # عناوين جدول توزيعات الدفعات
    worksheet.write(f'A{row}', 'اسم الدفعة', header_format)
    worksheet.write(f'B{row}', 'تاريخ التوزيع', header_format)
    worksheet.write(f'C{row}', 'الكتاكيت الموزعة', header_format)
    worksheet.write(f'D{row}', 'عدد العملاء', header_format)
    worksheet.write(f'E{row}', 'المبلغ المدفوع', header_format)
    worksheet.merge_range(f'F{row}:H{row}', '', header_format)
    row += 1

    # بيانات توزيعات الدفعات
    for distribution in context['today_distributions']:
        worksheet.write(f'A{row}', distribution.hatching.incubation.batch_entry.batch_name.name, cell_format)
        worksheet.write(f'B{row}', distribution.distribution_date, date_format)
        worksheet.write(f'C{row}', distribution.total_distributed_count, cell_format)
        worksheet.write(f'D{row}', distribution.distribution_items.count(), cell_format)
        worksheet.write(f'E{row}', distribution.total_paid_amount, cell_format)
        worksheet.merge_range(f'F{row}:H{row}', '', cell_format)
        row += 1

    if not context['today_distributions']:
        worksheet.merge_range(f'A{row}:H{row}', 'لا توجد توزيعات دفعات اليوم', cell_format)
        row += 1

    row += 1

    # المطهرات الواردة
    worksheet.merge_range(f'A{row}:H{row}', 'المطهرات الواردة اليوم', subheader_format)
    row += 1

    # عناوين جدول المطهرات الواردة
    worksheet.write(f'A{row}', 'المطهر', header_format)
    worksheet.write(f'B{row}', 'التصنيف', header_format)
    worksheet.write(f'C{row}', 'الكمية', header_format)
    worksheet.write(f'D{row}', 'وحدة القياس', header_format)
    worksheet.write(f'E{row}', 'ملاحظات', header_format)
    worksheet.merge_range(f'F{row}:H{row}', '', header_format)
    row += 1

    # بيانات المطهرات الواردة
    for transaction in context['today_received_disinfectants']:
        worksheet.write(f'A{row}', transaction.disinfectant.name, cell_format)
        worksheet.write(f'B{row}', transaction.disinfectant.category.name, cell_format)
        worksheet.write(f'C{row}', transaction.quantity, cell_format)
        worksheet.write(f'D{row}', transaction.disinfectant.unit, cell_format)
        worksheet.write(f'E{row}', transaction.notes or '-', cell_format)
        worksheet.merge_range(f'F{row}:H{row}', '', cell_format)
        row += 1

    if not context['today_received_disinfectants']:
        worksheet.merge_range(f'A{row}:H{row}', 'لا توجد مطهرات واردة اليوم', cell_format)
        row += 1

    row += 1

    # المطهرات المنصرفة
    worksheet.merge_range(f'A{row}:H{row}', 'المطهرات المنصرفة اليوم', subheader_format)
    row += 1

    # عناوين جدول المطهرات المنصرفة
    worksheet.write(f'A{row}', 'المطهر', header_format)
    worksheet.write(f'B{row}', 'التصنيف', header_format)
    worksheet.write(f'C{row}', 'الكمية', header_format)
    worksheet.write(f'D{row}', 'وحدة القياس', header_format)
    worksheet.write(f'E{row}', 'ملاحظات', header_format)
    worksheet.merge_range(f'F{row}:H{row}', '', header_format)
    row += 1

    # بيانات المطهرات المنصرفة
    for transaction in context['today_dispensed_disinfectants']:
        worksheet.write(f'A{row}', transaction.disinfectant.name, cell_format)
        worksheet.write(f'B{row}', transaction.disinfectant.category.name, cell_format)
        worksheet.write(f'C{row}', transaction.quantity, cell_format)
        worksheet.write(f'D{row}', transaction.disinfectant.unit, cell_format)
        worksheet.write(f'E{row}', transaction.notes or '-', cell_format)
        worksheet.merge_range(f'F{row}:H{row}', '', cell_format)
        row += 1

    if not context['today_dispensed_disinfectants']:
        worksheet.merge_range(f'A{row}:H{row}', 'لا توجد مطهرات منصرفة اليوم', cell_format)
        row += 1

    row += 1

    # مبيعات الكتاكيت الفرزة
    worksheet.merge_range(f'A{row}:H{row}', 'مبيعات الكتاكيت الفرزة اليوم', subheader_format)
    row += 1

    # عناوين جدول مبيعات الكتاكيت الفرزة
    worksheet.write(f'A{row}', 'العميل', header_format)
    worksheet.write(f'B{row}', 'الدفعة', header_format)
    worksheet.write(f'C{row}', 'الكمية', header_format)
    worksheet.write(f'D{row}', 'السعر', header_format)
    worksheet.write(f'E{row}', 'الإجمالي', header_format)
    worksheet.write(f'F{row}', 'المدفوع', header_format)
    worksheet.merge_range(f'G{row}:H{row}', '', header_format)
    row += 1

    # بيانات مبيعات الكتاكيت الفرزة
    for sale in context['today_culled_sales']:
        worksheet.write(f'A{row}', sale.customer.name, cell_format)
        worksheet.write(f'B{row}', sale.hatching.incubation.batch_entry.batch_name.name, cell_format)
        worksheet.write(f'C{row}', sale.quantity, cell_format)
        worksheet.write(f'D{row}', sale.price_per_unit, cell_format)
        worksheet.write(f'E{row}', sale.total_amount, cell_format)
        worksheet.write(f'F{row}', sale.paid_amount, cell_format)
        worksheet.merge_range(f'G{row}:H{row}', '', cell_format)
        row += 1

    if not context['today_culled_sales']:
        worksheet.merge_range(f'A{row}:H{row}', 'لا توجد مبيعات كتاكيت فرزة اليوم', cell_format)
        row += 1

    # تعديل عرض الأعمدة لتناسب المحتوى
    worksheet.set_column('A:A', 20)  # اسم الدفعة
    worksheet.set_column('B:B', 15)  # تاريخ
    worksheet.set_column('C:C', 15)  # تاريخ/كمية
    worksheet.set_column('D:D', 15)  # كمية/عدد
    worksheet.set_column('E:E', 15)  # ملاحظات/مبلغ
    worksheet.set_column('F:F', 15)  #
    worksheet.set_column('G:G', 15)  #
    worksheet.set_column('H:H', 15)  #
    worksheet.set_column('I:I', 15)  #

    workbook.close()

    # إعادة مؤشر الملف إلى البداية
    output.seek(0)

    # إنشاء استجابة HTTP مع ملف Excel
    filename = f'daily_report_{context["report_date"].strftime("%Y-%m-%d")}.xlsx'
    response = HttpResponse(
        output,
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    return response


def export_daily_report_pdf(context):
    """تصدير التقرير اليومي بصيغة PDF"""
    # إضافة التاريخ والوقت الحاليين إلى السياق
    context['current_datetime'] = timezone.now()

    # إعداد ملف PDF
    response = HttpResponse(content_type='application/pdf')
    filename = f'daily_report_{context["report_date"].strftime("%Y-%m-%d")}.pdf'
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    # إنشاء مستند PDF بالاتجاه الأفقي
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        rightMargin=30,
        leftMargin=30,
        topMargin=30,
        bottomMargin=30
    )

    # إنشاء قائمة العناصر
    elements = []

    # إنشاء أنماط النص
    styles = getSampleStyleSheet()

    # إنشاء أنماط النص العربي باستخدام الخطوط المدمجة
    arabic_style = ParagraphStyle(
        'ArabicStyle',
        parent=styles['Normal'],
        fontName='Helvetica',
        alignment=2,  # تحاذي يمين
        fontSize=14,
        leading=16,
        spaceAfter=10
    )

    arabic_title_style = ParagraphStyle(
        'ArabicTitleStyle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        alignment=1,  # وسط
        fontSize=20,
        leading=24,
        spaceAfter=12,
        backColor='#2c3e50',
        textColor='white'
    )

    arabic_subtitle_style = ParagraphStyle(
        'ArabicSubtitleStyle',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        alignment=1,  # وسط
        fontSize=16,
        leading=18,
        spaceAfter=10,
        backColor='#3498db',
        textColor='white'
    )

    # إضافة عنوان التقرير
    title_text = arabic_reshaper.reshape(f"التقرير اليومي - {context['report_date'].strftime('%Y-%m-%d')}")
    title_text = get_display(title_text)
    elements.append(Paragraph(title_text, arabic_title_style))
    elements.append(Spacer(1, 20))

    # إضافة الدفعات الواردة
    if context.get('today_entries'):
        # إضافة عنوان القسم
        subtitle_text = arabic_reshaper.reshape("الدفعات الواردة المسجلة اليوم")
        subtitle_text = get_display(subtitle_text)
        elements.append(Paragraph(subtitle_text, arabic_subtitle_style))

        # إنشاء بيانات الجدول
        table_data = [
            [
                get_display(arabic_reshaper.reshape("اسم الدفعة")),
                get_display(arabic_reshaper.reshape("تاريخ الدخول")),
                get_display(arabic_reshaper.reshape("الكمية")),
                get_display(arabic_reshaper.reshape("اسم السائق")),
                get_display(arabic_reshaper.reshape("ملاحظات"))
            ]
        ]

        # إضافة بيانات الدفعات
        for entry in context.get('today_entries', []):
            row = [
                get_display(arabic_reshaper.reshape(entry.batch_name.name)),
                get_display(arabic_reshaper.reshape(entry.date.strftime('%Y-%m-%d'))),
                str(entry.quantity),
                get_display(arabic_reshaper.reshape(entry.driver or '-')),
                get_display(arabic_reshaper.reshape(entry.notes or '-'))
            ]
            table_data.append(row)

        # إنشاء الجدول
        table = Table(table_data, colWidths=[150, 100, 80, 120, 200])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, 0), 14),
            ('FONTSIZE', (0, 1), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))

        elements.append(table)
        elements.append(Spacer(1, 20))
    else:
        # إضافة رسالة فارغة
        empty_text = arabic_reshaper.reshape("لا توجد دفعات واردة مسجلة اليوم")
        empty_text = get_display(empty_text)
        empty_style = ParagraphStyle(
            'EmptyStyle',
            parent=styles['Normal'],
            fontName='Helvetica',
            alignment=1,  # وسط
            fontSize=14,
            leading=16,
            spaceAfter=10,
            textColor='#7f8c8d'
        )
        elements.append(Paragraph(empty_text, empty_style))
        elements.append(Spacer(1, 20))

    # إضافة الدفعات المسكنة
    if context.get('today_incubations'):
        # إضافة عنوان القسم
        subtitle_text = arabic_reshaper.reshape("الدفعات التي تم تسكينها اليوم")
        subtitle_text = get_display(subtitle_text)
        elements.append(Paragraph(subtitle_text, arabic_subtitle_style))

        # إنشاء بيانات الجدول
        table_data = [
            [
                get_display(arabic_reshaper.reshape("اسم الدفعة")),
                get_display(arabic_reshaper.reshape("تاريخ التسكين")),
                get_display(arabic_reshaper.reshape("الكمية")),
                get_display(arabic_reshaper.reshape("الفاقد")),
                get_display(arabic_reshaper.reshape("تاريخ الخروج المتوقع"))
            ]
        ]

        # إضافة بيانات الدفعات المسكنة
        for incubation in context.get('today_incubations', []):
            row = [
                get_display(arabic_reshaper.reshape(incubation.batch_entry.batch_name.name)),
                get_display(arabic_reshaper.reshape(incubation.incubation_date.strftime('%Y-%m-%d'))),
                str(incubation.incubation_quantity),
                str(incubation.damaged_quantity or 0),
                get_display(arabic_reshaper.reshape(incubation.expected_hatch_date.strftime('%Y-%m-%d')))
            ]
            table_data.append(row)

        # إنشاء الجدول
        table = Table(table_data, colWidths=[150, 100, 80, 80, 120])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, 0), 14),
            ('FONTSIZE', (0, 1), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))

        elements.append(table)
        elements.append(Spacer(1, 20))
    else:
        # إضافة رسالة فارغة
        empty_text = arabic_reshaper.reshape("لا توجد دفعات تم تسكينها اليوم")
        empty_text = get_display(empty_text)
        empty_style = ParagraphStyle(
            'EmptyStyle',
            parent=styles['Normal'],
            fontName='Helvetica',
            alignment=1,  # وسط
            fontSize=14,
            leading=16,
            spaceAfter=10,
            textColor='#7f8c8d'
        )
        elements.append(Paragraph(empty_text, empty_style))
        elements.append(Spacer(1, 20))

    # إضافة الدفعات الخارجة
    if context.get('today_hatchings'):
        # إضافة عنوان القسم
        subtitle_text = arabic_reshaper.reshape("الدفعات التي خرجت اليوم")
        subtitle_text = get_display(subtitle_text)
        elements.append(Paragraph(subtitle_text, arabic_subtitle_style))

        # إنشاء بيانات الجدول
        table_data = [
            [
                get_display(arabic_reshaper.reshape("اسم الدفعة")),
                get_display(arabic_reshaper.reshape("تاريخ الوارد")),
                get_display(arabic_reshaper.reshape("تاريخ الخروج")),
                get_display(arabic_reshaper.reshape("الكتاكيت")),
                get_display(arabic_reshaper.reshape("الفرزة")),
                get_display(arabic_reshaper.reshape("الفاطس")),
                get_display(arabic_reshaper.reshape("المعدم")),
                get_display(arabic_reshaper.reshape("نسبة الإخصاب")),
                get_display(arabic_reshaper.reshape("نسبة الفقس"))
            ]
        ]

        # إضافة بيانات الدفعات الخارجة
        for hatching in context.get('today_hatchings', []):
            row = [
                get_display(arabic_reshaper.reshape(hatching.incubation.batch_entry.batch_name.name)),
                get_display(arabic_reshaper.reshape(hatching.incubation.batch_entry.date.strftime('%Y-%m-%d'))),
                get_display(arabic_reshaper.reshape(hatching.hatch_date.strftime('%Y-%m-%d'))),
                str(hatching.chicks_count),
                str(hatching.culled_count),
                str(hatching.dead_count),
                str(hatching.wasted_count),
                f"{hatching.fertility_rate}%",
                f"{hatching.hatch_rate}%"
            ]
            table_data.append(row)

        # إنشاء الجدول
        table = Table(table_data, colWidths=[100, 70, 70, 60, 60, 60, 60, 70, 70])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, 0), 14),
            ('FONTSIZE', (0, 1), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))

        elements.append(table)
        elements.append(Spacer(1, 20))
    else:
        # إضافة رسالة فارغة
        empty_text = arabic_reshaper.reshape("لا توجد دفعات خرجت اليوم")
        empty_text = get_display(empty_text)
        empty_style = ParagraphStyle(
            'EmptyStyle',
            parent=styles['Normal'],
            fontName='Helvetica',
            alignment=1,  # وسط
            fontSize=14,
            leading=16,
            spaceAfter=10,
            textColor='#7f8c8d'
        )
        elements.append(Paragraph(empty_text, empty_style))
        elements.append(Spacer(1, 20))

    # إضافة توزيعات الدفعات
    if context.get('today_distributions'):
        # إضافة عنوان القسم
        subtitle_text = arabic_reshaper.reshape("توزيعات الدفعات اليوم")
        subtitle_text = get_display(subtitle_text)
        elements.append(Paragraph(subtitle_text, arabic_subtitle_style))

        # إنشاء بيانات الجدول
        table_data = [
            [
                get_display(arabic_reshaper.reshape("اسم الدفعة")),
                get_display(arabic_reshaper.reshape("تاريخ التوزيع")),
                get_display(arabic_reshaper.reshape("الكتاكيت الموزعة")),
                get_display(arabic_reshaper.reshape("عدد العملاء")),
                get_display(arabic_reshaper.reshape("المبلغ المدفوع"))
            ]
        ]

        # إضافة بيانات التوزيعات
        for distribution in context.get('today_distributions', []):
            row = [
                get_display(arabic_reshaper.reshape(distribution.hatching.incubation.batch_entry.batch_name.name)),
                get_display(arabic_reshaper.reshape(distribution.distribution_date.strftime('%Y-%m-%d'))),
                str(distribution.total_distributed_count),
                str(distribution.distribution_items.count()),
                str(distribution.total_paid_amount)
            ]
            table_data.append(row)

        # إنشاء الجدول
        table = Table(table_data, colWidths=[150, 100, 100, 100, 100])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, 0), 14),
            ('FONTSIZE', (0, 1), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))

        elements.append(table)
        elements.append(Spacer(1, 20))
    else:
        # إضافة رسالة فارغة
        empty_text = arabic_reshaper.reshape("لا توجد توزيعات دفعات اليوم")
        empty_text = get_display(empty_text)
        empty_style = ParagraphStyle(
            'EmptyStyle',
            parent=styles['Normal'],
            fontName='Helvetica',
            alignment=1,  # وسط
            fontSize=14,
            leading=16,
            spaceAfter=10,
            textColor='#7f8c8d'
        )
        elements.append(Paragraph(empty_text, empty_style))
        elements.append(Spacer(1, 20))

    # إضافة المطهرات الواردة
    if context.get('today_received_disinfectants'):
        # إضافة عنوان القسم
        subtitle_text = arabic_reshaper.reshape("المطهرات الواردة اليوم")
        subtitle_text = get_display(subtitle_text)
        elements.append(Paragraph(subtitle_text, arabic_subtitle_style))

        # إنشاء بيانات الجدول
        table_data = [
            [
                get_display(arabic_reshaper.reshape("المطهر")),
                get_display(arabic_reshaper.reshape("التصنيف")),
                get_display(arabic_reshaper.reshape("الكمية")),
                get_display(arabic_reshaper.reshape("وحدة القياس")),
                get_display(arabic_reshaper.reshape("ملاحظات"))
            ]
        ]

        # إضافة بيانات المطهرات الواردة
        for transaction in context.get('today_received_disinfectants', []):
            row = [
                get_display(arabic_reshaper.reshape(transaction.disinfectant.name)),
                get_display(arabic_reshaper.reshape(transaction.disinfectant.category.name)),
                str(transaction.quantity),
                get_display(arabic_reshaper.reshape(transaction.disinfectant.unit)),
                get_display(arabic_reshaper.reshape(transaction.notes or '-'))
            ]
            table_data.append(row)

        # إنشاء الجدول
        table = Table(table_data, colWidths=[120, 120, 80, 100, 150])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, 0), 14),
            ('FONTSIZE', (0, 1), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))

        elements.append(table)
        elements.append(Spacer(1, 20))
    else:
        # إضافة رسالة فارغة
        empty_text = arabic_reshaper.reshape("لا توجد مطهرات واردة اليوم")
        empty_text = get_display(empty_text)
        empty_style = ParagraphStyle(
            'EmptyStyle',
            parent=styles['Normal'],
            fontName='Helvetica',
            alignment=1,  # وسط
            fontSize=14,
            leading=16,
            spaceAfter=10,
            textColor='#7f8c8d'
        )
        elements.append(Paragraph(empty_text, empty_style))
        elements.append(Spacer(1, 20))

    # إضافة المطهرات المنصرفة
    if context.get('today_dispensed_disinfectants'):
        # إضافة عنوان القسم
        subtitle_text = arabic_reshaper.reshape("المطهرات المنصرفة اليوم")
        subtitle_text = get_display(subtitle_text)
        elements.append(Paragraph(subtitle_text, arabic_subtitle_style))

        # إنشاء بيانات الجدول
        table_data = [
            [
                get_display(arabic_reshaper.reshape("المطهر")),
                get_display(arabic_reshaper.reshape("التصنيف")),
                get_display(arabic_reshaper.reshape("الكمية")),
                get_display(arabic_reshaper.reshape("وحدة القياس")),
                get_display(arabic_reshaper.reshape("ملاحظات"))
            ]
        ]

        # إضافة بيانات المطهرات المنصرفة
        for transaction in context.get('today_dispensed_disinfectants', []):
            row = [
                get_display(arabic_reshaper.reshape(transaction.disinfectant.name)),
                get_display(arabic_reshaper.reshape(transaction.disinfectant.category.name)),
                str(transaction.quantity),
                get_display(arabic_reshaper.reshape(transaction.disinfectant.unit)),
                get_display(arabic_reshaper.reshape(transaction.notes or '-'))
            ]
            table_data.append(row)

        # إنشاء الجدول
        table = Table(table_data, colWidths=[120, 120, 80, 100, 150])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, 0), 14),
            ('FONTSIZE', (0, 1), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))

        elements.append(table)
        elements.append(Spacer(1, 20))
    else:
        # إضافة رسالة فارغة
        empty_text = arabic_reshaper.reshape("لا توجد مطهرات منصرفة اليوم")
        empty_text = get_display(empty_text)
        empty_style = ParagraphStyle(
            'EmptyStyle',
            parent=styles['Normal'],
            fontName='Helvetica',
            alignment=1,  # وسط
            fontSize=14,
            leading=16,
            spaceAfter=10,
            textColor='#7f8c8d'
        )
        elements.append(Paragraph(empty_text, empty_style))
        elements.append(Spacer(1, 20))

    # إضافة مبيعات الكتاكيت الفرزة
    if context.get('today_culled_sales'):
        # إضافة عنوان القسم
        subtitle_text = arabic_reshaper.reshape("مبيعات الكتاكيت الفرزة اليوم")
        subtitle_text = get_display(subtitle_text)
        elements.append(Paragraph(subtitle_text, arabic_subtitle_style))

        # إنشاء بيانات الجدول
        table_data = [
            [
                get_display(arabic_reshaper.reshape("العميل")),
                get_display(arabic_reshaper.reshape("الدفعة")),
                get_display(arabic_reshaper.reshape("الكمية")),
                get_display(arabic_reshaper.reshape("السعر")),
                get_display(arabic_reshaper.reshape("الإجمالي")),
                get_display(arabic_reshaper.reshape("المدفوع"))
            ]
        ]

        # إضافة بيانات مبيعات الفرزة
        for sale in context.get('today_culled_sales', []):
            row = [
                get_display(arabic_reshaper.reshape(sale.customer.name)),
                get_display(arabic_reshaper.reshape(sale.hatching.incubation.batch_entry.batch_name.name)),
                str(sale.quantity),
                str(sale.price_per_unit),
                str(sale.total_amount),
                str(sale.paid_amount)
            ]
            table_data.append(row)

        # إنشاء الجدول
        table = Table(table_data, colWidths=[120, 120, 80, 80, 100, 100])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, 0), 14),
            ('FONTSIZE', (0, 1), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))

        elements.append(table)
        elements.append(Spacer(1, 20))
    else:
        # إضافة رسالة فارغة
        empty_text = arabic_reshaper.reshape("لا توجد مبيعات كتاكيت فرزة اليوم")
        empty_text = get_display(empty_text)
        empty_style = ParagraphStyle(
            'EmptyStyle',
            parent=styles['Normal'],
            fontName='Helvetica',
            alignment=1,  # وسط
            fontSize=14,
            leading=16,
            spaceAfter=10,
            textColor='#7f8c8d'
        )
        elements.append(Paragraph(empty_text, empty_style))
        elements.append(Spacer(1, 20))

    # إضافة تذييل التقرير
    footer_text = arabic_reshaper.reshape(f"تم إنشاء هذا التقرير بواسطة نظام إدارة معامل التفريخ - {context['current_datetime'].strftime('%Y-%m-%d %H:%M')}")
    footer_text = get_display(footer_text)
    footer_style = ParagraphStyle(
        'FooterStyle',
        parent=styles['Normal'],
        fontName='Helvetica',
        alignment=1,  # وسط
        fontSize=12,
        leading=14,
        textColor='#555555',
        backColor='#f8f9fa',
        borderPadding=10,
        borderWidth=1,
        borderColor='#3498db',
        borderRadius=5
    )
    elements.append(Paragraph(footer_text, footer_style))

    # بناء المستند
    doc.build(elements)

    # إرجاع الاستجابة
    pdf_data = buffer.getvalue()
    buffer.close()
    response.write(pdf_data)

    return response



