from django.urls import path
from . import views

urlpatterns = [
    path('employee/center/', views.employee_center, name='employee_center'),
    path('employee/salary/list/', views.employee_salary_list, name='employee_salary_list'),
    path('employee/salary/<int:salary_id>/', views.employee_salary_detail, name='employee_salary_detail'),
    path('employee/salary/<int:salary_id>/download/', views.employee_salary_download, name='employee_salary_download'),
]