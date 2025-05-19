from django.urls import path
from . import views

app_name = 'hatchery'

urlpatterns = [
    # Home URL
    path('', views.home, name='home'),

    # BatchName URLs
    path('batch-names/', views.batch_name_list, name='batch_name_list'),
    path('batch-names/create/', views.batch_name_create, name='batch_name_create'),
    path('batch-names/<int:pk>/update/', views.batch_name_update, name='batch_name_update'),
    path('batch-names/<int:pk>/delete/', views.batch_name_delete, name='batch_name_delete'),

    # Batch URLs
    path('batches/', views.batch_list, name='batch_list'),
    path('batches/create/', views.batch_create, name='batch_create'),
    path('batches/<int:pk>/', views.batch_detail, name='batch_detail'),
    path('batches/<int:pk>/update/', views.batch_update, name='batch_update'),
    path('batches/<int:pk>/delete/', views.batch_delete, name='batch_delete'),

    # Incubation URLs
    path('incubations/', views.incubation_list, name='incubation_list'),
    path('incubations/create/<int:batch_id>/', views.incubation_create, name='incubation_create'),
    path('incubations/<int:pk>/', views.incubation_detail, name='incubation_detail'),
    path('incubations/<int:pk>/update/', views.incubation_update, name='incubation_update'),
    path('incubations/<int:pk>/delete/', views.incubation_delete, name='incubation_delete'),

    # Hatching URLs
    path('hatchings/', views.hatching_list, name='hatching_list'),
    path('hatchings/create/<int:incubation_id>/', views.hatching_create, name='hatching_create'),
    path('hatchings/<int:pk>/', views.hatching_detail, name='hatching_detail'),
    path('hatchings/<int:pk>/update/', views.hatching_update, name='hatching_update'),
    path('hatchings/<int:pk>/delete/', views.hatching_delete, name='hatching_delete'),

    # Customer URLs
    path('customers/', views.customer_list, name='customer_list'),
    path('customers/create/', views.customer_create, name='customer_create'),
    path('customers/<int:pk>/', views.customer_detail, name='customer_detail'),
    path('customers/<int:pk>/update/', views.customer_update, name='customer_update'),
    path('customers/<int:pk>/delete/', views.customer_delete, name='customer_delete'),

    # Culled Sale URLs
    path('culled-sales/', views.culled_sale_list, name='culled_sale_list'),
    path('culled-sales/create/<int:hatching_id>/', views.culled_sale_create, name='culled_sale_create'),
    path('culled-sales/<int:pk>/', views.culled_sale_detail, name='culled_sale_detail'),
    path('culled-sales/<int:pk>/update/', views.culled_sale_update, name='culled_sale_update'),
    path('culled-sales/<int:pk>/delete/', views.culled_sale_delete, name='culled_sale_delete'),

    # Disinfectant Category URLs
    path('disinfectant-categories/', views.disinfectant_category_list, name='disinfectant_category_list'),
    path('disinfectant-categories/create/', views.disinfectant_category_create, name='disinfectant_category_create'),
    path('disinfectant-categories/<int:pk>/update/', views.disinfectant_category_update, name='disinfectant_category_update'),
    path('disinfectant-categories/<int:pk>/delete/', views.disinfectant_category_delete, name='disinfectant_category_delete'),

    # Disinfectant Inventory URLs
    path('disinfectant-inventory/', views.disinfectant_inventory_list, name='disinfectant_inventory_list'),
    path('disinfectant-inventory/create/', views.disinfectant_inventory_create, name='disinfectant_inventory_create'),
    path('disinfectant-inventory/<int:pk>/', views.disinfectant_inventory_detail, name='disinfectant_inventory_detail'),
    path('disinfectant-inventory/<int:pk>/update/', views.disinfectant_inventory_update, name='disinfectant_inventory_update'),
    path('disinfectant-inventory/<int:pk>/delete/', views.disinfectant_inventory_delete, name='disinfectant_inventory_delete'),

    # Disinfectant Transaction URLs
    path('disinfectant-transactions/', views.disinfectant_transaction_list, name='disinfectant_transaction_list'),
    path('disinfectant-transactions/create/', views.disinfectant_transaction_create, name='disinfectant_transaction_create'),
    path('disinfectant-transactions/create/<int:disinfectant_id>/<str:transaction_type>/', views.disinfectant_transaction_create, name='disinfectant_transaction_create_specific'),
    path('disinfectant-transactions/<int:pk>/', views.disinfectant_transaction_detail, name='disinfectant_transaction_detail'),
    path('disinfectant-transactions/<int:pk>/update/', views.disinfectant_transaction_update, name='disinfectant_transaction_update'),
    path('disinfectant-transactions/<int:pk>/delete/', views.disinfectant_transaction_delete, name='disinfectant_transaction_delete'),

    # Batch Distribution URLs
    path('distributions/', views.distribution_list, name='distribution_list'),
    path('distributions/create/', views.distribution_create, name='distribution_create'),
    path('distributions/create/<int:hatching_id>/', views.distribution_create, name='distribution_create_specific'),
    path('distributions/<int:pk>/', views.distribution_detail, name='distribution_detail'),
    path('distributions/<int:pk>/update/', views.distribution_update, name='distribution_update'),
    path('distributions/<int:pk>/delete/', views.distribution_delete, name='distribution_delete'),

    # Reports URLs
    path('reports/daily/', views.daily_report, name='daily_report'),

    # API URLs
    path('api/incubation/<int:pk>/', views.incubation_api, name='incubation_api'),
    path('api/customer/create/', views.customer_api_create, name='customer_api_create'),
]
