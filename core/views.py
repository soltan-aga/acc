from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from .models import Company, Branch, Store, Safe, Contact, Representative, Driver, SystemSettings
from .forms import CompanyForm, BranchForm, StoreForm, SafeForm, RepresentativeForm, DriverForm, ContactForm, SystemSettingsForm
from products.models import Product, Category
from invoices.models import Invoice
from finances.models import ContactTransaction

# Create your views here.

@login_required
def home(request):
    context = {
        'companies_count': Company.objects.count(),
        'branches_count': Branch.objects.count(),
        'stores_count': Store.objects.count(),
        'safes_count': Safe.objects.count(),
        'contacts_count': Contact.objects.count(),
        'customers_count': Contact.objects.filter(contact_type=Contact.CUSTOMER).count(),
        'suppliers_count': Contact.objects.filter(contact_type=Contact.SUPPLIER).count(),
        'products_count': Product.objects.count(),
        'categories_count': Category.objects.count(),
        'invoices_count': Invoice.objects.count(),
        'sale_invoices_count': Invoice.objects.filter(invoice_type=Invoice.SALE).count(),
        'purchase_invoices_count': Invoice.objects.filter(invoice_type=Invoice.PURCHASE).count(),
        'representatives_count': Representative.objects.count(),
        'drivers_count': Driver.objects.count(),
    }
    return render(request, 'core/home.html', context)

# Company Views
@login_required
def company_list(request):
    companies = Company.objects.all()
    return render(request, 'core/company/list.html', {'companies': companies})

@login_required
def company_detail(request, pk):
    company = get_object_or_404(Company, pk=pk)
    branches = Branch.objects.filter(company=company)
    return render(request, 'core/company/detail.html', {'company': company, 'branches': branches})

@login_required
def company_add(request):
    if request.method == 'POST':
        form = CompanyForm(request.POST, request.FILES)
        if form.is_valid():
            company = form.save()
            messages.success(request, f'تم إضافة الشركة {company.name} بنجاح')
            return redirect('company_detail', pk=company.pk)
    else:
        form = CompanyForm()
    return render(request, 'core/company/form.html', {'form': form, 'title': 'إضافة شركة جديدة'})

@login_required
def company_edit(request, pk):
    company = get_object_or_404(Company, pk=pk)
    if request.method == 'POST':
        form = CompanyForm(request.POST, request.FILES, instance=company)
        if form.is_valid():
            company = form.save()
            messages.success(request, f'تم تعديل الشركة {company.name} بنجاح')
            return redirect('company_detail', pk=company.pk)
    else:
        form = CompanyForm(instance=company)
    return render(request, 'core/company/form.html', {'form': form, 'title': f'تعديل الشركة {company.name}'})

@login_required
def company_delete(request, pk):
    company = get_object_or_404(Company, pk=pk)
    if request.method == 'POST':
        company_name = company.name
        company.delete()
        messages.success(request, f'تم حذف الشركة {company_name} بنجاح')
        return redirect('company_list')
    return render(request, 'core/company/delete.html', {'company': company})

# Branch Views
@login_required
def branch_list(request):
    branches = Branch.objects.all()
    return render(request, 'core/branch/list.html', {'branches': branches})

@login_required
def branch_detail(request, pk):
    branch = get_object_or_404(Branch, pk=pk)
    stores = Store.objects.filter(branch=branch)
    safes = Safe.objects.filter(branch=branch)
    return render(request, 'core/branch/detail.html', {
        'branch': branch,
        'stores': stores,
        'safes': safes
    })

@login_required
def branch_add(request):
    if request.method == 'POST':
        form = BranchForm(request.POST)
        if form.is_valid():
            branch = form.save()
            messages.success(request, f'تم إضافة الفرع {branch.name} بنجاح')
            return redirect('branch_detail', pk=branch.pk)
    else:
        form = BranchForm()
    return render(request, 'core/branch/form.html', {'form': form, 'title': 'إضافة فرع جديد'})

