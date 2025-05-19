from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q

from ..models import IncomeCategory
from ..forms import IncomeCategoryForm

@login_required
def income_category_list(request):
    """عرض قائمة أقسام الإيرادات"""
    categories = IncomeCategory.objects.all()

    # البحث
    search_query = request.GET.get('q')
    if search_query:
        categories = categories.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query)
        )

    return render(request, 'finances/income_category/list.html', {
        'categories': categories,
        'search_query': search_query
    })

@login_required
def income_category_add(request):
    """إضافة قسم إيرادات جديد"""
    if request.method == 'POST':
        form = IncomeCategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'تم إضافة قسم الإيرادات بنجاح')
            return redirect('income_category_list')
    else:
        form = IncomeCategoryForm()

    return render(request, 'finances/income_category/form.html', {
        'form': form,
        'title': 'إضافة قسم إيرادات جديد'
    })

@login_required
def income_category_edit(request, pk):
    """تعديل قسم إيرادات"""
    category = get_object_or_404(IncomeCategory, pk=pk)

    if request.method == 'POST':
        form = IncomeCategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, 'تم تعديل قسم الإيرادات بنجاح')
            return redirect('income_category_list')
    else:
        form = IncomeCategoryForm(instance=category)

    return render(request, 'finances/income_category/form.html', {
        'form': form,
        'title': 'تعديل قسم إيرادات',
        'category': category
    })

@login_required
def income_category_delete(request, pk):
    """حذف قسم إيرادات"""
    category = get_object_or_404(IncomeCategory, pk=pk)

    # التحقق من وجود إيرادات مرتبطة بهذا القسم
    if category.incomes.exists():
        messages.error(request, 'لا يمكن حذف هذا القسم لوجود إيرادات مرتبطة به')
        return redirect('income_category_list')

    # التحقق من وجود أقسام فرعية
    if category.children.exists():
        messages.error(request, 'لا يمكن حذف هذا القسم لوجود أقسام فرعية مرتبطة به')
        return redirect('income_category_list')

    if request.method == 'POST':
        category.delete()
        messages.success(request, 'تم حذف قسم الإيرادات بنجاح')
        return redirect('income_category_list')

    return render(request, 'finances/income_category/delete.html', {
        'category': category
    })
