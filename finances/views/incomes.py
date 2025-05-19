from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from ..models import Income, IncomeCategory
from ..forms import IncomeForm
from core.models import Safe

@login_required
def income_list(request):
    """عرض قائمة الإيرادات"""
    incomes = Income.objects.all().order_by('-date')

    # تصفية حسب القسم
    category_id = request.GET.get('category')
    if category_id:
        incomes = incomes.filter(category_id=category_id)

    # تصفية حسب الخزنة
    safe_id = request.GET.get('safe')
    if safe_id:
        incomes = incomes.filter(safe_id=safe_id)

    # تصفية حسب حالة الترحيل
    is_posted = request.GET.get('is_posted')
    if is_posted == 'yes':
        incomes = incomes.filter(is_posted=True)
    elif is_posted == 'no':
        incomes = incomes.filter(is_posted=False)

    # البحث
    search_query = request.GET.get('q')
    if search_query:
        incomes = incomes.filter(
            Q(number__icontains=search_query) |
            Q(payer__icontains=search_query) |
            Q(notes__icontains=search_query) |
            Q(reference_number__icontains=search_query)
        )

    # قائمة الأقسام والخزن للتصفية
    categories = IncomeCategory.objects.all()
    safes = Safe.objects.all()

    return render(request, 'finances/income/list.html', {
        'incomes': incomes,
        'categories': categories,
        'safes': safes,
        'selected_category': category_id,
        'selected_safe': safe_id,
        'selected_is_posted': is_posted,
        'search_query': search_query
    })

@login_required
def income_add(request):
    """إضافة إيراد جديد"""
    # إنشاء رقم مستند جديد
    last_income = Income.objects.order_by('-id').first()
    new_number = f"INC-{1:04d}" if not last_income else f"INC-{int(last_income.number.split('-')[1]) + 1:04d}"

    if request.method == 'POST':
        form = IncomeForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                income = form.save(commit=False)
                # دائماً قم بتعيين رقم مستند جديد
                income.number = new_number
                income.save()
                messages.success(request, 'تم إضافة الإيراد بنجاح')
                return redirect('income_list')
    else:
        form = IncomeForm(initial={
            'date': timezone.now()
        })

    return render(request, 'finances/income/form.html', {
        'form': form,
        'title': 'إضافة إيراد جديد'
    })

@login_required
def income_edit(request, pk):
    """تعديل إيراد"""
    income = get_object_or_404(Income, pk=pk)

    # إذا كان الإيراد مرحل، قم بإلغاء الترحيل أولاً
    was_posted = False
    if income.is_posted:
        was_posted = True
        income.unpost_income()

    if request.method == 'POST':
        form = IncomeForm(request.POST, instance=income)
        if form.is_valid():
            with transaction.atomic():
                income = form.save()
                # إعادة ترحيل الإيراد إذا كان مرحلاً قبل التعديل
                if was_posted:
                    income.post_income()
                messages.success(request, 'تم تعديل الإيراد بنجاح')
                return redirect('income_detail', pk=income.pk)
    else:
        form = IncomeForm(instance=income)

    return render(request, 'finances/income/form.html', {
        'form': form,
        'title': 'تعديل إيراد',
        'income': income
    })

@login_required
def income_detail(request, pk):
    """عرض تفاصيل الإيراد"""
    income = get_object_or_404(Income, pk=pk)

    return render(request, 'finances/income/detail.html', {
        'income': income
    })

@login_required
def income_delete(request, pk):
    """حذف إيراد"""
    income = get_object_or_404(Income, pk=pk)

    # إذا كان الإيراد مرحل، قم بإلغاء الترحيل أولاً
    if income.is_posted:
        income.unpost_income()

    if request.method == 'POST':
        income.delete()
        messages.success(request, 'تم حذف الإيراد بنجاح')
        return redirect('income_list')

    return render(request, 'finances/income/delete.html', {
        'income': income
    })

@login_required
def income_post(request, pk):
    """ترحيل الإيراد"""
    income = get_object_or_404(Income, pk=pk)

    if income.is_posted:
        messages.error(request, 'الإيراد مرحل بالفعل')
        return redirect('income_detail', pk=income.pk)

    success = income.post_income()

    if success:
        messages.success(request, 'تم ترحيل الإيراد بنجاح')
    else:
        messages.error(request, 'حدث خطأ أثناء ترحيل الإيراد')

    return redirect('income_detail', pk=income.pk)

@login_required
def income_unpost(request, pk):
    """إلغاء ترحيل الإيراد"""
    income = get_object_or_404(Income, pk=pk)

    if not income.is_posted:
        messages.error(request, 'الإيراد غير مرحل بالفعل')
        return redirect('income_detail', pk=income.pk)

    success = income.unpost_income()

    if success:
        messages.success(request, 'تم إلغاء ترحيل الإيراد بنجاح')
    else:
        messages.error(request, 'حدث خطأ أثناء إلغاء ترحيل الإيراد')

    return redirect('income_detail', pk=income.pk)
