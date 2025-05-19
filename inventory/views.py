from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Sum
from .models import Supplier, DisinfectantCategory, Disinfectant, DisinfectantReceived, DisinfectantIssued
from .forms import SupplierForm, DisinfectantCategoryForm, DisinfectantForm, DisinfectantReceivedForm, DisinfectantIssuedForm

# Create your views here.

@login_required
def home(request):
    """الصفحة الرئيسية لتطبيق المخزون"""
    # إحصائيات عامة
    disinfectants_count = Disinfectant.objects.count()
    suppliers_count = Supplier.objects.count()
    categories_count = DisinfectantCategory.objects.count()

    # المطهرات منخفضة المخزون
    low_stock_disinfectants = []
    for disinfectant in Disinfectant.objects.filter(is_active=True):
        if disinfectant.stock_status in ["منخفض", "نفذ"]:
            low_stock_disinfectants.append(disinfectant)

    context = {
        'disinfectants_count': disinfectants_count,
        'suppliers_count': suppliers_count,
        'categories_count': categories_count,
        'low_stock_disinfectants': low_stock_disinfectants,
    }

    return render(request, 'inventory/home.html', context)

# Placeholder views for inventory app
# These will be implemented with actual functionality later

@login_required
def supplier_list(request):
    """عرض قائمة الموردين"""
    suppliers = Supplier.objects.all().order_by('name')
    return render(request, 'inventory/supplier_list.html', {'suppliers': suppliers})

@login_required
def supplier_create(request):
    """إنشاء مورد جديد"""
    # Placeholder - will be implemented later
    messages.success(request, 'تم إنشاء المورد بنجاح')
    return redirect('inventory:supplier_list')

@login_required
def supplier_detail(request, pk):
    """عرض تفاصيل مورد"""
    supplier = get_object_or_404(Supplier, pk=pk)
    return render(request, 'inventory/supplier_detail.html', {'supplier': supplier})

@login_required
def supplier_update(request, pk):
    """تحديث بيانات مورد"""
    # Placeholder - will be implemented later
    messages.success(request, 'تم تحديث بيانات المورد بنجاح')
    return redirect('inventory:supplier_detail', pk=pk)

@login_required
def supplier_delete(request, pk):
    """حذف مورد"""
    # Placeholder - will be implemented later
    messages.success(request, 'تم حذف المورد بنجاح')
    return redirect('inventory:supplier_list')

@login_required
def category_list(request):
    """عرض قائمة تصنيفات المطهرات"""
    categories = DisinfectantCategory.objects.all().order_by('name')
    return render(request, 'inventory/category_list.html', {'categories': categories})

@login_required
def category_create(request):
    """إنشاء تصنيف جديد"""
    # Placeholder - will be implemented later
    messages.success(request, 'تم إنشاء التصنيف بنجاح')
    return redirect('inventory:category_list')

@login_required
def category_detail(request, pk):
    """عرض تفاصيل تصنيف"""
    category = get_object_or_404(DisinfectantCategory, pk=pk)
    return render(request, 'inventory/category_detail.html', {'category': category})

@login_required
def category_update(request, pk):
    """تحديث بيانات تصنيف"""
    # Placeholder - will be implemented later
    messages.success(request, 'تم تحديث بيانات التصنيف بنجاح')
    return redirect('inventory:category_detail', pk=pk)

@login_required
def category_delete(request, pk):
    """حذف تصنيف"""
    # Placeholder - will be implemented later
    messages.success(request, 'تم حذف التصنيف بنجاح')
    return redirect('inventory:category_list')

@login_required
def disinfectant_list(request):
    """عرض قائمة المطهرات"""
    disinfectants = Disinfectant.objects.all().order_by('name')
    return render(request, 'inventory/disinfectant_list.html', {'disinfectants': disinfectants})

@login_required
def disinfectant_create(request):
    """إنشاء مطهر جديد"""
    if request.method == 'POST':
        form = DisinfectantForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'تم إنشاء المطهر بنجاح')
            return redirect('inventory:disinfectant_list')
    else:
        form = DisinfectantForm()

    return render(request, 'inventory/disinfectant_form.html', {'form': form})

