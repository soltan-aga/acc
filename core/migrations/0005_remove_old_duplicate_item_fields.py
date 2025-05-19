from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_migrate_duplicate_item_settings'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='systemsettings',
            name='allow_duplicate_items',
        ),
        migrations.RemoveField(
            model_name='systemsettings',
            name='auto_increase_quantity',
        ),
    ]
