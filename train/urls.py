from django.urls import path

from train.views import TrainAddView, TrainListView, TrainDetailByIdView, TrainUpdateByIdView, TrainDeleteByIdView

urlpatterns = [
    path('add/', TrainAddView.as_view(),name='add'),
    path('getList/', TrainListView.as_view(),name='getList'),
    path('getById/',TrainDetailByIdView.as_view(),name='getById'),
    path('update/',TrainUpdateByIdView.as_view(),name='updateById'),
    path('delete/',TrainDeleteByIdView.as_view(),name='deleteById'),
]