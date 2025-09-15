from django.urls import path

from department.views import DepartmentAddView, DepartmentListView, DepartmentUpdateView, DepartmentDeleteView, \
    DepartmentDetailView, DepartmentBatchDeleteView, department_list, department_employees, employee_detail

urlpatterns = [
    # 前端页面路由
    path('', department_list, name='department_list'),
    path('<int:department_id>/employees/', department_employees, name='department_employees'),
    path('employee/<int:employee_id>/', employee_detail, name='employee_detail'),
    
    # API路由
    path('insert/',DepartmentAddView.as_view(),name='insert'),
    path('add/',DepartmentAddView.as_view(),name='add'),  # 添加别名用于前端
    path('getList/',DepartmentListView.as_view(),name='list'),
    path('update/',DepartmentUpdateView.as_view(),name='update'),
    path('delete/',DepartmentDeleteView.as_view(),name='delete'),
    path('batch-delete/',DepartmentBatchDeleteView.as_view(),name='batch_delete'),
    path('getDepartments/', DepartmentDetailView.as_view(), name='detail'),
]
