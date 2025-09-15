from django.contrib import admin
from .models import Personal

# Register your models here.

@admin.register(Personal)
class PersonalAdmin(admin.ModelAdmin):
    list_display = ('name', 'gender', 'birthday', 'station', 'phone', 'email', 'age', 'workStatus')
    list_filter = ('gender', 'station', 'workStatus', 'education')
    search_fields = ('name', 'phone', 'email', 'identity')
    ordering = ('name',)
    
    fieldsets = (
        ('基本信息', {
            'fields': ('name', 'gender', 'birthday', 'age', 'identity')
        }),
        ('联系方式', {
            'fields': ('phone', 'email')
        }),
        ('教育信息', {
            'fields': ('education', 'school')
        }),
        ('工作信息', {
            'fields': ('station', 'beginDate', 'workStatus')
        }),
    )
