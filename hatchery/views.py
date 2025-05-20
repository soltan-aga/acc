from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Sum, Q, F
from django.http import HttpResponse, JsonResponse
from django.template.loader import render_to_string

import io
import xlsxwriter

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
    BatchDistributionForm, BatchDistributionItemForm, BatchDistributionItemFormSet,
    PrintSettingsForm
)
import json

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

    # البحث
    search_query = request.GET.get('q')
    if search_query:
        batches = batches.filter(
            Q(batch_name__name__icontains=search_query) |
            Q(driver__icontains=search_query) |
            Q(notes__icontains=search_query)
        )

    # الفلترة حسب التاريخ
    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')

    if from_date:
        batches = batches.filter(date__gte=from_date)
    if to_date:
        batches = batches.filter(date__lte=to_date)

    # الفلترة حسب اسم الدفعة
    batch_name_id = request.GET.get('batch_name')
    if batch_name_id:
        batches = batches.filter(batch_name_id=batch_name_id)

    # إعداد قائمة الفلاتر
    batch_names = BatchName.objects.filter(is_active=True).order_by('name')

    batch_filters = [
        {
            'name': 'batch_name',
            'label': 'اسم الدفعة',
            'type': 'select',
            'options': batch_names,
            'value': batch_name_id
        }
    ]

    # التحقق من نوع الطلب (عرض عادي أو تصدير)
    export_type = request.GET.get('export')
    if export_type == 'print':
        return render(request, 'hatchery/batch_list_print.html', {
            'batches': batches,
            'current_datetime': timezone.now(),
            'search_query': search_query,
            'from_date': from_date,
            'to_date': to_date
        })

    return render(request, 'hatchery/batch_list.html', {
        'batches': batches,
        'batch_filters': batch_filters,
        'search_query': search_query,
        'from_date': from_date,
        'to_date': to_date,
        'date_filter': True
    })

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

    # البحث
    search_query = request.GET.get('q')
    if search_query:
        incubations = incubations.filter(
            Q(batch_entry__batch_name__name__icontains=search_query) |
            Q(notes__icontains=search_query)
        )

    # الفلترة حسب التاريخ
    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')

    if from_date:
        incubations = incubations.filter(incubation_date__gte=from_date)
    if to_date:
        incubations = incubations.filter(incubation_date__lte=to_date)

    # الفلترة حسب اسم الدفعة
    batch_name_id = request.GET.get('batch_name')
    if batch_name_id:
        incubations = incubations.filter(batch_entry__batch_name_id=batch_name_id)

    # الفلترة حسب حالة الخروج
    hatched_status = request.GET.get('hatched_status')
    if hatched_status:
        if hatched_status == 'hatched':
            incubations = incubations.filter(hatching__isnull=False)
        elif hatched_status == 'not_hatched':
            incubations = incubations.filter(hatching__isnull=True)

    # الحصول على الدفعات المتاحة للتسكين
    # أولاً، نحصل على قائمة الدفعات التي تم تسكينها بالفعل
    incubated_batch_ids = BatchIncubation.objects.values_list('batch_entry_id', flat=True)

    # ثم نحصل على الدفعات النشطة التي لم يتم تسكينها بعد
    available_batches = BatchEntry.objects.filter(
        batch_name__is_active=True  # الدفعات النشطة فقط
    ).exclude(
        id__in=incubated_batch_ids  # استبعاد الدفعات التي تم تسكينها بالفعل
    ).order_by('-date')

    # إعداد قائمة الفلاتر
    batch_names = BatchName.objects.filter(is_active=True).order_by('name')

    incubation_filters = [
        {
            'name': 'batch_name',
            'label': 'اسم الدفعة',
            'type': 'select',
            'options': batch_names,
            'value': batch_name_id
        },
        {
            'name': 'hatched_status',
            'label': 'حالة الخروج',
            'type': 'select',
            'options': [('hatched', 'خرجت'), ('not_hatched', 'لم تخرج')],
            'value': hatched_status
        }
    ]

    # التحقق من نوع الطلب (عرض عادي أو تصدير)
    export_type = request.GET.get('export')
    if export_type == 'print':
        return render(request, 'hatchery/incubation_list_print.html', {
            'incubations': incubations,
            'current_datetime': timezone.now(),
            'search_query': search_query,
            'from_date': from_date,
            'to_date': to_date
        })

    return render(request, 'hatchery/incubation_list.html', {
        'incubations': incubations,
        'available_batches': available_batches,
        'incubation_filters': incubation_filters,
        'search_query': search_query,
        'from_date': from_date,
        'to_date': to_date,
        'date_filter': True
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

    # البحث
    search_query = request.GET.get('q')
    if search_query:
        hatchings = hatchings.filter(
            Q(incubation__batch_entry__batch_name__name__icontains=search_query) |
            Q(notes__icontains=search_query)
        )

    # الفلترة حسب التاريخ
    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')

    if from_date:
        hatchings = hatchings.filter(hatch_date__gte=from_date)
    if to_date:
        hatchings = hatchings.filter(hatch_date__lte=to_date)

    # الفلترة حسب اسم الدفعة
    batch_name_id = request.GET.get('batch_name')
    if batch_name_id:
        hatchings = hatchings.filter(incubation__batch_entry__batch_name_id=batch_name_id)

    # الفلترة حسب نسبة الفقس
    hatch_rate_min = request.GET.get('hatch_rate_min')
    hatch_rate_max = request.GET.get('hatch_rate_max')

    if hatch_rate_min:
        hatchings = hatchings.filter(hatch_rate__gte=float(hatch_rate_min))
    if hatch_rate_max:
        hatchings = hatchings.filter(hatch_rate__lte=float(hatch_rate_max))

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

    # إعداد قائمة الفلاتر
    batch_names = BatchName.objects.filter(is_active=True).order_by('name')

    hatching_filters = [
        {
            'name': 'batch_name',
            'label': 'اسم الدفعة',
            'type': 'select',
            'options': batch_names,
            'value': batch_name_id
        },
        {
            'name': 'hatch_rate_min',
            'label': 'نسبة الفقس (من)',
            'type': 'text',
            'placeholder': '0',
            'value': hatch_rate_min
        },
        {
            'name': 'hatch_rate_max',
            'label': 'نسبة الفقس (إلى)',
            'type': 'text',
            'placeholder': '100',
            'value': hatch_rate_max
        }
    ]

    # التحقق من نوع الطلب (عرض عادي أو تصدير)
    export_type = request.GET.get('export')
    if export_type == 'print':
        return render(request, 'hatchery/hatching_list_print.html', {
            'hatchings': hatchings,
            'current_datetime': timezone.now(),
            'search_query': search_query,
            'from_date': from_date,
            'to_date': to_date
        })

    return render(request, 'hatchery/hatching_list.html', {
        'hatchings': hatchings,
        'ready_incubations': ready_incubations,
        'hatching_filters': hatching_filters,
        'search_query': search_query,
        'from_date': from_date,
        'to_date': to_date,
        'date_filter': True
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
    customer = get_object_or_404(Customer, pk=pk)

    if request.method == 'POST':
        form = CustomerForm(request.POST, instance=customer)
        if form.is_valid():
            form.save()
            messages.success(request, 'تم تحديث بيانات العميل بنجاح')
            return redirect('hatchery:customer_detail', pk=pk)
    else:
        form = CustomerForm(instance=customer)

    return render(request, 'hatchery/customer_form.html', {'form': form})

@login_required
def customer_delete(request, pk):
    """حذف عميل"""
    customer = get_object_or_404(Customer, pk=pk)

    if request.method == 'POST':
        try:
            customer.delete()
            messages.success(request, 'تم حذف العميل بنجاح')
        except Exception as e:
            messages.error(request, f'لا يمكن حذف العميل: {str(e)}')
        return redirect('hatchery:customer_list')

    return render(request, 'hatchery/customer_confirm_delete.html', {'customer': customer})

@login_required
def culled_sale_list(request):
    """عرض قائمة مبيعات الفرزة"""
    sales = CulledSale.objects.all().order_by('-invoice_date')

    # البحث
    search_query = request.GET.get('q')
    if search_query:
        sales = sales.filter(
            Q(customer__name__icontains=search_query) |
            Q(hatching__incubation__batch_entry__batch_name__name__icontains=search_query) |
            Q(notes__icontains=search_query)
        )

    # الفلترة حسب التاريخ
    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')

    if from_date:
        sales = sales.filter(invoice_date__gte=from_date)
    if to_date:
        sales = sales.filter(invoice_date__lte=to_date)

    # الفلترة حسب اسم الدفعة
    batch_name_id = request.GET.get('batch_name')
    if batch_name_id:
        sales = sales.filter(hatching__incubation__batch_entry__batch_name_id=batch_name_id)

    # الفلترة حسب العميل
    customer_id = request.GET.get('customer')
    if customer_id:
        sales = sales.filter(customer_id=customer_id)

    # الفلترة حسب حالة الدفع
    payment_status = request.GET.get('payment_status')
    if payment_status:
        if payment_status == 'paid':
            sales = sales.filter(paid_amount__gte=F('quantity') * F('price_per_unit'))
        elif payment_status == 'partially_paid':
            sales = sales.filter(paid_amount__gt=0).exclude(paid_amount__gte=F('quantity') * F('price_per_unit'))
        elif payment_status == 'unpaid':
            sales = sales.filter(paid_amount=0)

    # الحصول على الدفعات التي لديها كتاكيت فرزة متاحة للبيع
    available_hatchings = BatchHatching.objects.filter(
        culled_count__gt=0  # لديها كتاكيت فرزة
    ).exclude(
        culled_count=0  # استبعاد الدفعات التي ليس لديها فرزة
    ).order_by('-hatch_date')

    # تصفية الدفعات التي لديها فرزة متاحة للبيع
    available_hatchings = [h for h in available_hatchings if h.available_culled_count > 0]

    # إعداد قائمة الفلاتر
    batch_names = BatchName.objects.filter(is_active=True).order_by('name')
    customers = Customer.objects.filter(is_active=True).order_by('name')

    sale_filters = [
        {
            'name': 'batch_name',
            'label': 'اسم الدفعة',
            'type': 'select',
            'options': batch_names,
            'value': batch_name_id
        },
        {
            'name': 'customer',
            'label': 'العميل',
            'type': 'select',
            'options': customers,
            'value': customer_id
        },
        {
            'name': 'payment_status',
            'label': 'حالة الدفع',
            'type': 'select',
            'options': [('paid', 'مدفوع بالكامل'), ('partially_paid', 'مدفوع جزئياً'), ('unpaid', 'غير مدفوع')],
            'value': payment_status
        }
    ]

    # التحقق من نوع الطلب (عرض عادي أو تصدير)
    export_type = request.GET.get('export')
    if export_type == 'print':
        return render(request, 'hatchery/culled_sale_list_print.html', {
            'sales': sales,
            'current_datetime': timezone.now(),
            'search_query': search_query,
            'from_date': from_date,
            'to_date': to_date
        })

    return render(request, 'hatchery/culled_sale_list.html', {
        'sales': sales,
        'available_hatchings': available_hatchings,
        'sale_filters': sale_filters,
        'search_query': search_query,
        'from_date': from_date,
        'to_date': to_date,
        'date_filter': True
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

    # البحث
    search_query = request.GET.get('q')
    if search_query:
        inventory_items = inventory_items.filter(
            Q(name__icontains=search_query) |
            Q(supplier__icontains=search_query) |
            Q(category__name__icontains=search_query) |
            Q(notes__icontains=search_query)
        )

    # الفلترة حسب التصنيف
    category_id = request.GET.get('category')
    if category_id:
        inventory_items = inventory_items.filter(category_id=category_id)

    # الفلترة حسب حالة المخزون
    stock_status = request.GET.get('stock_status')
    if stock_status == 'low':
        inventory_items = inventory_items.filter(current_stock__lte=F('minimum_stock'))
    elif stock_status == 'normal':
        inventory_items = inventory_items.filter(current_stock__gt=F('minimum_stock'))

    # إعداد قائمة الفلاتر
    categories = DisinfectantCategory.objects.all().order_by('name')

    inventory_filters = [
        {
            'name': 'category',
            'label': 'التصنيف',
            'type': 'select',
            'options': categories,
            'value': category_id
        },
        {
            'name': 'stock_status',
            'label': 'حالة المخزون',
            'type': 'select',
            'options': [
                {'id': 'low', 'name': 'منخفض'},
                {'id': 'normal', 'name': 'طبيعي'}
            ],
            'value': stock_status
        }
    ]

    # التحقق من نوع الطلب (عرض عادي أو تصدير)
    export_type = request.GET.get('export')
    if export_type == 'print':
        return render(request, 'hatchery/disinfectant_inventory_list_print.html', {
            'inventory_items': inventory_items,
            'current_datetime': timezone.now(),
            'search_query': search_query
        })
    elif export_type == 'excel':
        return export_disinfectant_inventory_excel(inventory_items)
    elif export_type == 'pdf':
        return export_disinfectant_inventory_pdf(inventory_items)

    return render(request, 'hatchery/disinfectant_inventory_list.html', {
        'inventory_items': inventory_items,
        'inventory_filters': inventory_filters,
        'search_query': search_query
    })

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

    # البحث
    search_query = request.GET.get('q')
    if search_query:
        transactions = transactions.filter(
            Q(disinfectant__name__icontains=search_query) |
            Q(disinfectant__category__name__icontains=search_query) |
            Q(notes__icontains=search_query)
        )

    # الفلترة حسب التاريخ
    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')

    if from_date:
        transactions = transactions.filter(transaction_date__gte=from_date)
    if to_date:
        transactions = transactions.filter(transaction_date__lte=to_date)

    # الفلترة حسب نوع الحركة
    transaction_type = request.GET.get('transaction_type')
    if transaction_type:
        transactions = transactions.filter(transaction_type=transaction_type)

    # الفلترة حسب المطهر
    disinfectant_id = request.GET.get('disinfectant')
    if disinfectant_id:
        transactions = transactions.filter(disinfectant_id=disinfectant_id)

    # الفلترة حسب التصنيف
    category_id = request.GET.get('category')
    if category_id:
        transactions = transactions.filter(disinfectant__category_id=category_id)

    # إعداد قائمة الفلاتر
    disinfectants = DisinfectantInventory.objects.all().order_by('name')
    categories = DisinfectantCategory.objects.all().order_by('name')

    transaction_filters = [
        {
            'name': 'transaction_type',
            'label': 'نوع الحركة',
            'type': 'select',
            'options': [
                {'id': 'receive', 'name': 'استلام'},
                {'id': 'dispense', 'name': 'صرف'}
            ],
            'value': transaction_type
        },
        {
            'name': 'disinfectant',
            'label': 'المطهر',
            'type': 'select',
            'options': disinfectants,
            'value': disinfectant_id
        },
        {
            'name': 'category',
            'label': 'التصنيف',
            'type': 'select',
            'options': categories,
            'value': category_id
        }
    ]

    # التحقق من نوع الطلب (عرض عادي أو تصدير)
    export_type = request.GET.get('export')
    if export_type == 'print':
        return render(request, 'hatchery/disinfectant_transaction_list_print.html', {
            'transactions': transactions,
            'current_datetime': timezone.now(),
            'search_query': search_query,
            'from_date': from_date,
            'to_date': to_date
        })
    elif export_type == 'excel':
        return export_disinfectant_transaction_excel(transactions)
    elif export_type == 'pdf':
        return export_disinfectant_transaction_pdf(transactions)

    return render(request, 'hatchery/disinfectant_transaction_list.html', {
        'transactions': transactions,
        'transaction_filters': transaction_filters,
        'search_query': search_query,
        'from_date': from_date,
        'to_date': to_date,
        'date_filter': True
    })

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

    # البحث
    search_query = request.GET.get('q')
    if search_query:
        distributions = distributions.filter(
            Q(hatching__incubation__batch_entry__batch_name__name__icontains=search_query) |
            Q(notes__icontains=search_query) |
            Q(distribution_items__customer__name__icontains=search_query)
        ).distinct()

    # الفلترة حسب التاريخ
    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')

    if from_date:
        distributions = distributions.filter(distribution_date__gte=from_date)
    if to_date:
        distributions = distributions.filter(distribution_date__lte=to_date)

    # الفلترة حسب اسم الدفعة
    batch_name_id = request.GET.get('batch_name')
    if batch_name_id:
        distributions = distributions.filter(hatching__incubation__batch_entry__batch_name_id=batch_name_id)

    # الفلترة حسب العميل
    customer_id = request.GET.get('customer')
    if customer_id:
        distributions = distributions.filter(distribution_items__customer_id=customer_id).distinct()

    # الحصول على الدفعات التي خرجت اليوم
    today = timezone.now().date()
    today_hatchings = BatchHatching.objects.filter(
        hatch_date=today
    ).order_by('-hatch_date')

    # إعداد قائمة الفلاتر
    batch_names = BatchName.objects.filter(is_active=True).order_by('name')
    customers = Customer.objects.filter(is_active=True).order_by('name')

    distribution_filters = [
        {
            'name': 'batch_name',
            'label': 'اسم الدفعة',
            'type': 'select',
            'options': batch_names,
            'value': batch_name_id
        },
        {
            'name': 'customer',
            'label': 'العميل',
            'type': 'select',
            'options': customers,
            'value': customer_id
        }
    ]

    # التحقق من نوع الطلب (عرض عادي أو تصدير)
    export_type = request.GET.get('export')
    if export_type == 'print':
        # الحصول على عناصر التوزيع لكل توزيع
        for distribution in distributions:
            distribution.items = distribution.distribution_items.all()

        return render(request, 'hatchery/distribution_list_print.html', {
            'distributions': distributions,
            'current_datetime': timezone.now(),
            'search_query': search_query,
            'from_date': from_date,
            'to_date': to_date
        })

    return render(request, 'hatchery/distribution_list.html', {
        'distributions': distributions,
        'today_hatchings': today_hatchings,
        'distribution_filters': distribution_filters,
        'search_query': search_query,
        'from_date': from_date,
        'to_date': to_date,
        'date_filter': True
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

# Reports views
@login_required
def reports_home(request):
    """الصفحة الرئيسية للتقارير"""
    context = {
        'today': timezone.now().date()
    }
    return render(request, 'hatchery/reports_home.html', context)


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

    # استرجاع إعدادات الطباعة
    settings = get_print_settings(request)
    show_created_today = settings['show_created_today'] == '1'

    # الدفعات الواردة المسجلة اليوم
    if show_created_today:
        # عرض الدفعات التي تم تسجيلها اليوم بغض النظر عن تاريخ الدخول
        today_entries = BatchEntry.objects.filter(
            created_at__date=report_date
        ).order_by('-date')
    else:
        # عرض الدفعات التي تاريخ دخولها هو اليوم فقط
        today_entries = BatchEntry.objects.filter(
            date=report_date
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
        return export_daily_report_excel(context, request=request)
    elif export_type == 'pdf':
        return export_daily_report_pdf(context, request=request)
    elif export_type == 'print':
        # إضافة التاريخ والوقت الحاليين إلى السياق
        context['current_datetime'] = timezone.now()

        # إضافة إعدادات الطباعة إلى السياق
        settings = get_print_settings(request)
        context['show_created_today'] = settings['show_created_today'] == '1'
        context['show_price_in_distribution'] = settings['show_price_in_distribution'] == '1'
        context['show_price_in_culled_sales'] = settings['show_price_in_culled_sales'] == '1'
        context['hide_empty_sections'] = settings['hide_empty_sections'] == '1'

        # حساب إجمالي المبلغ المدفوع من مبيعات الفرزة
        context['total_culled_sales_paid'] = today_culled_sales.aggregate(total=Sum('paid_amount'))['total'] or 0

        return render(request, 'hatchery/daily_report_print.html', context)

    return render(request, 'hatchery/daily_report.html', context)


def export_daily_report_excel(context, request=None):
    """تصدير التقرير اليومي بصيغة Excel"""
    # استرجاع إعدادات الطباعة
    settings = get_print_settings(request) if request else {
        'show_created_today': '1',
        'hide_empty_sections': '0',
        'show_price_in_distribution': '0',
        'show_price_in_culled_sales': '1',
    }

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


@login_required
def print_settings(request):
    """صفحة إعدادات الطباعة والتصدير"""
    # استرجاع الإعدادات المحفوظة من الجلسة
    saved_settings = request.session.get('print_settings', {})

    if request.method == 'POST':
        form = PrintSettingsForm(request.POST)
        if form.is_valid():
            # حفظ الإعدادات في الجلسة
            settings_data = {
                'show_created_today': '1' if form.cleaned_data['show_created_today'] else '0',
                'hide_empty_sections': '1' if form.cleaned_data['hide_empty_sections'] else '0',
                'show_price_in_distribution': '1' if form.cleaned_data['show_price_in_distribution'] else '0',
                'show_price_in_culled_sales': '1' if form.cleaned_data['show_price_in_culled_sales'] else '0',
            }
            request.session['print_settings'] = settings_data
            messages.success(request, 'تم حفظ إعدادات الطباعة بنجاح')

            # إعادة توجيه المستخدم إلى الصفحة السابقة إذا كانت موجودة
            next_url = request.POST.get('next', 'hatchery:reports')
            return redirect(next_url)
    else:
        # تعبئة النموذج بالإعدادات المحفوظة
        initial_data = {
            'show_created_today': saved_settings.get('show_created_today') == '1',
            'hide_empty_sections': saved_settings.get('hide_empty_sections') == '1',
            'show_price_in_distribution': saved_settings.get('show_price_in_distribution') == '1',
            'show_price_in_culled_sales': saved_settings.get('show_price_in_culled_sales') == '1',
        }
        form = PrintSettingsForm(initial=initial_data)

    return render(request, 'hatchery/print_settings.html', {
        'form': form,
        'next': request.GET.get('next', 'hatchery:reports')
    })


def get_print_settings(request):
    """استرجاع إعدادات الطباعة من الجلسة فقط"""
    # استرجاع الإعدادات المحفوظة من الجلسة
    saved_settings = request.session.get('print_settings', {})

    # استخدام الإعدادات المحفوظة فقط مع القيم الافتراضية إذا لم تكن موجودة
    settings = {
        'show_created_today': saved_settings.get('show_created_today', '1'),
        'hide_empty_sections': saved_settings.get('hide_empty_sections', '0'),
        'show_price_in_distribution': saved_settings.get('show_price_in_distribution', '0'),
        'show_price_in_culled_sales': saved_settings.get('show_price_in_culled_sales', '1'),
    }

    return settings


def export_daily_report_pdf(context, request=None):
    """تصدير التقرير اليومي بصيغة PDF"""
    # بدلاً من استخدام مكتبات خارجية لتحويل HTML إلى PDF،
    # سنقوم بإعادة توجيه المستخدم إلى صفحة الطباعة مع معلمة إضافية لتنزيل PDF تلقائيًا

    # إنشاء عنوان URL لصفحة الطباعة مع المعلمات المطلوبة
    print_url = f"/hatchery/reports/daily/?date={context['report_date'].strftime('%Y-%m-%d')}&export=print&auto_download_pdf=1"

    # إعادة توجيه المستخدم إلى صفحة الطباعة - سيتم استخدام الإعدادات المحفوظة في الجلسة تلقائيًا
    return redirect(print_url)


def export_disinfectant_inventory_excel(inventory_items):
    """تصدير مخزون المطهرات بصيغة Excel"""
    # إنشاء ملف Excel في الذاكرة
    output = io.BytesIO()
    workbook = xlsxwriter.Workbook(output)
    worksheet = workbook.add_worksheet('مخزون المطهرات')

    # تعيين اتجاه الورقة من اليمين إلى اليسار
    worksheet.right_to_left()

    # تنسيق العناوين
    header_format = workbook.add_format({
        'bold': True,
        'align': 'center',
        'valign': 'vcenter',
        'bg_color': '#4472C4',
        'font_color': 'white',
        'border': 1
    })

    # تنسيق البيانات
    cell_format = workbook.add_format({
        'align': 'center',
        'valign': 'vcenter',
        'border': 1
    })

    # تنسيق الخلايا الرقمية
    number_format = workbook.add_format({
        'align': 'center',
        'valign': 'vcenter',
        'border': 1,
        'num_format': '#,##0.00'
    })

    # تنسيق حالة المخزون
    low_stock_format = workbook.add_format({
        'align': 'center',
        'valign': 'vcenter',
        'border': 1,
        'bg_color': '#FF9999'
    })

    normal_stock_format = workbook.add_format({
        'align': 'center',
        'valign': 'vcenter',
        'border': 1,
        'bg_color': '#99FF99'
    })

    # العناوين
    headers = [
        'ملاحظات',
        'حالة المخزون',
        'الحد الأدنى',
        'المخزون الحالي',
        'وحدة القياس',
        'المورد',
        'اسم المطهر',
        'التصنيف'
    ]

    # كتابة العناوين
    for col, header in enumerate(headers):
        worksheet.write(0, col, header, header_format)

    # كتابة البيانات
    for row, item in enumerate(inventory_items, start=1):
        # تقريب الأرقام إذا كانت الأرقام بعد الفاصلة أصفار
        current_stock = float(item.current_stock)
        minimum_stock = float(item.minimum_stock)

        # التحقق مما إذا كان الرقم صحيحًا
        if current_stock == int(current_stock):
            current_stock = int(current_stock)
        if minimum_stock == int(minimum_stock):
            minimum_stock = int(minimum_stock)

        worksheet.write(row, 0, item.notes or '-', cell_format)

        # حالة المخزون
        if item.is_low_stock:
            worksheet.write(row, 1, 'منخفض', low_stock_format)
        else:
            worksheet.write(row, 1, 'طبيعي', normal_stock_format)

        worksheet.write(row, 2, minimum_stock, number_format)
        worksheet.write(row, 3, current_stock, number_format)
        worksheet.write(row, 4, item.unit, cell_format)
        worksheet.write(row, 5, item.supplier or '-', cell_format)
        worksheet.write(row, 6, item.name, cell_format)
        worksheet.write(row, 7, item.category.name, cell_format)

    # ضبط عرض الأعمدة
    for col in range(len(headers)):
        worksheet.set_column(col, col, 20)

    # إغلاق الملف
    workbook.close()

    # إعادة مؤشر الملف إلى البداية
    output.seek(0)

    # إنشاء استجابة HTTP مع ملف Excel
    response = HttpResponse(
        output.read(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename=disinfectant_inventory.xlsx'

    return response


def export_disinfectant_inventory_pdf(inventory_items):
    """تصدير مخزون المطهرات بصيغة PDF"""
    # بدلاً من استخدام مكتبات خارجية لتحويل HTML إلى PDF،
    # سنقوم بإعادة توجيه المستخدم إلى صفحة الطباعة مع معلمة إضافية لتنزيل PDF تلقائيًا

    # إنشاء عنوان URL لصفحة الطباعة مع المعلمات المطلوبة
    print_url = "/hatchery/disinfectant-inventory/?export=print&auto_download_pdf=1"

    # إضافة معلمات البحث والفلترة إذا كانت موجودة
    # (هذا سيتم تنفيذه في المستقبل عند الحاجة)

    # إعادة توجيه المستخدم إلى صفحة الطباعة
    return redirect(print_url)


def export_disinfectant_transaction_excel(transactions):
    """تصدير حركات المطهرات بصيغة Excel"""
    # إنشاء ملف Excel في الذاكرة
    output = io.BytesIO()
    workbook = xlsxwriter.Workbook(output)
    worksheet = workbook.add_worksheet('حركات المطهرات')

    # تعيين اتجاه الورقة من اليمين إلى اليسار
    worksheet.right_to_left()

    # تنسيق العناوين
    header_format = workbook.add_format({
        'bold': True,
        'align': 'center',
        'valign': 'vcenter',
        'bg_color': '#4472C4',
        'font_color': 'white',
        'border': 1
    })

    # تنسيق البيانات
    cell_format = workbook.add_format({
        'align': 'center',
        'valign': 'vcenter',
        'border': 1
    })

    # تنسيق الخلايا الرقمية
    number_format = workbook.add_format({
        'align': 'center',
        'valign': 'vcenter',
        'border': 1,
        'num_format': '#,##0.00'
    })

    # تنسيق نوع الحركة
    receive_format = workbook.add_format({
        'align': 'center',
        'valign': 'vcenter',
        'border': 1,
        'bg_color': '#99FF99'
    })

    dispense_format = workbook.add_format({
        'align': 'center',
        'valign': 'vcenter',
        'border': 1,
        'bg_color': '#FFCC99'
    })

    # العناوين
    headers = [
        'ملاحظات',
        'وحدة القياس',
        'الكمية',
        'نوع الحركة',
        'التصنيف',
        'المطهر',
        'تاريخ الحركة'
    ]

    # كتابة العناوين
    for col, header in enumerate(headers):
        worksheet.write(0, col, header, header_format)

    # كتابة البيانات
    for row, transaction in enumerate(transactions, start=1):
        # تقريب الأرقام إذا كانت الأرقام بعد الفاصلة أصفار
        quantity = float(transaction.quantity)

        # التحقق مما إذا كان الرقم صحيحًا
        if quantity == int(quantity):
            quantity = int(quantity)

        worksheet.write(row, 0, transaction.notes or '-', cell_format)
        worksheet.write(row, 1, transaction.disinfectant.unit, cell_format)
        worksheet.write(row, 2, quantity, number_format)

        # نوع الحركة
        if transaction.transaction_type == 'receive':
            worksheet.write(row, 3, 'استلام', receive_format)
        else:
            worksheet.write(row, 3, 'صرف', dispense_format)

        worksheet.write(row, 4, transaction.disinfectant.category.name, cell_format)
        worksheet.write(row, 5, transaction.disinfectant.name, cell_format)
        worksheet.write(row, 6, transaction.transaction_date.strftime('%Y-%m-%d'), cell_format)

    # ضبط عرض الأعمدة
    for col in range(len(headers)):
        worksheet.set_column(col, col, 20)

    # إغلاق الملف
    workbook.close()

    # إعادة مؤشر الملف إلى البداية
    output.seek(0)

    # إنشاء استجابة HTTP مع ملف Excel
    response = HttpResponse(
        output.read(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename=disinfectant_transactions.xlsx'

    return response


def export_disinfectant_transaction_pdf(transactions):
    """تصدير حركات المطهرات بصيغة PDF"""
    # بدلاً من استخدام مكتبات خارجية لتحويل HTML إلى PDF،
    # سنقوم بإعادة توجيه المستخدم إلى صفحة الطباعة مع معلمة إضافية لتنزيل PDF تلقائيًا

    # إنشاء عنوان URL لصفحة الطباعة مع المعلمات المطلوبة
    print_url = "/hatchery/disinfectant-transactions/?export=print&auto_download_pdf=1"

    # إضافة معلمات البحث والفلترة إذا كانت موجودة
    # (هذا سيتم تنفيذه في المستقبل عند الحاجة)

    # إعادة توجيه المستخدم إلى صفحة الطباعة
    return redirect(print_url)