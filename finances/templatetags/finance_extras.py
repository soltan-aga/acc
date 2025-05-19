from django import template

register = template.Library()

@register.filter
def div(value, arg):
    """
    تقسيم القيمة على المعامل
    """
    try:
        return float(value) / float(arg)
    except (ValueError, ZeroDivisionError):
        return 0

@register.filter
def mul(value, arg):
    """
    ضرب القيمة في المعامل
    """
    try:
        return float(value) * float(arg)
    except ValueError:
        return 0

@register.filter
def abs_value(value):
    """
    القيمة المطلقة للرقم
    """
    try:
        return abs(float(value))
    except ValueError:
        return 0
