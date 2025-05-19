from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Sum
from django.utils import timezone
from datetime import datetime, timedelta

from ...models import Income, Expense, IncomeCategory, ExpenseCategory

@login_required
def income_expense_report(request):
    """تقرير الإيرادات والمصروفات"""
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

    # إذا لم يتم تحديد تاريخ، استخدم الشهر الحالي
    if not from_date_obj:
        from_date_obj = timezone.now().replace(day=1, hour=0, minute=0, second=0)
        from_date = from_date_obj.strftime('%Y-%m-%d')

    if not to_date_obj:
        # آخر يوم في الشهر
        next_month = from_date_obj.replace(day=28) + timedelta(days=4)
        last_day = (next_month - timedelta(days=next_month.day)).day
        to_date_obj = from_date_obj.replace(day=last_day, hour=23, minute=59, second=59)
        to_date = to_date_obj.strftime('%Y-%m-%d')

    # الحصول على الإيرادات والمصروفات
    incomes = Income.objects.filter(
        date__gte=from_date_obj,
        date__lte=to_date_obj,
        is_posted=True
    ).order_by('date')

    expenses = Expense.objects.filter(
        date__gte=from_date_obj,
        date__lte=to_date_obj,
        is_posted=True
    ).order_by('date')

    # تجميع الإيرادات حسب القسم
    income_by_category = {}
    for income in incomes:
        category_name = income.category.name
        if category_name not in income_by_category:
            income_by_category[category_name] = 0
        income_by_category[category_name] += income.amount

    # تجميع المصروفات حسب القسم
    expense_by_category = {}
    for expense in expenses:
        category_name = expense.category.name
        if category_name not in expense_by_category:
            expense_by_category[category_name] = 0
        expense_by_category[category_name] += expense.amount

    # حساب الإجماليات
    total_income = incomes.aggregate(Sum('amount'))['amount__sum'] or 0
    total_expense = expenses.aggregate(Sum('amount'))['amount__sum'] or 0
    net_profit = total_income - total_expense

    return render(request, 'finances/reports/income_expense.html', {
        'incomes': incomes,
        'expenses': expenses,
        'income_by_category': income_by_category,
        'expense_by_category': expense_by_category,
        'total_income': total_income,
        'total_expense': total_expense,
        'net_profit': net_profit,
        'from_date': from_date,
        'to_date': to_date
    })

@login_required
def income_expense_print(request):
    """طباعة تقرير الإيرادات والمصروفات"""
    # نفس منطق التصفية الموجود في الدالة السابقة
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

    # إذا لم يتم تحديد تاريخ، استخدم الشهر الحالي
    if not from_date_obj:
        from_date_obj = timezone.now().replace(day=1, hour=0, minute=0, second=0)
        from_date = from_date_obj.strftime('%Y-%m-%d')

    if not to_date_obj:
        # آخر يوم في الشهر
        next_month = from_date_obj.replace(day=28) + timedelta(days=4)
        last_day = (next_month - timedelta(days=next_month.day)).day
        to_date_obj = from_date_obj.replace(day=last_day, hour=23, minute=59, second=59)
        to_date = to_date_obj.strftime('%Y-%m-%d')

    # الحصول على الإيرادات والمصروفات
    incomes = Income.objects.filter(
        date__gte=from_date_obj,
        date__lte=to_date_obj,
        is_posted=True
    ).order_by('date')

    expenses = Expense.objects.filter(
        date__gte=from_date_obj,
        date__lte=to_date_obj,
        is_posted=True
    ).order_by('date')

    # تجميع الإيرادات حسب القسم
    income_by_category = {}
    for income in incomes:
        category_name = income.category.name
        if category_name not in income_by_category:
            income_by_category[category_name] = 0
        income_by_category[category_name] += income.amount

    # تجميع المصروفات حسب القسم
    expense_by_category = {}
    for expense in expenses:
        category_name = expense.category.name
        if category_name not in expense_by_category:
            expense_by_category[category_name] = 0
        expense_by_category[category_name] += expense.amount

    # حساب الإجماليات
    total_income = incomes.aggregate(Sum('amount'))['amount__sum'] or 0
    total_expense = expenses.aggregate(Sum('amount'))['amount__sum'] or 0
    net_profit = total_income - total_expense

    # التحقق من نوع التصدير
    export_type = request.GET.get('export')

    return render(request, 'finances/reports/income_expense_print.html', {
        'incomes': incomes,
        'expenses': expenses,
        'income_by_category': income_by_category,
        'expense_by_category': expense_by_category,
        'total_income': total_income,
        'total_expense': total_expense,
        'net_profit': net_profit,
        'from_date': from_date,
        'to_date': to_date,
        'print_date': timezone.now(),
        'export_type': export_type
    })
