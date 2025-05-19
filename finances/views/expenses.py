from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from ..models import Expense, ExpenseCategory
from ..forms import ExpenseForm
from core.models import Safe

@login_required
def expense_list(request):
    """عرض قائمة المصروفات"""
    expenses = Expense.objects.all().order_by('-date')

    # تصفية حسب القسم
    category_id = request.GET.get('category')
    if category_id:
        expenses = expenses.filter(category_id=category_id)

    # تصفية حسب الخزنة
    safe_id = request.GET.get('safe')
    if safe_id:
        expenses = expenses.filter(safe_id=safe_id)

    # تصفية حسب حالة الترحيل
    is_posted = request.GET.get('is_posted')
    if is_posted == 'yes':
        expenses = expenses.filter(is_posted=True)
    elif is_posted == 'no':
        expenses = expenses.filter(is_posted=False)

    # البحث
    search_query = request.GET.get('q')
    if search_query:
        expenses = expenses.filter(
            Q(number__icontains=search_query) |
            Q(payee__icontains=search_query) |
            Q(notes__icontains=search_query) |
            Q(reference_number__icontains=search_query)
        )

    # قائمة الأقسام والخزن للتصفية
    categories = ExpenseCategory.objects.all()
    safes = Safe.objects.all()

    # إعداد قائمة الفلاتر للقالب الجزئي
    expense_filters = [
        {
            'name': 'category',
            'label': 'القسم',
            'type': 'select',
            'options': categories,
            'value': category_id
        },
        {
            'name': 'safe',
            'label': 'الخزنة',
            'type': 'select',
            'options': safes,
            'value': safe_id
        },
        {
            'name': 'is_posted',
            'label': 'حالة الترحيل',
            'type': 'select',
            'options': [('yes', 'مرحل'), ('no', 'غير مرحل')],
            'value': is_posted
        }
    ]

    return render(request, 'finances/expense/list.html', {
        'expenses': expenses,
        'expense_filters': expense_filters,
        'search_query': search_query
    })

@login_required
def expense_add(request):
    """إضافة مصروف جديد"""
    # إنشاء رقم مستند جديد
    last_expense = Expense.objects.order_by('-id').first()
    new_number = f"EXP-{1:04d}" if not last_expense else f"EXP-{int(last_expense.number.split('-')[1]) + 1:04d}"

    if request.method == 'POST':
        form = ExpenseForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                expense = form.save(commit=False)
                # دائماً قم بتعيين رقم مستند جديد
                expense.number = new_number
                expense.save()
                messages.success(request, 'تم إضافة المصروف بنجاح')
                return redirect('expense_list')
    else:
        form = ExpenseForm(initial={
            'date': timezone.now()
        })

    return render(request, 'finances/expense/form.html', {
        'form': form,
        'title': 'إضافة مصروف جديد'
    })

@login_required
def expense_edit(request, pk):
    """تعديل مصروف"""
    expense = get_object_or_404(Expense, pk=pk)

    # إذا كان المصروف مرحل، قم بإلغاء الترحيل أولاً
    was_posted = False
    if expense.is_posted:
        was_posted = True
        expense.unpost_expense()

    if request.method == 'POST':
        form = ExpenseForm(request.POST, instance=expense)
        if form.is_valid():
            with transaction.atomic():
                expense = form.save()
                # إعادة ترحيل المصروف إذا كان مرحلاً قبل التعديل
                if was_posted:
                    expense.post_expense()
                messages.success(request, 'تم تعديل المصروف بنجاح')
                return redirect('expense_detail', pk=expense.pk)
    else:
        form = ExpenseForm(instance=expense)

    return render(request, 'finances/expense/form.html', {
        'form': form,
        'title': 'تعديل مصروف',
        'expense': expense
    })

@login_required
def expense_detail(request, pk):
    """عرض تفاصيل المصروف"""
    expense = get_object_or_404(Expense, pk=pk)

    return render(request, 'finances/expense/detail.html', {
        'expense': expense
    })

@login_required
def expense_delete(request, pk):
    """حذف مصروف"""
    expense = get_object_or_404(Expense, pk=pk)

    # إذا كان المصروف مرحل، قم بإلغاء الترحيل أولاً
    if expense.is_posted:
        expense.unpost_expense()

    if request.method == 'POST':
        expense.delete()
        messages.success(request, 'تم حذف المصروف بنجاح')
        return redirect('expense_list')

    return render(request, 'finances/expense/delete.html', {
        'expense': expense
    })

@login_required
def expense_post(request, pk):
    """ترحيل المصروف"""
    expense = get_object_or_404(Expense, pk=pk)

    if expense.is_posted:
        messages.error(request, 'المصروف مرحل بالفعل')
        return redirect('expense_detail', pk=expense.pk)

    success = expense.post_expense()

    if success:
        messages.success(request, 'تم ترحيل المصروف بنجاح')
    else:
        messages.error(request, 'حدث خطأ أثناء ترحيل المصروف')

    return redirect('expense_detail', pk=expense.pk)

@login_required
def expense_unpost(request, pk):
    """إلغاء ترحيل المصروف"""
    expense = get_object_or_404(Expense, pk=pk)

    if not expense.is_posted:
        messages.error(request, 'المصروف غير مرحل بالفعل')
        return redirect('expense_detail', pk=expense.pk)

    success = expense.unpost_expense()

    if success:
        messages.success(request, 'تم إلغاء ترحيل المصروف بنجاح')
    else:
        messages.error(request, 'حدث خطأ أثناء إلغاء ترحيل المصروف')

    return redirect('expense_detail', pk=expense.pk)
