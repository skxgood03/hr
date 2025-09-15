from django.urls import path

from station.views import StationAddView, StationListView, GetStationByIdView, GetStatioinByDepartmentIdView, \
    UpdateStationView, DeleteStationView, station_list

urlpatterns = [
    # 前端页面路由
    path('', station_list, name='station_list'),
    
    # API路由
    path('add/', StationAddView.as_view(),name='add'),
    path('getList/', StationListView.as_view(),name='getList'),
    path('getStations/',GetStatioinByDepartmentIdView.as_view(),name='getStations'),
    path('getById/',GetStationByIdView.as_view(),name='getById'),
    path('update/',UpdateStationView.as_view(),name='updateById'),
    path('delete/',DeleteStationView.as_view(),name='deleteById'),
]