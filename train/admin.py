from django.contrib import admin
from .models import Train

# Register your models here.

@admin.register(Train)
class TrainAdmin(admin.ModelAdmin):
    list_display = ('personal', 'beginDate', 'endDate', 'trainContent', 'trainCost')
    list_filter = ('beginDate', 'endDate', 'personal')
    search_fields = ('trainContent', 'personal__name')
    ordering = ('-beginDate',)
    date_hierarchy = 'beginDate'
    
    fieldsets = (
        ('培训信息', {
            'fields': ('personal', 'trainContent', 'trainCost')
        }),
        ('时间安排', {
            'fields': ('beginDate', 'endDate')
        }),
    )
