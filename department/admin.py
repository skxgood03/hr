from django.contrib import admin
from .models import Department

# Register your models here.

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('departmentName', 'description')
    list_filter = ('departmentName',)
    search_fields = ('departmentName', 'description')
    ordering = ('departmentName',)
    
    fieldsets = (
        ('部门信息', {
            'fields': ('departmentName', 'description')
        }),
    )
