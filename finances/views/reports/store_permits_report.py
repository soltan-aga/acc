from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.utils import timezone

from ...models import StorePermit, StorePermitItem
from core.models import Store, SystemSettings, Driver, Representative
from products.models import Product, Category

@login_required
def store_permits_report(request):
    """عرض تقرير بنود الأذونات المخزنية"""
    # الحصول على إعدادات النظام
    settings = SystemSettings.get_settings()

    # البحث والتصفية - نبدأ بجميع بنود الأذونات
    permit_items = StorePermitItem.objects.select_related(
        'permit', 'product', 'product_unit', 'product_unit__unit',
        'permit__store', 'permit__driver', 'permit__representative'
    ).order_by('-permit__date')

    # تصفية حسب نوع الإذن
    permit_type = request.GET.get('permit_type')
    if permit_type:
        permit_items = permit_items.filter(permit__permit_type=permit_type)

    # تصفية حسب المخزن
    store_id = request.GET.get('store')
    if store_id:
        permit_items = permit_items.filter(permit__store_id=store_id)

    # تصفية حسب حالة الترحيل
    is_posted = request.GET.get('is_posted')
    if is_posted == 'yes':
        permit_items = permit_items.filter(permit__is_posted=True)
    elif is_posted == 'no':
        permit_items = permit_items.filter(permit__is_posted=False)

    # تصفية حسب التاريخ
    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')

    if from_date:
        permit_items = permit_items.filter(permit__date__date__gte=from_date)

    if to_date:
        permit_items = permit_items.filter(permit__date__date__lte=to_date)

    # تصفية حسب الشخص (المستلم/المرسل)
    person_name = request.GET.get('person_name')
    if person_name:
        permit_items = permit_items.filter(permit__person_name__icontains=person_name)

    # تصفية حسب السائق
    driver_id = request.GET.get('driver')
    if driver_id:
        permit_items = permit_items.filter(permit__driver_id=driver_id)

    # تصفية حسب المندوب
    representative_id = request.GET.get('representative')
    if representative_id:
        permit_items = permit_items.filter(permit__representative_id=representative_id)

    # تصفية حسب المنتج
    product_id = request.GET.get('product')
    if product_id:
        permit_items = permit_items.filter(product_id=product_id)

    # تصفية حسب قسم المنتج
    category_id = request.GET.get('category')
    if category_id:
        permit_items = permit_items.filter(product__category_id=category_id)

    # البحث العام
    search_query = request.GET.get('q')
    if search_query:
        permit_items = permit_items.filter(
            Q(permit__number__icontains=search_query) |
            Q(permit__person_name__icontains=search_query) |
            Q(product__name__icontains=search_query) |
            Q(notes__icontains=search_query)
        )

    # الحصول على قوائم للفلاتر
    stores = Store.objects.all()
    drivers = Driver.objects.all()
    representatives = Representative.objects.all()
    products = Product.objects.all()
    categories = Category.objects.all()

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
        },
        {
            'name': 'person_name',
            'label': 'المستلم/المرسل',
            'type': 'text',
            'value': person_name
        },
        {
            'name': 'driver',
            'label': 'السائق',
            'type': 'select',
            'options': drivers,
            'value': driver_id
        },
        {
            'name': 'representative',
            'label': 'المندوب',
            'type': 'select',
            'options': representatives,
            'value': representative_id
        },
        {
            'name': 'product',
            'label': 'المنتج',
            'type': 'select',
            'options': products,
            'value': product_id
        },
        {
            'name': 'category',
            'label': 'قسم المنتج',
            'type': 'select',
            'options': categories,
            'value': category_id
        }
    ]

    return render(request, 'finances/reports/store_permits_report.html', {
        'permit_items': permit_items,
        'permit_filters': permit_filters,
        'from_date': from_date,
        'to_date': to_date,
        'search_query': search_query,
        'settings': settings,
        'title': 'تقرير بنود الأذونات المخزنية'
    })

@login_required
def store_permits_report_print(request):
    """طباعة تقرير بنود الأذونات المخزنية"""
    # نفس منطق التصفية الموجود في الدالة السابقة
    permit_items = StorePermitItem.objects.select_related(
        'permit', 'product', 'product_unit', 'product_unit__unit',
        'permit__store', 'permit__driver', 'permit__representative'
    ).order_by('-permit__date')

    # تصفية حسب نوع الإذن
    permit_type = request.GET.get('permit_type')
    if permit_type:
        permit_items = permit_items.filter(permit__permit_type=permit_type)

    # تصفية حسب المخزن
    store_id = request.GET.get('store')
    if store_id:
        permit_items = permit_items.filter(permit__store_id=store_id)

    # تصفية حسب حالة الترحيل
    is_posted = request.GET.get('is_posted')
    if is_posted == 'yes':
        permit_items = permit_items.filter(permit__is_posted=True)
    elif is_posted == 'no':
        permit_items = permit_items.filter(permit__is_posted=False)

    # تصفية حسب التاريخ
    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')

    if from_date:
        permit_items = permit_items.filter(permit__date__date__gte=from_date)

    if to_date:
        permit_items = permit_items.filter(permit__date__date__lte=to_date)

    # تصفية حسب الشخص (المستلم/المرسل)
    person_name = request.GET.get('person_name')
    if person_name:
        permit_items = permit_items.filter(permit__person_name__icontains=person_name)

    # تصفية حسب السائق
    driver_id = request.GET.get('driver')
    if driver_id:
        permit_items = permit_items.filter(permit__driver_id=driver_id)

    # تصفية حسب المندوب
    representative_id = request.GET.get('representative')
    if representative_id:
        permit_items = permit_items.filter(permit__representative_id=representative_id)

    # تصفية حسب المنتج
    product_id = request.GET.get('product')
    if product_id:
        permit_items = permit_items.filter(product_id=product_id)

    # تصفية حسب قسم المنتج
    category_id = request.GET.get('category')
    if category_id:
        permit_items = permit_items.filter(product__category_id=category_id)

    # البحث العام
    search_query = request.GET.get('q')
    if search_query:
        permit_items = permit_items.filter(
            Q(permit__number__icontains=search_query) |
            Q(permit__person_name__icontains=search_query) |
            Q(product__name__icontains=search_query) |
            Q(notes__icontains=search_query)
        )

    # الحصول على إعدادات النظام
    settings = SystemSettings.get_settings()

    return render(request, 'finances/reports/store_permits_report_print.html', {
        'permit_items': permit_items,
        'from_date': from_date,
        'to_date': to_date,
        'settings': settings,
        'title': 'طباعة تقرير بنود الأذونات المخزنية',
        'print_date': timezone.now()
    })
