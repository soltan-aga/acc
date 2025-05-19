from django.urls import path
from . import views

app_name = 'inventory'

urlpatterns = [
    # Home URL
    path('', views.home, name='home'),

    # Supplier URLs
    path('suppliers/', views.supplier_list, name='supplier_list'),
    path('suppliers/create/', views.supplier_create, name='supplier_create'),
    path('suppliers/<int:pk>/', views.supplier_detail, name='supplier_detail'),
    path('suppliers/<int:pk>/update/', views.supplier_update, name='supplier_update'),
    path('suppliers/<int:pk>/delete/', views.supplier_delete, name='supplier_delete'),

    # Disinfectant Category URLs
    path('categories/', views.category_list, name='category_list'),
    path('categories/create/', views.category_create, name='category_create'),
    path('categories/<int:pk>/', views.category_detail, name='category_detail'),
    path('categories/<int:pk>/update/', views.category_update, name='category_update'),
    path('categories/<int:pk>/delete/', views.category_delete, name='category_delete'),

    # Disinfectant URLs
    path('disinfectants/', views.disinfectant_list, name='disinfectant_list'),
    path('disinfectants/create/', views.disinfectant_create, name='disinfectant_create'),
    path('disinfectants/<int:pk>/', views.disinfectant_detail, name='disinfectant_detail'),
    path('disinfectants/<int:pk>/update/', views.disinfectant_update, name='disinfectant_update'),
    path('disinfectants/<int:pk>/delete/', views.disinfectant_delete, name='disinfectant_delete'),

    # Received Disinfectant URLs
    path('received/', views.received_list, name='received_list'),
    path('received/create/<int:disinfectant_id>/', views.received_create, name='received_create'),
    path('received/<int:pk>/', views.received_detail, name='received_detail'),
    path('received/<int:pk>/update/', views.received_update, name='received_update'),
    path('received/<int:pk>/delete/', views.received_delete, name='received_delete'),

    # Issued Disinfectant URLs
    path('issued/', views.issued_list, name='issued_list'),
    path('issued/create/<int:disinfectant_id>/', views.issued_create, name='issued_create'),
    path('issued/<int:pk>/', views.issued_detail, name='issued_detail'),
    path('issued/<int:pk>/update/', views.issued_update, name='issued_update'),
    path('issued/<int:pk>/delete/', views.issued_delete, name='issued_delete'),
]
