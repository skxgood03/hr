from django.urls import path

from personal.views import PersonalAddView, PersnoalListsView, PersonalGetByIdView, PersonalUpdateView, \
    PersonalDeleteView, PersonalNameByDepartmentView, personal_list, PersonalWebAddView, \
    PersonalWebDetailView, PersonalWebUpdateView, PersonalWebDeleteView, export_personal_excel

urlpatterns = [
    # 前端页面路由
    path('', personal_list, name='personal_list'),
    path('export/excel/', export_personal_excel, name='export_excel'),
    
    # Web前端适配的API路由
    path('add/', PersonalWebAddView.as_view(), name='web_add'),
    path('detail/<int:personal_id>/', PersonalWebDetailView.as_view(), name='web_detail'),
    path('update/', PersonalWebUpdateView.as_view(), name='web_update'),
    path('delete/', PersonalWebDeleteView.as_view(), name='web_delete'),
    
    # 原有API路由（保持兼容性）
    path('api/add/',PersonalAddView.as_view(),name='add'),
    path('getList/',PersnoalListsView.as_view(),name='getList'),
    path('getById/',PersonalGetByIdView.as_view(),name='getById'),
    path('api/update/',PersonalUpdateView.as_view(),name='update'),
    path('api/delete/',PersonalDeleteView.as_view(),name='delete'),
    path('getPersonalsName/', PersonalNameByDepartmentView.as_view(),name='getPersonalsName'),
]