# نظام إدارة المخازن والمحاسبة (ACC)

نظام متكامل لإدارة المخازن والمحاسبة، يتيح إدارة الشركات والفروع والمخازن والخزن والعملاء والموردين والمنتجات والفواتير والتقارير.

## المميزات

* إدارة الشركات والفروع والمخازن والخزن
* إدارة العملاء والموردين
* إدارة المناديب والسائقين
* إدارة المنتجات وأقسامها ووحدات القياس
* إدارة الفواتير (بيع، شراء، مرتجع بيع، مرتجع شراء)
* إدارة المعاملات المالية
* إدارة حركات الحسابات والمنتجات

## التطبيقات الرئيسية

* **core**: الشركات والفروع والمخازن والخزن والمناديب والسائقين وجهات الاتصال
* **products**: المنتجات وأقسامها ووحدات القياس
* **invoices**: الفواتير وبنودها
* **finances**: حركات الخزنة وحركات حسابات العملاء والموردين وحركات المنتجات

## متطلبات التشغيل

* Python 3.8 أو أحدث
* Django 4.0 أو أحدث
* Pillow

## التثبيت من الصفر

1. قم بإنشاء مجلد جديد للمشروع:
   ```
   mkdir acc
   cd acc
   ```

2. قم بإنشاء بيئة افتراضية:
   ```
   python -m venv venv
   ```

3. تفعيل البيئة الافتراضية:
   * ويندوز:
     ```
     venv\Scripts\activate
     ```
   * لينكس/ماك:
     ```
     source venv/bin/activate
     ```

4. تثبيت المتطلبات:
   ```
   pip install django pillow
   ```

5. إنشاء مشروع Django:
   ```
   django-admin startproject acc .
   ```

6. إنشاء التطبيقات:
   ```
   python manage.py startapp core
   python manage.py startapp products
   python manage.py startapp invoices
   python manage.py startapp finances
   ```

7. إضافة التطبيقات إلى INSTALLED_APPS في acc/settings.py:
   ```python
   INSTALLED_APPS = [
       # ...
       'core',
       'products',
       'invoices',
       'finances',
   ]
   ```

8. تكوين إعدادات الوسائط والملفات الثابتة في acc/settings.py:
   ```python
   STATIC_URL = "static/"
   STATIC_ROOT = BASE_DIR / 'staticfiles'
   STATICFILES_DIRS = [
       BASE_DIR / 'static',
   ]

   MEDIA_URL = '/media/'
   MEDIA_ROOT = BASE_DIR / 'media'
   ```

9. إنشاء مجلدات للملفات الثابتة والوسائط:
   ```
   mkdir static media
   ```

10. تكوين ملفات URL:
    ```python
    # acc/urls.py
    from django.contrib import admin
    from django.urls import path, include
    from django.conf import settings
    from django.conf.urls.static import static

    urlpatterns = [
        path('admin/', admin.site.urls),
        path('', include('core.urls')),
    ]

    if settings.DEBUG:
        urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    ```

11. إنشاء نماذج التطبيقات وتسجيلها في admin.py

12. إجراء الهجرات:
    ```
    python manage.py makemigrations
    python manage.py migrate
    ```

13. إنشاء حساب مدير:
    ```
    python manage.py createsuperuser
    ```

14. تشغيل الخادم:
    ```
    python manage.py runserver
    ```

## حل مشاكل التبعيات الدائرية

عند حدوث مشاكل في التبعيات الدائرية بين التطبيقات، يمكن حل ذلك باستخدام:

1. استخدام الاقتباسات في تعريف العلاقات:
   ```python
   invoice = models.ForeignKey('invoices.Invoice', on_delete=models.SET_NULL, ...)
   ```

2. استخدام التطبيقات المنفصلة وترتيب الهجرات بشكل مناسب.

## الاستخدام

1. قم بزيارة `http://127.0.0.1:8000/` للوصول إلى الصفحة الرئيسية.
2. قم بزيارة `http://127.0.0.1:8000/admin/` للوصول إلى لوحة التحكم. 