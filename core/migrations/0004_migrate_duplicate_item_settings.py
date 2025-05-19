from django.db import migrations

def migrate_duplicate_item_settings(apps, schema_editor):
    """
    نقل البيانات من الحقول القديمة إلى الحقل الجديد
    """
    SystemSettings = apps.get_model('core', 'SystemSettings')
    
    # الحصول على جميع إعدادات النظام
    for settings in SystemSettings.objects.all():
        # تحديد قيمة الحقل الجديد بناءً على قيم الحقول القديمة
        if settings.allow_duplicate_items:
            settings.duplicate_item_handling = 'allow_duplicate'
        else:
            settings.duplicate_item_handling = 'increase_quantity'
        
        # حفظ التغييرات
        settings.save()


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_systemsettings_duplicate_item_handling'),
    ]

    operations = [
        migrations.RunPython(migrate_duplicate_item_settings),
    ]
