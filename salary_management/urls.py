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
    
    # 薪资调整相关 (暂时注释，待实现)
    # path('adjustment/list/', views.salary_adjustment_list, name='salary_adjustment_list'),
    # path('adjustment/create/', views.salary_adjustment_create, name='salary_adjustment_create'),
    # path('adjustment/detail/<int:adjustment_id>/', views.salary_adjustment_detail, name='salary_adjustment_detail'),
    # path('adjustment/approve/<int:adjustment_id>/', views.salary_adjustment_approve, name='salary_adjustment_approve'),
    # path('adjustment/reject/<int:adjustment_id>/', views.salary_adjustment_reject, name='salary_adjustment_reject'),
    
    # 考勤薪资计算相关
    path('attendance/calculate/', views.attendance_salary_calculate, name='attendance_salary_calculate'),
    path('attendance/list/', views.attendance_salary_list, name='attendance_salary_list'),
    path('attendance/detail/<int:detail_id>/', views.attendance_salary_detail, name='attendance_salary_detail'),
    path('attendance/rules/', views.attendance_calculation_rules, name='attendance_calculation_rules'),
    
    # 考勤薪资计算API接口 (暂时注释，待实现)
    # path('api/batch-calculate/', views.api_batch_calculate_salary, name='api_batch_calculate_salary'),
    # path('api/salary-config/create/', views.api_create_salary_config, name='api_create_salary_config'),
    # path('api/salary-config/update/', views.api_update_salary_config, name='api_update_salary_config'),
    # path('api/salary-config/delete/', views.api_delete_salary_config, name='api_delete_salary_config'),
    # path('api/salary-adjustment/create/', views.api_create_salary_adjustment, name='api_create_salary_adjustment'),
    # path('api/salary-adjustment/approve/', views.api_approve_salary_adjustment, name='api_approve_salary_adjustment'),
    # path('api/salary-adjustment/reject/', views.api_reject_salary_adjustment, name='api_reject_salary_adjustment'),

    # 考勤薪资计算规则API (暂时注释，待实现)
    # path('api/attendance-rule/create/', views.api_create_attendance_rule, name='api_create_attendance_rule'),
    # path('api/attendance/preview/', views.api_preview_attendance_calculation, name='api_preview_attendance_calculation'),
    # path('api/attendance/delete/', views.api_delete_attendance_salary_record, name='api_delete_attendance_salary_record'),
]