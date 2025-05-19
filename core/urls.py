from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),

    # Company URLs
    path('companies/', views.company_list, name='company_list'),
    path('companies/add/', views.company_add, name='company_add'),
    path('companies/<int:pk>/', views.company_detail, name='company_detail'),
    path('companies/<int:pk>/edit/', views.company_edit, name='company_edit'),
    path('companies/<int:pk>/delete/', views.company_delete, name='company_delete'),

    # Branch URLs
    path('branches/', views.branch_list, name='branch_list'),
    path('branches/add/', views.branch_add, name='branch_add'),
    path('branches/<int:pk>/', views.branch_detail, name='branch_detail'),
    path('branches/<int:pk>/edit/', views.branch_edit, name='branch_edit'),
    path('branches/<int:pk>/delete/', views.branch_delete, name='branch_delete'),

    # Store URLs
    path('stores/', views.store_list, name='store_list'),
    path('stores/add/', views.store_add, name='store_add'),
    path('stores/<int:pk>/', views.store_detail, name='store_detail'),
    path('stores/<int:pk>/edit/', views.store_edit, name='store_edit'),
    path('stores/<int:pk>/delete/', views.store_delete, name='store_delete'),

    # Safe URLs
    path('safes/', views.safe_list, name='safe_list'),
    path('safes/add/', views.safe_add, name='safe_add'),
    path('safes/<int:pk>/', views.safe_detail, name='safe_detail'),
    path('safes/<int:pk>/edit/', views.safe_edit, name='safe_edit'),
    path('safes/<int:pk>/delete/', views.safe_delete, name='safe_delete'),

    # Representative URLs
    path('representatives/', views.representative_list, name='representative_list'),
    path('representatives/add/', views.representative_add, name='representative_add'),
    path('representatives/<int:pk>/', views.representative_detail, name='representative_detail'),
    path('representatives/<int:pk>/edit/', views.representative_edit, name='representative_edit'),
    path('representatives/<int:pk>/delete/', views.representative_delete, name='representative_delete'),

    # Driver URLs
    path('drivers/', views.driver_list, name='driver_list'),
    path('drivers/add/', views.driver_add, name='driver_add'),
    path('drivers/<int:pk>/', views.driver_detail, name='driver_detail'),
    path('drivers/<int:pk>/edit/', views.driver_edit, name='driver_edit'),
    path('drivers/<int:pk>/delete/', views.driver_delete, name='driver_delete'),

    # Contact URLs (General)
    path('contacts/', views.contact_list, name='contact_list'),
    path('contacts/add/', views.contact_add, name='contact_add'),
    path('contacts/<int:pk>/', views.contact_detail, name='contact_detail'),
    path('contacts/<int:pk>/edit/', views.contact_edit, name='contact_edit'),
    path('contacts/<int:pk>/delete/', views.contact_delete, name='contact_delete'),
    path('contacts/<int:pk>/statement/', views.contact_statement, name='contact_statement'),

    # Customer URLs
    path('customers/', views.customer_list, name='customer_list'),
    path('customers/add/', views.customer_add, name='customer_add'),

    # Supplier URLs
    path('suppliers/', views.supplier_list, name='supplier_list'),
    path('suppliers/add/', views.supplier_add, name='supplier_add'),

    # System Settings URL
    path('settings/', views.system_settings, name='system_settings'),

    # API URLs
    path('api/contact/<int:pk>/balance/', views.contact_balance_api, name='contact_balance_api'),
]