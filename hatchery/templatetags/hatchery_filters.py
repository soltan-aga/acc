from django import template
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation

register = template.Library()

@register.filter
def smart_number(value):
    """
    تقريب الأرقام إلى رقم صحيح إذا كانت الأرقام بعد الفاصلة أصفار
    مثال: 10.00 -> 10, 10.50 -> 10.5
    """
    if value is None:
        return "0"

    try:
        # تحويل القيمة إلى Decimal للتعامل مع الأرقام بدقة
        decimal_value = Decimal(str(value))

        # التحقق مما إذا كان الرقم صحيحًا (بدون كسور)
        if decimal_value == decimal_value.to_integral_exact():
            return str(int(decimal_value))

        # إزالة الأصفار الزائدة بعد الفاصلة العشرية
        # مثال: 10.50 -> 10.5, 10.00 -> 10
        normalized = decimal_value.normalize()

        # إذا كان الرقم بعد التطبيع صحيحًا، نعيده كرقم صحيح
        if normalized == normalized.to_integral_exact():
            return str(int(normalized))

        # وإلا نعيد الرقم بعد التطبيع (بدون أصفار زائدة)
        return str(normalized)

    except (ValueError, TypeError, InvalidOperation):
        # في حالة حدوث أي خطأ، نعيد القيمة كما هي
        return str(value)

@register.filter
def format_decimal(value, decimal_places=2):
    """
    تنسيق الأرقام العشرية مع إزالة الأصفار الزائدة
    مثال: format_decimal(10.00) -> 10, format_decimal(10.50) -> 10.5
    """
    if value is None:
        return "0"

    try:
        # تحويل القيمة إلى Decimal للتعامل مع الأرقام بدقة
        decimal_value = Decimal(str(value))

        # تقريب الرقم إلى عدد المنازل العشرية المطلوبة
        rounded = decimal_value.quantize(Decimal('0.' + '0' * int(decimal_places)), rounding=ROUND_HALF_UP)

        # إزالة الأصفار الزائدة
        normalized = rounded.normalize()

        # إذا كان الرقم بعد التطبيع صحيحًا، نعيده كرقم صحيح
        if normalized == normalized.to_integral_exact():
            return str(int(normalized))

        # وإلا نعيد الرقم بعد التطبيع (بدون أصفار زائدة)
        return str(normalized)

    except (ValueError, TypeError, InvalidOperation):
        # في حالة حدوث أي خطأ، نعيد القيمة كما هي
        return str(value)
