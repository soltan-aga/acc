from django.urls import path
from . import views

app_name = 'employees'

urlpatterns = [
    # صفحات الموظفين
    path('', views.employee_list, name='employee_list'),
    path('employee/<int:pk>/', views.employee_detail, name='employee_detail'),
    path('employee/add/', views.employee_add, name='employee_add'),
    path('employee/<int:pk>/edit/', views.employee_edit, name='employee_edit'),
    path('employee/<int:pk>/delete/', views.employee_delete, name='employee_delete'),

    # صفحات الحضور والغياب
    path('attendance/', views.attendance_list, name='attendance_list'),
    path('attendance/daily/', views.attendance_daily, name='attendance_daily'),
    path('attendance/monthly/', views.attendance_monthly, name='attendance_monthly'),
    path('attendance/add/', views.attendance_add, name='attendance_add'),
    path('attendance/bulk-add/', views.attendance_bulk_add, name='attendance_bulk_add'),
    path('attendance/<int:pk>/delete/', views.attendance_delete, name='attendance_delete'),

    # صفحات السلف
    path('loans/', views.loan_list, name='loan_list'),
    path('loan/<int:pk>/', views.loan_detail, name='loan_detail'),
    path('loan/add/', views.loan_add, name='loan_add'),
    path('loan/<int:pk>/edit/', views.loan_edit, name='loan_edit'),
    path('loan/<int:pk>/post/', views.loan_post, name='loan_post'),
    path('loan/<int:pk>/unpost/', views.loan_unpost, name='loan_unpost'),
    path('loan/<int:pk>/delete/', views.loan_delete, name='loan_delete'),

    # صفحات المرتبات
    path('salaries/', views.salary_list, name='salary_list'),
    path('salary/<int:pk>/', views.salary_detail, name='salary_detail'),
    path('salary/add/', views.salary_add, name='salary_add'),
    path('salary/<int:pk>/edit/', views.salary_edit, name='salary_edit'),
    path('salary/<int:pk>/post/', views.salary_post, name='salary_post'),
    path('salary/<int:pk>/unpost/', views.salary_unpost, name='salary_unpost'),
    path('salary/<int:pk>/delete/', views.salary_delete, name='salary_delete'),
    path('salary/generate-monthly/', views.salary_generate_monthly, name='salary_generate_monthly'),

    # التقارير
    path('reports/attendance/daily/', views.report_attendance_daily, name='report_attendance_daily'),
    path('reports/attendance/monthly/', views.report_attendance_monthly, name='report_attendance_monthly'),
    path('reports/employee/<int:pk>/attendance/', views.report_employee_attendance, name='report_employee_attendance'),
    path('reports/employee/<int:pk>/loans/', views.report_employee_loans, name='report_employee_loans'),
    path('reports/loans/monthly/', views.report_monthly_loans, name='report_monthly_loans'),
]
