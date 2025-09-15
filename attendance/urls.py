from django.urls import path
from . import views

app_name = 'attendance'

urlpatterns = [
    # 页面视图
    path('employee/', views.employee_attendance_view, name='employee_attendance'),
    path('admin/', views.admin_attendance_view, name='admin_attendance'),
    
    # API接口
    path('api/records/', views.get_attendance_records, name='api_get_records'),
    path('api/import/', views.import_attendance_records, name='api_import_records'),
    
    # 异常检测API
    path('api/detection/daily/', views.daily_anomaly_detection_api, name='api_daily_detection'),
    path('api/detection/manual/', views.manual_anomaly_detection_api, name='api_manual_detection'),
    
    # 数据同步API
    path('api/sync/monthly/', views.monthly_sync_api, name='api_monthly_sync'),
    path('api/sync/manual/', views.manual_sync_api, name='api_manual_sync'),
    
    # 统计报告API
    path('api/reports/daily/', views.daily_report_api, name='api_daily_report'),
    path('api/reports/weekly/', views.weekly_report_api, name='api_weekly_report'),
    path('api/reports/monthly/', views.monthly_report_api, name='api_monthly_report'),
    
    # 统计数据API
    path('api/statistics/daily/', views.daily_statistics_api, name='api_daily_statistics'),
]