@login_required
def branch_edit(request, pk):
    branch = get_object_or_404(Branch, pk=pk)
    if request.method == 'POST':
        form = BranchForm(request.POST, instance=branch)
        if form.is_valid():
            branch = form.save()
            messages.success(request, f'تم تعديل الفرع {branch.name} بنجاح')
            return redirect('branch_detail', pk=branch.pk)
    else:
        form = BranchForm(instance=branch)
    return render(request, 'core/branch/form.html', {'form': form, 'title': f'تعديل الفرع {branch.name}'})

@login_required
def branch_delete(request, pk):
    branch = get_object_or_404(Branch, pk=pk)
    if request.method == 'POST':
        branch_name = branch.name
        branch.delete()
        messages.success(request, f'تم حذف الفرع {branch_name} بنجاح')
        return redirect('branch_list')
    return render(request, 'core/branch/delete.html', {'branch': branch})

# Store Views
@login_required
def store_list(request):
    stores = Store.objects.all()
    return render(request, 'core/store/list.html', {'stores': stores})

@login_required
def store_detail(request, pk):
    store = get_object_or_404(Store, pk=pk)
    return render(request, 'core/store/detail.html', {'store': store})

@login_required
def store_add(request):
    if request.method == 'POST':
        form = StoreForm(request.POST)
        if form.is_valid():
            store = form.save()
            messages.success(request, f'تم إضافة المخزن {store.name} بنجاح')
            return redirect('store_detail', pk=store.pk)
    else:
        form = StoreForm()
    return render(request, 'core/store/form.html', {'form': form, 'title': 'إضافة مخزن جديد'})

@login_required
def store_edit(request, pk):
    store = get_object_or_404(Store, pk=pk)
    if request.method == 'POST':
        form = StoreForm(request.POST, instance=store)
        if form.is_valid():
            store = form.save()
            messages.success(request, f'تم تعديل المخزن {store.name} بنجاح')
            return redirect('store_detail', pk=store.pk)
    else:
        form = StoreForm(instance=store)
    return render(request, 'core/store/form.html', {'form': form, 'title': f'تعديل المخزن {store.name}'})

@login_required
def store_delete(request, pk):
    store = get_object_or_404(Store, pk=pk)
    if request.method == 'POST':
        store_name = store.name
        store.delete()
        messages.success(request, f'تم حذف المخزن {store_name} بنجاح')
        return redirect('store_list')
    return render(request, 'core/store/delete.html', {'store': store})

# Safe Views
@login_required
def safe_list(request):
    safes = Safe.objects.all()
    return render(request, 'core/safe/list.html', {'safes': safes})

@login_required
def safe_detail(request, pk):
    safe = get_object_or_404(Safe, pk=pk)
    return render(request, 'core/safe/detail.html', {'safe': safe})

@login_required
def safe_add(request):
    if request.method == 'POST':
        form = SafeForm(request.POST)
        if form.is_valid():
            safe = form.save()
            # Set current_balance to initial_balance when creating
            safe.current_balance = safe.initial_balance
            safe.save()
            messages.success(request, f'تم إضافة الخزنة {safe.name} بنجاح')
            return redirect('safe_detail', pk=safe.pk)
    else:
        form = SafeForm()
    return render(request, 'core/safe/form.html', {'form': form, 'title': 'إضافة خزنة جديدة'})

@login_required
def safe_edit(request, pk):
    safe = get_object_or_404(Safe, pk=pk)
    if request.method == 'POST':
        form = SafeForm(request.POST, instance=safe)
        if form.is_valid():
            # Save the old initial balance
            old_initial_balance = safe.initial_balance
            # Save the form
            safe = form.save()
            # Adjust current balance based on the change in initial balance
            if old_initial_balance != safe.initial_balance:
                difference = safe.initial_balance - old_initial_balance
                safe.current_balance += difference
                safe.save()
            messages.success(request, f'تم تعديل الخزنة {safe.name} بنجاح')
            return redirect('safe_detail', pk=safe.pk)
    else:
        form = SafeForm(instance=safe)
    return render(request, 'core/safe/form.html', {'form': form, 'title': f'تعديل الخزنة {safe.name}'})

