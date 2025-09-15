from django.urls import path

from recruit.views import RecruitAddView, RecruitListView, RecruitDetailByIdView, RecruitUpdateByIdView, \
    RecruitDeleteByIdView

urlpatterns = [
    path('add/',RecruitAddView.as_view(), name='add'),
    path('getList/',RecruitListView.as_view(), name='getList'),
    path('getById/',RecruitDetailByIdView.as_view(), name='getById'),
    path('update/',RecruitUpdateByIdView.as_view(), name='update'),
    path('delete/',RecruitDeleteByIdView.as_view(), name='delete'),
]