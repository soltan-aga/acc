from django.urls import path
from . import views

urlpatterns = [
    # Product Transaction URLs
    path('inventory/', views.product_inventory, name='product_inventory'),
    path('transactions/', views.product_transaction_list, name='product_transaction_list'),
    path('transactions/add/', views.product_transaction_add, name='product_transaction_add'),
    path('transactions/<int:pk>/', views.product_transaction_detail, name='product_transaction_detail'),
    path('transactions/<int:pk>/edit/', views.product_transaction_edit, name='product_transaction_edit'),
    path('transactions/<int:pk>/delete/', views.product_transaction_delete, name='product_transaction_delete'),
    path('transactions/<int:pk>/post/', views.product_transaction_post, name='product_transaction_post'),
    path('transactions/<int:pk>/unpost/', views.product_transaction_unpost, name='product_transaction_unpost'),
    path('products/<int:product_id>/movement/', views.product_movement_report, name='product_movement_report'),

    # تقارير مالية
    path('reports/financial-transactions/', views.financial_transactions_report, name='financial_transactions_report'),
    path('reports/financial-transactions/print/', views.financial_transactions_print, name='financial_transactions_print'),
    path('reports/income-expense/', views.income_expense_report, name='income_expense_report'),
    path('reports/income-expense/print/', views.income_expense_print, name='income_expense_print'),
    path('reports/store-permits/', views.store_permits_report, name='store_permits_report'),
    path('reports/store-permits/print/', views.store_permits_report_print, name='store_permits_report_print'),

    # Expense Categories
    path('expense-categories/', views.expense_category_list, name='expense_category_list'),
    path('expense-categories/add/', views.expense_category_add, name='expense_category_add'),
    path('expense-categories/<int:pk>/edit/', views.expense_category_edit, name='expense_category_edit'),
    path('expense-categories/<int:pk>/delete/', views.expense_category_delete, name='expense_category_delete'),

    # Income Categories
    path('income-categories/', views.income_category_list, name='income_category_list'),
    path('income-categories/add/', views.income_category_add, name='income_category_add'),
    path('income-categories/<int:pk>/edit/', views.income_category_edit, name='income_category_edit'),
    path('income-categories/<int:pk>/delete/', views.income_category_delete, name='income_category_delete'),

    # Expenses
    path('expenses/', views.expense_list, name='expense_list'),
    path('expenses/add/', views.expense_add, name='expense_add'),
    path('expenses/<int:pk>/', views.expense_detail, name='expense_detail'),
    path('expenses/<int:pk>/edit/', views.expense_edit, name='expense_edit'),
    path('expenses/<int:pk>/delete/', views.expense_delete, name='expense_delete'),
    path('expenses/<int:pk>/post/', views.expense_post, name='expense_post'),
    path('expenses/<int:pk>/unpost/', views.expense_unpost, name='expense_unpost'),

    # Incomes
    path('incomes/', views.income_list, name='income_list'),
    path('incomes/add/', views.income_add, name='income_add'),
    path('incomes/<int:pk>/', views.income_detail, name='income_detail'),
    path('incomes/<int:pk>/edit/', views.income_edit, name='income_edit'),
    path('incomes/<int:pk>/delete/', views.income_delete, name='income_delete'),
    path('incomes/<int:pk>/post/', views.income_post, name='income_post'),
    path('incomes/<int:pk>/unpost/', views.income_unpost, name='income_unpost'),

    # Safe Deposits
    path('safe-deposits/', views.safe_deposit_list, name='safe_deposit_list'),
    path('safe-deposits/add/', views.safe_deposit_add, name='safe_deposit_add'),
    path('safe-deposits/<int:pk>/', views.safe_deposit_detail, name='safe_deposit_detail'),
    path('safe-deposits/<int:pk>/edit/', views.safe_deposit_edit, name='safe_deposit_edit'),
    path('safe-deposits/<int:pk>/delete/', views.safe_deposit_delete, name='safe_deposit_delete'),
    path('safe-deposits/<int:pk>/post/', views.safe_deposit_post, name='safe_deposit_post'),
    path('safe-deposits/<int:pk>/unpost/', views.safe_deposit_unpost, name='safe_deposit_unpost'),

    # Safe Withdrawals
    path('safe-withdrawals/', views.safe_withdrawal_list, name='safe_withdrawal_list'),
    path('safe-withdrawals/add/', views.safe_withdrawal_add, name='safe_withdrawal_add'),
    path('safe-withdrawals/<int:pk>/', views.safe_withdrawal_detail, name='safe_withdrawal_detail'),
    path('safe-withdrawals/<int:pk>/edit/', views.safe_withdrawal_edit, name='safe_withdrawal_edit'),
    path('safe-withdrawals/<int:pk>/delete/', views.safe_withdrawal_delete, name='safe_withdrawal_delete'),
    path('safe-withdrawals/<int:pk>/post/', views.safe_withdrawal_post, name='safe_withdrawal_post'),
    path('safe-withdrawals/<int:pk>/unpost/', views.safe_withdrawal_unpost, name='safe_withdrawal_unpost'),

    # Store Permit URLs
    path('store-permits/', views.store_permit_list, name='store_permit_list'),
    path('store-permits/add/', views.store_permit_add, name='store_permit_add'),
    path('store-permits/add-issue/', views.store_permit_add_issue, name='store_permit_add_issue'),
    path('store-permits/add-receive/', views.store_permit_add_receive, name='store_permit_add_receive'),
    path('store-permits/<int:pk>/', views.store_permit_detail, name='store_permit_detail'),
    path('store-permits/<int:pk>/edit/', views.store_permit_edit, name='store_permit_edit'),
    path('store-permits/<int:pk>/delete/', views.store_permit_delete, name='store_permit_delete'),
    path('store-permits/<int:pk>/post/', views.store_permit_post, name='store_permit_post'),
    path('store-permits/<int:pk>/unpost/', views.store_permit_unpost, name='store_permit_unpost'),
    path('store-permits/<int:pk>/print/', views.store_permit_print, name='store_permit_print'),
]