@login_required
def safe_delete(request, pk):
    safe = get_object_or_404(Safe, pk=pk)
    if request.method == 'POST':
        safe_name = safe.name
        safe.delete()
        messages.success(request, f'تم حذف الخزنة {safe_name} بنجاح')
        return redirect('safe_list')
    return render(request, 'core/safe/delete.html', {'safe': safe})

# Representative Views
@login_required
def representative_list(request):
    representatives = Representative.objects.all()
    return render(request, 'core/representative/list.html', {'representatives': representatives})

@login_required
def representative_detail(request, pk):
    representative = get_object_or_404(Representative, pk=pk)
    return render(request, 'core/representative/detail.html', {'representative': representative})

@login_required
def representative_add(request):
    if request.method == 'POST':
        form = RepresentativeForm(request.POST)
        if form.is_valid():
            representative = form.save()
            messages.success(request, f'تم إضافة المندوب {representative.name} بنجاح')
            return redirect('representative_detail', pk=representative.pk)
    else:
        form = RepresentativeForm()
    return render(request, 'core/representative/form.html', {'form': form, 'title': 'إضافة مندوب جديد'})

@login_required
def representative_edit(request, pk):
    representative = get_object_or_404(Representative, pk=pk)
    if request.method == 'POST':
        form = RepresentativeForm(request.POST, instance=representative)
        if form.is_valid():
            representative = form.save()
            messages.success(request, f'تم تعديل المندوب {representative.name} بنجاح')
            return redirect('representative_detail', pk=representative.pk)
    else:
        form = RepresentativeForm(instance=representative)
    return render(request, 'core/representative/form.html', {'form': form, 'title': f'تعديل المندوب {representative.name}'})

@login_required
def representative_delete(request, pk):
    representative = get_object_or_404(Representative, pk=pk)
    if request.method == 'POST':
        representative_name = representative.name
        representative.delete()
        messages.success(request, f'تم حذف المندوب {representative_name} بنجاح')
        return redirect('representative_list')
    return render(request, 'core/representative/delete.html', {'representative': representative})

# Driver Views
@login_required
def driver_list(request):
    drivers = Driver.objects.all()
    return render(request, 'core/driver/list.html', {'drivers': drivers})

@login_required
def driver_detail(request, pk):
    driver = get_object_or_404(Driver, pk=pk)
    return render(request, 'core/driver/detail.html', {'driver': driver})

@login_required
def driver_add(request):
    if request.method == 'POST':
        form = DriverForm(request.POST)
        if form.is_valid():
            driver = form.save()
            messages.success(request, f'تم إضافة السائق {driver.name} بنجاح')
            return redirect('driver_detail', pk=driver.pk)
    else:
        form = DriverForm()
    return render(request, 'core/driver/form.html', {'form': form, 'title': 'إضافة سائق جديد'})

@login_required
def driver_edit(request, pk):
    driver = get_object_or_404(Driver, pk=pk)
    if request.method == 'POST':
        form = DriverForm(request.POST, instance=driver)
        if form.is_valid():
            driver = form.save()
            messages.success(request, f'تم تعديل السائق {driver.name} بنجاح')
            return redirect('driver_detail', pk=driver.pk)
    else:
        form = DriverForm(instance=driver)
    return render(request, 'core/driver/form.html', {'form': form, 'title': f'تعديل السائق {driver.name}'})

@login_required
def driver_delete(request, pk):
    driver = get_object_or_404(Driver, pk=pk)
    if request.method == 'POST':
        driver_name = driver.name
        driver.delete()
        messages.success(request, f'تم حذف السائق {driver_name} بنجاح')
        return redirect('driver_list')
    return render(request, 'core/driver/delete.html', {'driver': driver})

