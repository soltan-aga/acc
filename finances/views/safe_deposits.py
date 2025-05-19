from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from ..models import SafeDeposit
from ..forms import SafeDepositForm
from core.models import Safe

@login_required
def safe_deposit_list(request):
    """عرض قائمة الإيداعات في الخزنة"""
    deposits = SafeDeposit.objects.all().order_by('-date')

    # تصفية حسب الخزنة
    safe_id = request.GET.get('safe')
    if safe_id:
        deposits = deposits.filter(safe_id=safe_id)

    # تصفية حسب حالة الترحيل
    is_posted = request.GET.get('is_posted')
    if is_posted == 'yes':
        deposits = deposits.filter(is_posted=True)
    elif is_posted == 'no':
        deposits = deposits.filter(is_posted=False)

    # البحث
    search_query = request.GET.get('q')
    if search_query:
        deposits = deposits.filter(
            Q(number__icontains=search_query) |
            Q(source__icontains=search_query) |
            Q(notes__icontains=search_query) |
            Q(reference_number__icontains=search_query)
        )

    # قائمة الخزن للتصفية
    safes = Safe.objects.all()

    return render(request, 'finances/safe_deposit/list.html', {
        'deposits': deposits,
        'safes': safes,
        'selected_safe': safe_id,
        'selected_is_posted': is_posted,
        'search_query': search_query
    })

@login_required
def safe_deposit_add(request):
    """إضافة إيداع جديد في الخزنة"""
    # إنشاء رقم مستند جديد
    last_deposit = SafeDeposit.objects.order_by('-id').first()
    new_number = f"DEP-{1:04d}" if not last_deposit else f"DEP-{int(last_deposit.number.split('-')[1]) + 1:04d}"

    if request.method == 'POST':
        form = SafeDepositForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                deposit = form.save(commit=False)
                # دائماً قم بتعيين رقم مستند جديد
                deposit.number = new_number
                deposit.save()
                messages.success(request, 'تم إضافة الإيداع بنجاح')
                return redirect('safe_deposit_list')
    else:
        form = SafeDepositForm(initial={
            'date': timezone.now()
        })

    return render(request, 'finances/safe_deposit/form.html', {
        'form': form,
        'title': 'إضافة إيداع جديد في الخزنة'
    })

@login_required
def safe_deposit_edit(request, pk):
    """تعديل إيداع في الخزنة"""
    deposit = get_object_or_404(SafeDeposit, pk=pk)

    # إذا كان الإيداع مرحل، قم بإلغاء الترحيل أولاً
    was_posted = False
    if deposit.is_posted:
        was_posted = True
        deposit.unpost_deposit()

    if request.method == 'POST':
        form = SafeDepositForm(request.POST, instance=deposit)
        if form.is_valid():
            with transaction.atomic():
                deposit = form.save()
                # إعادة ترحيل الإيداع إذا كان مرحلاً قبل التعديل
                if was_posted:
                    deposit.post_deposit()
                messages.success(request, 'تم تعديل الإيداع بنجاح')
                return redirect('safe_deposit_detail', pk=deposit.pk)
    else:
        form = SafeDepositForm(instance=deposit)

    return render(request, 'finances/safe_deposit/form.html', {
        'form': form,
        'title': 'تعديل إيداع في الخزنة',
        'deposit': deposit
    })

@login_required
def safe_deposit_detail(request, pk):
    """عرض تفاصيل الإيداع في الخزنة"""
    deposit = get_object_or_404(SafeDeposit, pk=pk)

    return render(request, 'finances/safe_deposit/detail.html', {
        'deposit': deposit
    })

@login_required
def safe_deposit_delete(request, pk):
    """حذف إيداع في الخزنة"""
    deposit = get_object_or_404(SafeDeposit, pk=pk)

    # إذا كان الإيداع مرحل، قم بإلغاء الترحيل أولاً
    if deposit.is_posted:
        deposit.unpost_deposit()

    if request.method == 'POST':
        deposit.delete()
        messages.success(request, 'تم حذف الإيداع بنجاح')
        return redirect('safe_deposit_list')

    return render(request, 'finances/safe_deposit/delete.html', {
        'deposit': deposit
    })

@login_required
def safe_deposit_post(request, pk):
    """ترحيل الإيداع في الخزنة"""
    deposit = get_object_or_404(SafeDeposit, pk=pk)

    if deposit.is_posted:
        messages.error(request, 'الإيداع مرحل بالفعل')
        return redirect('safe_deposit_detail', pk=deposit.pk)

    success = deposit.post_deposit()

    if success:
        messages.success(request, 'تم ترحيل الإيداع بنجاح')
    else:
        messages.error(request, 'حدث خطأ أثناء ترحيل الإيداع')

    return redirect('safe_deposit_detail', pk=deposit.pk)

@login_required
def safe_deposit_unpost(request, pk):
    """إلغاء ترحيل الإيداع في الخزنة"""
    deposit = get_object_or_404(SafeDeposit, pk=pk)

    if not deposit.is_posted:
        messages.error(request, 'الإيداع غير مرحل بالفعل')
        return redirect('safe_deposit_detail', pk=deposit.pk)

    success = deposit.unpost_deposit()

    if success:
        messages.success(request, 'تم إلغاء ترحيل الإيداع بنجاح')
    else:
        messages.error(request, 'حدث خطأ أثناء إلغاء ترحيل الإيداع')

    return redirect('safe_deposit_detail', pk=deposit.pk)
