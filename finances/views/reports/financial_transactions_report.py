from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Sum
from django.utils import timezone
from datetime import datetime, timedelta

from ...models import SafeTransaction
from core.models import Safe

@login_required
def financial_transactions_report(request):
    """تقرير الحركات المالية"""
    # الحصول على الخزنة المحددة
    safe_id = request.GET.get('safe')
    safe = None
    if safe_id:
        try:
            safe = Safe.objects.get(pk=safe_id)
        except Safe.DoesNotExist:
            pass

    # الحصول على نطاق التاريخ
    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')

    # تحويل التواريخ إلى كائنات datetime
    from_date_obj = None
    to_date_obj = None

    if from_date:
        try:
            from_date_obj = datetime.strptime(from_date, '%Y-%m-%d').replace(hour=0, minute=0, second=0)
        except ValueError:
            from_date = None

    if to_date:
        try:
            to_date_obj = datetime.strptime(to_date, '%Y-%m-%d').replace(hour=23, minute=59, second=59)
        except ValueError:
            to_date = None

    # إذا لم يتم تحديد تاريخ، استخدم اليوم
    if not from_date_obj:
        from_date_obj = timezone.now().replace(hour=0, minute=0, second=0)
        from_date = from_date_obj.strftime('%Y-%m-%d')

    if not to_date_obj:
        to_date_obj = timezone.now().replace(hour=23, minute=59, second=59)
        to_date = to_date_obj.strftime('%Y-%m-%d')

    # الحصول على الحركات المالية
    transactions = SafeTransaction.objects.filter(
        date__gte=from_date_obj,
        date__lte=to_date_obj
    ).order_by('date')

    # تصفية حسب الخزنة
    if safe:
        transactions = transactions.filter(safe=safe)

    # الحصول على الرصيد السابق
    previous_transactions = SafeTransaction.objects.filter(date__lt=from_date_obj)
    if safe:
        previous_transactions = previous_transactions.filter(safe=safe)

    # حساب الإيرادات والمصروفات السابقة
    previous_in = previous_transactions.filter(
        transaction_type__in=['deposit', 'income', 'receipt', 'sale_invoice', 'purchase_return_invoice']
    ).aggregate(Sum('amount'))['amount__sum'] or 0

    previous_out = previous_transactions.filter(
        transaction_type__in=['withdrawal', 'expense', 'payment', 'purchase_invoice', 'sale_return_invoice']
    ).aggregate(Sum('amount'))['amount__sum'] or 0

    previous_balance = previous_in - previous_out

    # حساب الإيرادات والمصروفات الحالية
    current_in = transactions.filter(
        transaction_type__in=['deposit', 'income', 'receipt', 'sale_invoice', 'purchase_return_invoice']
    ).aggregate(Sum('amount'))['amount__sum'] or 0

    current_out = transactions.filter(
        transaction_type__in=['withdrawal', 'expense', 'payment', 'purchase_invoice', 'sale_return_invoice']
    ).aggregate(Sum('amount'))['amount__sum'] or 0

    # حساب صافي الحركة والرصيد النهائي
    net_movement = current_in - current_out
    final_balance = previous_balance + net_movement

    # الحصول على الرصيد الحالي للخزنة
    current_safe_balance = None
    if safe:
        # حساب الرصيد الحالي للخزنة
        safe_in = SafeTransaction.objects.filter(
            safe=safe,
            transaction_type__in=['deposit', 'income', 'receipt', 'sale_invoice', 'purchase_return_invoice']
        ).aggregate(Sum('amount'))['amount__sum'] or 0

        safe_out = SafeTransaction.objects.filter(
            safe=safe,
            transaction_type__in=['withdrawal', 'expense', 'payment', 'purchase_invoice', 'sale_return_invoice']
        ).aggregate(Sum('amount'))['amount__sum'] or 0

        current_safe_balance = safe.initial_balance + safe_in - safe_out

    # إعداد قائمة الحركات مع الرصيد المتراكم
    transactions_with_balance = []
    running_balance = previous_balance

    for transaction in transactions:
        # حساب الرصيد المتراكم بناءً على نوع العملية
        if transaction.transaction_type in ['deposit', 'income', 'receipt', 'sale_invoice', 'purchase_return_invoice']:
            # عمليات تزيد الرصيد
            running_balance += transaction.amount
        else:
            # عمليات تنقص الرصيد
            running_balance -= transaction.amount

        transactions_with_balance.append({
            'transaction': transaction,
            'running_balance': running_balance
        })

    # الحصول على قائمة الخزن للتصفية
    safes = Safe.objects.all()

    # الحصول على قائمة أنواع العمليات للتصفية
    transaction_types = [
        ('deposit', 'إيداع'),
        ('withdrawal', 'سحب'),
        ('income', 'إيراد'),
        ('expense', 'مصروف'),
        ('receipt', 'قبض'),
        ('payment', 'دفع'),
        ('sale_invoice', 'فاتورة بيع'),
        ('purchase_invoice', 'فاتورة شراء'),
        ('sale_return_invoice', 'مرتجع بيع'),
        ('purchase_return_invoice', 'مرتجع شراء'),
    ]

    # الحصول على اسم الخزنة المحددة للعرض
    selected_safe_name = safe.name if safe else None

    return render(request, 'finances/reports/financial_transactions.html', {
        'transactions': transactions,
        'transactions_with_balance': transactions_with_balance,
        'transaction_types': transaction_types,
        'safes': safes,
        'selected_safe': safe,
        'selected_safe_name': selected_safe_name,
        'from_date': from_date,
        'to_date': to_date,
        'previous_balance': previous_balance,
        'current_in': current_in,
        'current_out': current_out,
        'net_movement': net_movement,
        'final_balance': final_balance,
        'total_in': current_in,
        'total_out': current_out,
        'net_total': net_movement,
        'current_safe_balance': current_safe_balance
    })

