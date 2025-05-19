from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.db.models import Q
from django.forms import inlineformset_factory
from django.utils import timezone

from ..models import StorePermit, StorePermitItem, ProductTransaction
from ..forms import StorePermitForm, StorePermitItemForm
from core.models import Store, Driver, Representative
from products.models import Product, ProductUnit

# ======== أذونات المخزن (الصرف والاستلام) ========
@login_required
def store_permit_list(request):
    """عرض قائمة أذونات المخزن"""
    permits = StorePermit.objects.all().order_by('-date')

    # تصفية حسب نوع الإذن
    permit_type = request.GET.get('permit_type')
    if permit_type:
        permits = permits.filter(permit_type=permit_type)

    # تصفية حسب المخزن
    store_id = request.GET.get('store')
    if store_id:
        permits = permits.filter(store_id=store_id)

    # تصفية حسب حالة الترحيل
    is_posted = request.GET.get('is_posted')
    if is_posted == 'yes':
        permits = permits.filter(is_posted=True)
    elif is_posted == 'no':
        permits = permits.filter(is_posted=False)

    # تصفية حسب التاريخ
    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')

    if from_date:
        try:
            from_date_obj = timezone.datetime.strptime(from_date, '%Y-%m-%d').replace(hour=0, minute=0, second=0)
            permits = permits.filter(date__gte=from_date_obj)
        except ValueError:
            messages.error(request, 'تنسيق تاريخ البداية غير صحيح. يرجى استخدام التنسيق YYYY-MM-DD')
            from_date = None

    if to_date:
        try:
            to_date_obj = timezone.datetime.strptime(to_date, '%Y-%m-%d').replace(hour=23, minute=59, second=59)
            permits = permits.filter(date__lte=to_date_obj)
        except ValueError:
            messages.error(request, 'تنسيق تاريخ النهاية غير صحيح. يرجى استخدام التنسيق YYYY-MM-DD')
            to_date = None

    # البحث
    search_query = request.GET.get('q')
    if search_query:
        permits = permits.filter(
            Q(number__icontains=search_query) |
            Q(person_name__icontains=search_query) |
            Q(notes__icontains=search_query) |
            Q(reference_number__icontains=search_query)
        )

    # قائمة المخازن للتصفية
    stores = Store.objects.all()

    # إعداد قائمة الفلاتر للقالب الجزئي
    permit_filters = [
        {
            'name': 'permit_type',
            'label': 'نوع الإذن',
            'type': 'select',
            'options': StorePermit.PERMIT_TYPES,
            'value': permit_type
        },
        {
            'name': 'store',
            'label': 'المخزن',
            'type': 'select',
            'options': stores,
            'value': store_id
        },
        {
            'name': 'is_posted',
            'label': 'حالة الترحيل',
            'type': 'select',
            'options': [('yes', 'مرحل'), ('no', 'غير مرحل')],
            'value': is_posted
        }
    ]

    return render(request, 'store_permits/list.html', {
        'permits': permits,
        'permit_filters': permit_filters,
        'from_date': from_date,
        'to_date': to_date,
        'search_query': search_query
    })

@login_required
def store_permit_add(request):
    """إضافة إذن مخزني جديد"""
    # إنشاء رقم مستند جديد
    last_permit = StorePermit.objects.order_by('-id').first()
    new_number = f"PER-{1:04d}" if not last_permit else f"PER-{int(last_permit.number.split('-')[1]) + 1:04d}"

    # إنشاء نموذج البيانات الرئيسي
    if request.method == 'POST':
        form = StorePermitForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                permit = form.save(commit=False)
                permit.number = new_number
                permit.save()

                # إنشاء نموذج البنود
                StorePermitItemFormSet = inlineformset_factory(
                    StorePermit, StorePermitItem,
                    form=StorePermitItemForm, extra=1, can_delete=True
                )
                formset = StorePermitItemFormSet(request.POST, instance=permit)

                if formset.is_valid():
                    formset.save()
                    messages.success(request, 'تم إضافة الإذن المخزني بنجاح')
                    return redirect('store_permit_detail', pk=permit.pk)
                else:
                    # في حالة وجود أخطاء في البنود، قم بحذف الإذن وإظهار الأخطاء
                    permit.delete()
                    for error in formset.errors:
                        messages.error(request, f'خطأ في البنود: {error}')
        else:
            # Crear el formset incluso cuando el formulario principal no es válido
            StorePermitItemFormSet = inlineformset_factory(
                StorePermit, StorePermitItem,
                form=StorePermitItemForm, extra=1, can_delete=True
            )
            formset = StorePermitItemFormSet(request.POST)

            # Mostrar errores del formulario principal
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'خطأ في حقل {field}: {error}')
    else:
        form = StorePermitForm(initial={
            'date': timezone.now(),
            'is_posted': True
        })
        StorePermitItemFormSet = inlineformset_factory(
            StorePermit, StorePermitItem,
            form=StorePermitItemForm, extra=1, can_delete=True
        )
        formset = StorePermitItemFormSet()

    return render(request, 'store_permits/form.html', {
        'form': form,
        'formset': formset,
        'title': 'إضافة إذن مخزني جديد'
    })