# Contact Views (Customers and Suppliers)
@login_required
def contact_list(request, contact_type=None):
    """View to display all contacts or filter by type (customer/supplier)"""
    if contact_type == 'customers':
        contacts = Contact.objects.filter(contact_type=Contact.CUSTOMER)
        title = 'العملاء'
        add_url = 'customer_add'
    elif contact_type == 'suppliers':
        contacts = Contact.objects.filter(contact_type=Contact.SUPPLIER)
        title = 'الموردين'
        add_url = 'supplier_add'
    else:
        contacts = Contact.objects.all()
        title = 'جهات الاتصال'
        add_url = 'contact_add'

    return render(request, 'core/contact/list.html', {
        'contacts': contacts,
        'title': title,
        'add_url': add_url,
        'contact_type': contact_type
    })

@login_required
def customer_list(request):
    """View to display all customers"""
    return contact_list(request, 'customers')

@login_required
def supplier_list(request):
    """View to display all suppliers"""
    return contact_list(request, 'suppliers')

@login_required
def contact_detail(request, pk):
    """View to display contact details"""
    contact = get_object_or_404(Contact, pk=pk)
    return render(request, 'core/contact/detail.html', {'contact': contact})

@login_required
def contact_add(request, contact_type=None):
    """View to add a new contact"""
    initial = {}
    if contact_type == 'customer':
        initial['contact_type'] = Contact.CUSTOMER
        title = 'إضافة عميل جديد'
        success_message = 'تم إضافة العميل بنجاح'
        redirect_url = 'customer_list'
    elif contact_type == 'supplier':
        initial['contact_type'] = Contact.SUPPLIER
        title = 'إضافة مورد جديد'
        success_message = 'تم إضافة المورد بنجاح'
        redirect_url = 'supplier_list'
    else:
        title = 'إضافة جهة اتصال جديدة'
        success_message = 'تم إضافة جهة الاتصال بنجاح'
        redirect_url = 'contact_list'

    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            contact = form.save()
            # Set current_balance to initial_balance when creating
            contact.current_balance = contact.initial_balance
            contact.save()
            messages.success(request, success_message)
            return redirect(redirect_url)
    else:
        form = ContactForm(initial=initial)

    return render(request, 'core/contact/form.html', {
        'form': form,
        'title': title,
        'contact_type': contact_type
    })

@login_required
def customer_add(request):
    """View to add a new customer"""
    return contact_add(request, 'customer')

@login_required
def supplier_add(request):
    """View to add a new supplier"""
    return contact_add(request, 'supplier')

@login_required
def contact_edit(request, pk):
    """View to edit a contact"""
    contact = get_object_or_404(Contact, pk=pk)

    if request.method == 'POST':
        form = ContactForm(request.POST, instance=contact)
        if form.is_valid():
            # Save the old initial balance
            old_initial_balance = contact.initial_balance
            # Save the form
            contact = form.save()
            # Adjust current balance based on the change in initial balance
            if old_initial_balance != contact.initial_balance:
                difference = contact.initial_balance - old_initial_balance
                contact.current_balance += difference
                contact.save()

            if contact.contact_type == Contact.CUSTOMER:
                success_message = f'تم تعديل العميل {contact.name} بنجاح'
                redirect_url = 'customer_list'
            else:
                success_message = f'تم تعديل المورد {contact.name} بنجاح'
                redirect_url = 'supplier_list'

            messages.success(request, success_message)
            return redirect(redirect_url)
    else:
        form = ContactForm(instance=contact)

    if contact.contact_type == Contact.CUSTOMER:
        title = f'تعديل العميل {contact.name}'
    else:
        title = f'تعديل المورد {contact.name}'

    return render(request, 'core/contact/form.html', {
        'form': form,
        'title': title,
        'contact': contact
    })

