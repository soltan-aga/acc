from django.shortcuts import render
from django.utils import timezone
from hatchery.models import BatchEntry, BatchIncubation, BatchHatching, CulledSale
from inventory.models import Disinfectant

def farm_home(request):
    """
    عرض الصفحة الرئيسية للمزرعة
    """
    # يمكن إضافة إحصائيات أو معلومات أخرى هنا إذا كانت متوفرة
    batch_count = BatchEntry.objects.count()
    incubation_count = BatchIncubation.objects.count()
    hatching_count = BatchHatching.objects.count()
    sales_count = CulledSale.objects.count()

    # الدفعات الجاهزة للخروج (تاريخ الخروج المتوقع هو اليوم أو قبله)
    today = timezone.now().date()
    ready_to_hatch = BatchIncubation.objects.filter(
        expected_hatch_date__lte=today
    ).exclude(
        hatching__isnull=False  # استبعاد الدفعات التي خرجت بالفعل
    ).order_by('expected_hatch_date')[:5]

    # المطهرات منخفضة المخزون
    low_stock_disinfectants = []
    for disinfectant in Disinfectant.objects.filter(is_active=True):
        if disinfectant.stock_status in ["منخفض", "نفذ"]:
            low_stock_disinfectants.append(disinfectant)

    # آخر عمليات البيع
    recent_sales = CulledSale.objects.all().order_by('-invoice_date')[:5]

    context = {
        'batch_count': batch_count,
        'incubation_count': incubation_count,
        'hatching_count': hatching_count,
        'sales_count': sales_count,
        'ready_to_hatch': ready_to_hatch,
        'low_stock_disinfectants': low_stock_disinfectants,
        'recent_sales': recent_sales,
    }

    return render(request, 'farm/home.html', context)