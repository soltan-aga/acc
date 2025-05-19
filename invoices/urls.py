from django.urls import path
from . import views

urlpatterns = [
    # مسارات الفواتير
    path('invoices/', views.invoice_list, name='invoice_list'),
    path('invoices/create/', views.invoice_create, name='invoice_create'),
    path('invoices/<int:pk>/', views.invoice_detail, name='invoice_detail'),
    path('invoices/<int:pk>/edit/', views.invoice_edit, name='invoice_edit'),
    path('invoices/<int:pk>/delete/', views.invoice_delete, name='invoice_delete'),
    path('invoices/<int:pk>/post/', views.invoice_post, name='invoice_post'),
    path('invoices/<int:pk>/unpost/', views.invoice_unpost, name='invoice_unpost'),
    path('invoices/<int:pk>/print/', views.invoice_print, name='invoice_print'),

    # مسارات أنواع الفواتير
    path('invoices/sales/', views.sale_invoice_list, name='sale_invoice_list'),
    path('invoices/purchases/', views.purchase_invoice_list, name='purchase_invoice_list'),
    path('invoices/sale-returns/', views.sale_return_invoice_list, name='sale_return_invoice_list'),
    path('invoices/purchase-returns/', views.purchase_return_invoice_list, name='purchase_return_invoice_list'),

    # مسارات المدفوعات
    path('payments/', views.payment_list, name='payment_list'),
    path('payments/add/', views.payment_add, name='payment_add'),
    path('payments/<int:pk>/', views.payment_detail, name='payment_detail'),
    path('payments/<int:pk>/post/', views.payment_post, name='payment_post'),
    path('payments/<int:pk>/unpost/', views.payment_unpost, name='payment_unpost'),

    # مسارات التحصيلات والمدفوعات
    path('receipts/', views.receipt_list, name='receipt_list'),
    path('payments-to-suppliers/', views.payment_to_supplier_list, name='payment_to_supplier_list'),
]