@login_required
def contact_delete(request, pk):
    """View to delete a contact"""
    contact = get_object_or_404(Contact, pk=pk)

    if request.method == 'POST':
        contact_name = contact.name
        contact_type = contact.contact_type
        contact.delete()

        if contact_type == Contact.CUSTOMER:
            success_message = f'تم حذف العميل {contact_name} بنجاح'
            redirect_url = 'customer_list'
        else:
            success_message = f'تم حذف المورد {contact_name} بنجاح'
            redirect_url = 'supplier_list'

        messages.success(request, success_message)
        return redirect(redirect_url)

    return render(request, 'core/contact/delete.html', {'contact': contact})

@login_required
def contact_statement(request, pk):
    """عرض كشف حساب العميل/المورد"""
    contact = get_object_or_404(Contact, pk=pk)

    # الحصول على جميع حركات الحساب لهذا العميل/المورد
    transactions = ContactTransaction.objects.filter(contact=contact).order_by('date')

    # البحث والتصفية
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    transaction_type = request.GET.get('type', '')

    # تطبيق التصفية حسب التاريخ
    if date_from:
        transactions = transactions.filter(date__gte=date_from)
    if date_to:
        transactions = transactions.filter(date__lte=date_to)

    # تطبيق التصفية حسب نوع العملية
    if transaction_type:
        transactions = transactions.filter(transaction_type=transaction_type)

    # البحث
    query = request.GET.get('q', '')
    if query:
        transactions = transactions.filter(
            Q(description__icontains=query) |
            Q(reference_number__icontains=query) |
            Q(invoice__number__icontains=query)
        )

    # حساب الرصيد التراكمي لكل حركة
    running_balance = contact.initial_balance
    transaction_list = []

    for transaction in transactions:
        # حساب الرصيد التراكمي
        running_balance += transaction.amount

        # تحديد المبلغ الدائن والمدين
        debit_amount = 0
        credit_amount = 0

        if transaction.amount > 0:
            debit_amount = transaction.amount
        else:
            credit_amount = abs(transaction.amount)

        # إضافة الحركة مع الرصيد التراكمي والمبالغ المفصلة
        transaction_list.append({
            'transaction': transaction,
            'debit_amount': debit_amount,
            'credit_amount': credit_amount,
            'running_balance': running_balance
        })

    context = {
        'contact': contact,
        'transactions': transaction_list,
        'initial_balance': contact.initial_balance,
        'current_balance': contact.current_balance,
        'date_from': date_from,
        'date_to': date_to,
        'transaction_type': transaction_type,
        'query': query,
        'transaction_types': ContactTransaction.TRANSACTION_TYPE_CHOICES
    }

    return render(request, 'core/contact/statement.html', context)


# System Settings Views
@login_required
def system_settings(request):
    """عرض وتعديل إعدادات النظام"""
    # الحصول على إعدادات النظام أو إنشاء إعدادات افتراضية إذا لم تكن موجودة
    settings = SystemSettings.get_settings()

    if request.method == 'POST':
        form = SystemSettingsForm(request.POST, instance=settings)
        if form.is_valid():
            form.save()
            messages.success(request, 'تم حفظ إعدادات النظام بنجاح')
            return redirect('system_settings')
    else:
        form = SystemSettingsForm(instance=settings)

    return render(request, 'core/settings/system_settings.html', {
        'form': form,
        'title': 'إعدادات النظام'
    })


# API Views
from django.http import JsonResponse

@login_required
def contact_balance_api(request, pk):
    """واجهة برمجة التطبيقات للحصول على رصيد العميل/المورد"""
    try:
        contact = get_object_or_404(Contact, pk=pk)
        return JsonResponse({
            'success': True,
            'contact_id': contact.id,
            'contact_name': contact.name,
            'contact_type': contact.contact_type,
            'current_balance': float(contact.current_balance),
            'credit_limit': float(contact.credit_limit)
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)
