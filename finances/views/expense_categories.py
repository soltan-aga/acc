from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q

from ..models import ExpenseCategory
from ..forms import ExpenseCategoryForm

@login_required
def expense_category_list(request):
    """عرض قائمة أقسام المصروفات"""
    categories = ExpenseCategory.objects.all()

    # البحث
    search_query = request.GET.get('q')
    if search_query:
        categories = categories.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query)
        )

    return render(request, 'finances/expense_category/list.html', {
        'categories': categories,
        'search_query': search_query
    })

@login_required
def expense_category_add(request):
    """إضافة قسم مصروفات جديد"""
    if request.method == 'POST':
        form = ExpenseCategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'تم إضافة قسم المصروفات بنجاح')
            return redirect('expense_category_list')
    else:
        form = ExpenseCategoryForm()

    return render(request, 'finances/expense_category/form.html', {
        'form': form,
        'title': 'إضافة قسم مصروفات جديد'
    })

@login_required
def expense_category_edit(request, pk):
    """تعديل قسم مصروفات"""
    category = get_object_or_404(ExpenseCategory, pk=pk)

    if request.method == 'POST':
        form = ExpenseCategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, 'تم تعديل قسم المصروفات بنجاح')
            return redirect('expense_category_list')
    else:
        form = ExpenseCategoryForm(instance=category)

    return render(request, 'finances/expense_category/form.html', {
        'form': form,
        'title': 'تعديل قسم مصروفات',
        'category': category
    })

@login_required
def expense_category_delete(request, pk):
    """حذف قسم مصروفات"""
    category = get_object_or_404(ExpenseCategory, pk=pk)

    # التحقق من وجود مصروفات مرتبطة بهذا القسم
    if category.expenses.exists():
        messages.error(request, 'لا يمكن حذف هذا القسم لوجود مصروفات مرتبطة به')
        return redirect('expense_category_list')

    # التحقق من وجود أقسام فرعية
    if category.children.exists():
        messages.error(request, 'لا يمكن حذف هذا القسم لوجود أقسام فرعية مرتبطة به')
        return redirect('expense_category_list')

    if request.method == 'POST':
        category.delete()
        messages.success(request, 'تم حذف قسم المصروفات بنجاح')
        return redirect('expense_category_list')

    return render(request, 'finances/expense_category/delete.html', {
        'category': category
    })