@login_required
def store_permit_add_issue(request):
    """إضافة إذن صرف مخزني جديد"""
    # إنشاء رقم مستند جديد
    last_permit = StorePermit.objects.order_by('-id').first()
    new_number = f"ISS-{1:04d}" if not last_permit else f"ISS-{int(last_permit.number.split('-')[1]) + 1:04d}"

    # إنشاء نموذج البيانات الرئيسي
    if request.method == 'POST':
        form = StorePermitForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                permit = form.save(commit=False)
                permit.permit_type = StorePermit.ISSUE
                permit.number = new_number
                permit.save()

                # إنشاء نموذج البنود
                StorePermitItemFormSet = inlineformset_factory(
                    StorePermit, StorePermitItem,
                    form=StorePermitItemForm, extra=1, can_delete=True
                )
                formset = StorePermitItemFormSet(request.POST, instance=permit)

                if formset.is_valid():
                    formset.save()
                    messages.success(request, 'تم إضافة إذن الصرف المخزني بنجاح')
                    return redirect('store_permit_detail', pk=permit.pk)
                else:
                    # في حالة وجود أخطاء في البنود، قم بحذف الإذن وإظهار الأخطاء
                    permit.delete()
                    for error in formset.errors:
                        messages.error(request, f'خطأ في البنود: {error}')
        else:
            # Crear el formset incluso cuando el formulario principal no es válido
            StorePermitItemFormSet = inlineformset_factory(
                StorePermit, StorePermitItem,
                form=StorePermitItemForm, extra=1, can_delete=True
            )
            formset = StorePermitItemFormSet(request.POST)

            # Mostrar errores del formulario principal
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'خطأ في حقل {field}: {error}')
    else:
        form = StorePermitForm(initial={
            'permit_type': StorePermit.ISSUE,
            'date': timezone.now(),
            'is_posted': True
        })
        StorePermitItemFormSet = inlineformset_factory(
            StorePermit, StorePermitItem,
            form=StorePermitItemForm, extra=1, can_delete=True
        )
        formset = StorePermitItemFormSet()

    return render(request, 'store_permits/form.html', {
        'form': form,
        'formset': formset,
        'title': 'إضافة إذن صرف مخزني جديد',
        'permit_type': 'issue'
    })

@login_required
def store_permit_add_receive(request):
    """إضافة إذن استلام مخزني جديد"""
    # إنشاء رقم مستند جديد
    last_permit = StorePermit.objects.order_by('-id').first()
    new_number = f"REC-{1:04d}" if not last_permit else f"REC-{int(last_permit.number.split('-')[1]) + 1:04d}"

    # إنشاء نموذج البيانات الرئيسي
    if request.method == 'POST':
        form = StorePermitForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                permit = form.save(commit=False)
                permit.permit_type = StorePermit.RECEIVE
                permit.number = new_number
                permit.save()

                # إنشاء نموذج البنود
                StorePermitItemFormSet = inlineformset_factory(
                    StorePermit, StorePermitItem,
                    form=StorePermitItemForm, extra=1, can_delete=True
                )
                formset = StorePermitItemFormSet(request.POST, instance=permit)

                if formset.is_valid():
                    formset.save()
                    messages.success(request, 'تم إضافة إذن الاستلام المخزني بنجاح')
                    return redirect('store_permit_detail', pk=permit.pk)
                else:
                    # في حالة وجود أخطاء في البنود، قم بحذف الإذن وإظهار الأخطاء
                    permit.delete()
                    print("أخطاء في نموذج البنود:", formset.errors)

                    # عرض تفاصيل الأخطاء
                    for i, form_errors in enumerate(formset.errors):
                        for field, errors in form_errors.items():
                            for error in errors:
                                messages.error(request, f'خطأ في البند #{i+1} - حقل {field}: {error}')

                    # إذا لم تكن هناك رسائل خطأ محددة، أضف رسالة عامة
                    if not messages.get_messages(request):
                        messages.error(request, 'حدث خطأ أثناء حفظ بنود الإذن. يرجى التحقق من البيانات المدخلة.')
        else:
            # Crear el formset incluso cuando el formulario principal no es válido
            StorePermitItemFormSet = inlineformset_factory(
                StorePermit, StorePermitItem,
                form=StorePermitItemForm, extra=1, can_delete=True
            )
            formset = StorePermitItemFormSet(request.POST)

            # Mostrar errores del formulario principal
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'خطأ في حقل {field}: {error}')
    else:
        form = StorePermitForm(initial={
            'permit_type': StorePermit.RECEIVE,
            'date': timezone.now(),
            'is_posted': True
        })
        StorePermitItemFormSet = inlineformset_factory(
            StorePermit, StorePermitItem,
            form=StorePermitItemForm, extra=1, can_delete=True
        )
        formset = StorePermitItemFormSet()

    return render(request, 'store_permits/form.html', {
        'form': form,
        'formset': formset,
        'title': 'إضافة إذن استلام مخزني جديد',
        'permit_type': 'receive'
    })

