from django.urls import path
from . import views

app_name = 'salary_management'

urlpatterns = [
    # 主要页面
    path('', views.salary_dashboard, name='dashboard'),
    path('grades/', views.salary_grade_list, name='grade_list'),
    path('configs/', views.employee_salary_config_list, name='config_list'),
    path('monthly/', views.monthly_salary_list, name='monthly_list'),
    path('calculate/', views.salary_calculate, name='calculate'),
    
    # 详情页面
    path('slip/<int:employee_id>/<str:salary_month>/', views.salary_slip, name='salary_slip'),
    path('print/<int:salary_id>/', views.print_salary_slip, name='print_salary_slip'),
    
    # 报表页面
    path('reports/department/', views.department_report, name='department_report'),
    path('reports/company/', views.company_summary, name='company_summary'),
    
    # 流程图页面
    path('workflow/', views.workflow_diagram, name='workflow'),
    
    # API接口
    path('api/preview/', views.api_preview_calculation, name='api_preview'),
    path('api/calculate/', views.api_calculate_salary, name='api_calculate'),
    path('api/update-status/', views.api_update_salary_status, name='api_update_status'),
    path('api/adjustment/', views.api_create_salary_adjustment, name='api_adjustment'),
    path('api/statistics/', views.api_salary_statistics, name='api_statistics'),# API接口
    path('api/employees/', views.api_get_employees, name='api_employees'),
    path('api/salary-grades/', views.api_get_salary_grades, name='api_salary_grades'),
    path('api/create-config/', views.api_create_salary_config, name='api_create_config'),
    path('api/config/<int:config_id>/', views.api_get_salary_config, name='api_get_config'),
    path('api/config/<int:config_id>/update/', views.api_update_salary_config, name='api_update_config'),
    path('api/config/<int:config_id>/deactivate/', views.api_deactivate_salary_config, name='api_deactivate_config'),
    path('api/history/<int:employee_id>/', views.api_get_salary_history, name='api_salary_history'),
    path('api/delete-record/', views.api_delete_salary_record, name='api_delete_record'),
    
    # 住房公积金比例相关API
    path('api/housing-fund-rate/update/', views.api_update_housing_fund_rate, name='api_update_housing_fund_rate'),
    path('api/housing-fund-rate/<int:employee_id>/', views.api_get_housing_fund_rate, name='api_get_housing_fund_rate'),
]