@login_required
def financial_transactions_print(request):
    """طباعة تقرير الحركات المالية"""
    # نفس منطق التصفية الموجود في الدالة السابقة
    safe_id = request.GET.get('safe')
    safe = None
    if safe_id:
        try:
            safe = Safe.objects.get(pk=safe_id)
        except Safe.DoesNotExist:
            pass

    # الحصول على نطاق التاريخ
    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')

    # تحويل التواريخ إلى كائنات datetime
    from_date_obj = None
    to_date_obj = None

    if from_date:
        try:
            from_date_obj = datetime.strptime(from_date, '%Y-%m-%d').replace(hour=0, minute=0, second=0)
        except ValueError:
            from_date = None

    if to_date:
        try:
            to_date_obj = datetime.strptime(to_date, '%Y-%m-%d').replace(hour=23, minute=59, second=59)
        except ValueError:
            to_date = None

    # إذا لم يتم تحديد تاريخ، استخدم اليوم
    if not from_date_obj:
        from_date_obj = timezone.now().replace(hour=0, minute=0, second=0)
        from_date = from_date_obj.strftime('%Y-%m-%d')

    if not to_date_obj:
        to_date_obj = timezone.now().replace(hour=23, minute=59, second=59)
        to_date = to_date_obj.strftime('%Y-%m-%d')

    # الحصول على الحركات المالية
    transactions = SafeTransaction.objects.filter(
        date__gte=from_date_obj,
        date__lte=to_date_obj
    ).order_by('date')

    # تصفية حسب الخزنة
    if safe:
        transactions = transactions.filter(safe=safe)

    # الحصول على الرصيد السابق
    previous_transactions = SafeTransaction.objects.filter(date__lt=from_date_obj)
    if safe:
        previous_transactions = previous_transactions.filter(safe=safe)

    # حساب الإيرادات والمصروفات السابقة
    previous_in = previous_transactions.filter(
        transaction_type__in=['deposit', 'income', 'receipt', 'sale_invoice', 'purchase_return_invoice']
    ).aggregate(Sum('amount'))['amount__sum'] or 0

    previous_out = previous_transactions.filter(
        transaction_type__in=['withdrawal', 'expense', 'payment', 'purchase_invoice', 'sale_return_invoice']
    ).aggregate(Sum('amount'))['amount__sum'] or 0

    previous_balance = previous_in - previous_out

    # حساب الإيرادات والمصروفات الحالية
    current_in = transactions.filter(
        transaction_type__in=['deposit', 'income', 'receipt', 'sale_invoice', 'purchase_return_invoice']
    ).aggregate(Sum('amount'))['amount__sum'] or 0

    current_out = transactions.filter(
        transaction_type__in=['withdrawal', 'expense', 'payment', 'purchase_invoice', 'sale_return_invoice']
    ).aggregate(Sum('amount'))['amount__sum'] or 0

    # حساب صافي الحركة والرصيد النهائي
    net_movement = current_in - current_out
    final_balance = previous_balance + net_movement

    # إعداد قائمة الحركات مع الرصيد المتراكم
    transactions_with_balance = []
    running_balance = previous_balance

    for transaction in transactions:
        # حساب الرصيد المتراكم بناءً على نوع العملية
        if transaction.transaction_type in ['deposit', 'income', 'receipt', 'sale_invoice', 'purchase_return_invoice']:
            # عمليات تزيد الرصيد
            running_balance += transaction.amount
        else:
            # عمليات تنقص الرصيد
            running_balance -= transaction.amount

        transactions_with_balance.append({
            'transaction': transaction,
            'running_balance': running_balance
        })

    # الحصول على اسم الخزنة المحددة للعرض
    selected_safe_name = safe.name if safe else None

    return render(request, 'finances/reports/financial_transactions_print.html', {
        'transactions_with_balance': transactions_with_balance,
        'selected_safe_name': selected_safe_name,
        'from_date': from_date,
        'to_date': to_date,
        'previous_balance': previous_balance,
        'current_in': current_in,
        'current_out': current_out,
        'net_movement': net_movement,
        'final_balance': final_balance,
        'total_in': current_in,
        'total_out': current_out,
        'net_total': net_movement,
        'print_date': timezone.now()
    })