@login_required
def disinfectant_detail(request, pk):
    """عرض تفاصيل مطهر"""
    disinfectant = get_object_or_404(Disinfectant, pk=pk)
    return render(request, 'inventory/disinfectant_detail.html', {'disinfectant': disinfectant})

@login_required
def disinfectant_update(request, pk):
    """تحديث بيانات مطهر"""
    # Placeholder - will be implemented later
    messages.success(request, 'تم تحديث بيانات المطهر بنجاح')
    return redirect('inventory:disinfectant_detail', pk=pk)

@login_required
def disinfectant_delete(request, pk):
    """حذف مطهر"""
    # Placeholder - will be implemented later
    messages.success(request, 'تم حذف المطهر بنجاح')
    return redirect('inventory:disinfectant_list')

@login_required
def received_list(request):
    """عرض قائمة المطهرات الواردة"""
    received_items = DisinfectantReceived.objects.all().order_by('-date')
    return render(request, 'inventory/received_list.html', {'received_items': received_items})

@login_required
def received_create(request, disinfectant_id):
    """إنشاء وارد جديد"""
    disinfectant = get_object_or_404(Disinfectant, pk=disinfectant_id)

    if request.method == 'POST':
        form = DisinfectantReceivedForm(request.POST, disinfectant_id=disinfectant_id)
        if form.is_valid():
            form.save()
            messages.success(request, 'تم تسجيل الوارد بنجاح')
            return redirect('inventory:received_list')
    else:
        form = DisinfectantReceivedForm(disinfectant_id=disinfectant_id)

    return render(request, 'inventory/received_form.html', {'form': form, 'disinfectant': disinfectant})

@login_required
def received_detail(request, pk):
    """عرض تفاصيل وارد"""
    received = get_object_or_404(DisinfectantReceived, pk=pk)
    return render(request, 'inventory/received_detail.html', {'received': received})

@login_required
def received_update(request, pk):
    """تحديث بيانات وارد"""
    # Placeholder - will be implemented later
    messages.success(request, 'تم تحديث بيانات الوارد بنجاح')
    return redirect('inventory:received_detail', pk=pk)

@login_required
def received_delete(request, pk):
    """حذف وارد"""
    # Placeholder - will be implemented later
    messages.success(request, 'تم حذف الوارد بنجاح')
    return redirect('inventory:received_list')

@login_required
def issued_list(request):
    """عرض قائمة المطهرات المنصرفة"""
    issued_items = DisinfectantIssued.objects.all().order_by('-date')
    return render(request, 'inventory/issued_list.html', {'issued_items': issued_items})

@login_required
def issued_create(request, disinfectant_id):
    """إنشاء منصرف جديد"""
    disinfectant = get_object_or_404(Disinfectant, pk=disinfectant_id)

    if request.method == 'POST':
        form = DisinfectantIssuedForm(request.POST, disinfectant_id=disinfectant_id)
        if form.is_valid():
            form.save()
            messages.success(request, 'تم تسجيل المنصرف بنجاح')
            return redirect('inventory:issued_list')
    else:
        form = DisinfectantIssuedForm(disinfectant_id=disinfectant_id)

    return render(request, 'inventory/issued_form.html', {'form': form, 'disinfectant': disinfectant})

@login_required
def issued_detail(request, pk):
    """عرض تفاصيل منصرف"""
    issued = get_object_or_404(DisinfectantIssued, pk=pk)
    return render(request, 'inventory/issued_detail.html', {'issued': issued})

@login_required
def issued_update(request, pk):
    """تحديث بيانات منصرف"""
    # Placeholder - will be implemented later
    messages.success(request, 'تم تحديث بيانات المنصرف بنجاح')
    return redirect('inventory:issued_detail', pk=pk)

@login_required
def issued_delete(request, pk):
    """حذف منصرف"""
    # Placeholder - will be implemented later
    messages.success(request, 'تم حذف المنصرف بنجاح')
    return redirect('inventory:issued_list')
