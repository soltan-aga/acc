from django import template

register = template.Library()

@register.filter
def getattribute(obj, attr):
    """
    فلتر للوصول إلى خاصية ديناميكية في كائن
    مثال: {{ form|getattribute:"status_"|add:employee_id }}
    """
    try:
        # محاولة الوصول إلى الحقل باستخدام الاسم المركب مباشرة
        return obj[attr]
    except (KeyError, AttributeError):
        # إذا فشل، نعيد None
        return None

@register.filter
def getitem(obj, key):
    """
    فلتر للوصول إلى عنصر في قاموس أو كائن
    مثال: {{ form|getitem:field_name }}
    """
    try:
        return obj[key]
    except (KeyError, AttributeError):
        return None

@register.filter
def add(value, arg):
    """
    فلتر لإضافة قيمة إلى قيمة أخرى
    مثال: {{ "status_"|add:employee_id }} أو {{ year|add:offset }}
    """
    try:
        # محاولة تحويل القيم إلى أرقام إذا كانت أرقام
        if isinstance(value, (int, float)) or (isinstance(value, str) and value.isdigit()):
            if isinstance(arg, (int, float)) or (isinstance(arg, str) and arg.isdigit()):
                return int(value) + int(arg)
        # إذا لم تكن أرقام، نتعامل معها كنصوص
        return str(value) + str(arg)
    except (ValueError, TypeError):
        # في حالة حدوث أي خطأ، نعيد النصوص مدمجة
        return str(value) + str(arg)

@register.filter(name='get_range')
def get_range(value):
    """
    فلتر لإنشاء نطاق من 1 إلى القيمة المحددة
    مثال: {% for i in 5|get_range %}
    """
    return range(1, int(value) + 1)
