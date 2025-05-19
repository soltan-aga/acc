from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from ..models import SafeWithdrawal
from ..forms import SafeWithdrawalForm
from core.models import Safe

@login_required
def safe_withdrawal_list(request):
    """عرض قائمة السحوبات من الخزنة"""
    withdrawals = SafeWithdrawal.objects.all().order_by('-date')

    # تصفية حسب الخزنة
    safe_id = request.GET.get('safe')
    if safe_id:
        withdrawals = withdrawals.filter(safe_id=safe_id)

    # تصفية حسب حالة الترحيل
    is_posted = request.GET.get('is_posted')
    if is_posted == 'yes':
        withdrawals = withdrawals.filter(is_posted=True)
    elif is_posted == 'no':
        withdrawals = withdrawals.filter(is_posted=False)

    # البحث
    search_query = request.GET.get('q')
    if search_query:
        withdrawals = withdrawals.filter(
            Q(number__icontains=search_query) |
            Q(recipient__icontains=search_query) |
            Q(notes__icontains=search_query) |
            Q(reference_number__icontains=search_query)
        )

    # قائمة الخزن للتصفية
    safes = Safe.objects.all()

    return render(request, 'finances/safe_withdrawal/list.html', {
        'withdrawals': withdrawals,
        'safes': safes,
        'selected_safe': safe_id,
        'selected_is_posted': is_posted,
        'search_query': search_query
    })

@login_required
def safe_withdrawal_add(request):
    """إضافة سحب جديد من الخزنة"""
    # إنشاء رقم مستند جديد
    last_withdrawal = SafeWithdrawal.objects.order_by('-id').first()
    new_number = f"WDR-{1:04d}" if not last_withdrawal else f"WDR-{int(last_withdrawal.number.split('-')[1]) + 1:04d}"

    if request.method == 'POST':
        form = SafeWithdrawalForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                withdrawal = form.save(commit=False)
                # دائماً قم بتعيين رقم مستند جديد
                withdrawal.number = new_number
                withdrawal.save()
                messages.success(request, 'تم إضافة السحب بنجاح')
                return redirect('safe_withdrawal_list')
    else:
        form = SafeWithdrawalForm(initial={
            'date': timezone.now()
        })

    return render(request, 'finances/safe_withdrawal/form.html', {
        'form': form,
        'title': 'إضافة سحب جديد من الخزنة'
    })

@login_required
def safe_withdrawal_edit(request, pk):
    """تعديل سحب من الخزنة"""
    withdrawal = get_object_or_404(SafeWithdrawal, pk=pk)

    # إذا كان السحب مرحل، قم بإلغاء الترحيل أولاً
    was_posted = False
    if withdrawal.is_posted:
        was_posted = True
        withdrawal.unpost_withdrawal()

    if request.method == 'POST':
        form = SafeWithdrawalForm(request.POST, instance=withdrawal)
        if form.is_valid():
            with transaction.atomic():
                withdrawal = form.save()
                # إعادة ترحيل السحب إذا كان مرحلاً قبل التعديل
                if was_posted:
                    withdrawal.post_withdrawal()
                messages.success(request, 'تم تعديل السحب بنجاح')
                return redirect('safe_withdrawal_detail', pk=withdrawal.pk)
    else:
        form = SafeWithdrawalForm(instance=withdrawal)

    return render(request, 'finances/safe_withdrawal/form.html', {
        'form': form,
        'title': 'تعديل سحب من الخزنة',
        'withdrawal': withdrawal
    })

@login_required
def safe_withdrawal_detail(request, pk):
    """عرض تفاصيل السحب من الخزنة"""
    withdrawal = get_object_or_404(SafeWithdrawal, pk=pk)

    return render(request, 'finances/safe_withdrawal/detail.html', {
        'withdrawal': withdrawal
    })

@login_required
def safe_withdrawal_delete(request, pk):
    """حذف سحب من الخزنة"""
    withdrawal = get_object_or_404(SafeWithdrawal, pk=pk)

    # إذا كان السحب مرحل، قم بإلغاء الترحيل أولاً
    if withdrawal.is_posted:
        withdrawal.unpost_withdrawal()

    if request.method == 'POST':
        withdrawal.delete()
        messages.success(request, 'تم حذف السحب بنجاح')
        return redirect('safe_withdrawal_list')

    return render(request, 'finances/safe_withdrawal/delete.html', {
        'withdrawal': withdrawal
    })

@login_required
def safe_withdrawal_post(request, pk):
    """ترحيل السحب من الخزنة"""
    withdrawal = get_object_or_404(SafeWithdrawal, pk=pk)

    if withdrawal.is_posted:
        messages.error(request, 'السحب مرحل بالفعل')
        return redirect('safe_withdrawal_detail', pk=withdrawal.pk)

    success = withdrawal.post_withdrawal()

    if success:
        messages.success(request, 'تم ترحيل السحب بنجاح')
    else:
        messages.error(request, 'حدث خطأ أثناء ترحيل السحب')

    return redirect('safe_withdrawal_detail', pk=withdrawal.pk)

@login_required
def safe_withdrawal_unpost(request, pk):
    """إلغاء ترحيل السحب من الخزنة"""
    withdrawal = get_object_or_404(SafeWithdrawal, pk=pk)

    if not withdrawal.is_posted:
        messages.error(request, 'السحب غير مرحل بالفعل')
        return redirect('safe_withdrawal_detail', pk=withdrawal.pk)

    success = withdrawal.unpost_withdrawal()

    if success:
        messages.success(request, 'تم إلغاء ترحيل السحب بنجاح')
    else:
        messages.error(request, 'حدث خطأ أثناء إلغاء ترحيل السحب')

    return redirect('safe_withdrawal_detail', pk=withdrawal.pk)