@login_required
def store_permit_detail(request, pk):
    """عرض تفاصيل إذن مخزني"""
    permit = get_object_or_404(StorePermit, pk=pk)
    return render(request, 'store_permits/detail.html', {
        'permit': permit
    })

@login_required
def store_permit_edit(request, pk):
    """تعديل إذن مخزني"""
    permit = get_object_or_404(StorePermit, pk=pk)

    if request.method == 'POST':
        form = StorePermitForm(request.POST, instance=permit)
        if form.is_valid():
            with transaction.atomic():
                permit = form.save()

                # إنشاء نموذج البنود
                StorePermitItemFormSet = inlineformset_factory(
                    StorePermit, StorePermitItem,
                    form=StorePermitItemForm, extra=1, can_delete=True
                )
                formset = StorePermitItemFormSet(request.POST, instance=permit)

                if formset.is_valid():
                    formset.save()
                    messages.success(request, 'تم تعديل الإذن المخزني بنجاح')
                    return redirect('store_permit_detail', pk=permit.pk)
                else:
                    print("أخطاء في نموذج البنود (تعديل):", formset.errors)

                    # عرض تفاصيل الأخطاء
                    for i, form_errors in enumerate(formset.errors):
                        for field, errors in form_errors.items():
                            for error in errors:
                                messages.error(request, f'خطأ في البند #{i+1} - حقل {field}: {error}')

                    # إذا لم تكن هناك رسائل خطأ محددة، أضف رسالة عامة
                    if not messages.get_messages(request):
                        messages.error(request, 'حدث خطأ أثناء حفظ بنود الإذن. يرجى التحقق من البيانات المدخلة.')
        else:
            # Crear el formset incluso cuando el formulario principal no es válido
            StorePermitItemFormSet = inlineformset_factory(
                StorePermit, StorePermitItem,
                form=StorePermitItemForm, extra=1, can_delete=True
            )
            formset = StorePermitItemFormSet(request.POST, instance=permit)

            # Mostrar errores del formulario principal
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'خطأ في حقل {field}: {error}')
    else:
        form = StorePermitForm(instance=permit)
        StorePermitItemFormSet = inlineformset_factory(
            StorePermit, StorePermitItem,
            form=StorePermitItemForm, extra=1, can_delete=True
        )
        formset = StorePermitItemFormSet(instance=permit)

    return render(request, 'store_permits/form.html', {
        'form': form,
        'formset': formset,
        'title': 'تعديل إذن مخزني',
        'permit_type': permit.permit_type
    })

@login_required
def store_permit_delete(request, pk):
    """حذف إذن مخزني"""
    permit = get_object_or_404(StorePermit, pk=pk)

    if request.method == 'POST':
        # إلغاء ترحيل الإذن قبل الحذف إذا كان مرحلاً
        if permit.is_posted:
            permit.unpost_permit()

        # حذف الإذن
        permit.delete()
        messages.success(request, 'تم حذف الإذن المخزني بنجاح')
        return redirect('store_permit_list')

    return render(request, 'store_permits/delete.html', {
        'permit': permit
    })

@login_required
def store_permit_post(request, pk):
    """ترحيل إذن مخزني"""
    permit = get_object_or_404(StorePermit, pk=pk)

    if permit.is_posted:
        messages.warning(request, 'الإذن المخزني مرحل بالفعل')
    else:
        if permit.post_permit():
            messages.success(request, 'تم ترحيل الإذن المخزني بنجاح')
        else:
            messages.error(request, 'حدث خطأ أثناء ترحيل الإذن المخزني')

    return redirect('store_permit_detail', pk=permit.pk)

@login_required
def store_permit_unpost(request, pk):
    """إلغاء ترحيل إذن مخزني"""
    permit = get_object_or_404(StorePermit, pk=pk)

    if not permit.is_posted:
        messages.warning(request, 'الإذن المخزني غير مرحل بالفعل')
    else:
        if permit.unpost_permit():
            messages.success(request, 'تم إلغاء ترحيل الإذن المخزني بنجاح')
        else:
            messages.error(request, 'حدث خطأ أثناء إلغاء ترحيل الإذن المخزني')

    return redirect('store_permit_detail', pk=permit.pk)


@login_required
def store_permit_print(request, pk):
    """طباعة إذن مخزني"""
    permit = get_object_or_404(StorePermit, pk=pk)
    return render(request, 'store_permits/print.html', {
        'permit': permit
    })


