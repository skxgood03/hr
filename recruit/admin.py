from django.contrib import admin
from .models import Recruit

# Register your models here.

@admin.register(Recruit)
class RecruitAdmin(admin.ModelAdmin):
    list_display = ('station', 'needNum', 'demand', 'needEducation', 'recruitStatus')
    list_filter = ('station', 'recruitStatus', 'needEducation', 'startDate')
    search_fields = ('demand', 'station__stationName')
    ordering = ('-startDate',)
    date_hierarchy = 'startDate'
    
    fieldsets = (
        ('招聘信息', {
            'fields': ('station', 'needNum', 'demand', 'needEducation')
        }),
        ('时间安排', {
            'fields': ('startDate', 'endDate')
        }),
        ('状态', {
            'fields': ('recruitStatus',)
        }),
    )
