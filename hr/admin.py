from django.contrib import admin
from .models import User, Role

# Register your models here.
@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'created_at']
    list_filter = ['name', 'created_at']
    search_fields = ['name', 'description']
    ordering = ['name']
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('基本信息', {
            'fields': ('name', 'description')
        }),
        ('时间信息', {
            'fields': ('created_at',)
        }),
    )

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['username', 'role', 'get_role_display', 'employee_id', 'get_employee_name', 'created_at']
    list_filter = ['role', 'created_at']
    search_fields = ['username', 'employee_id']
    ordering = ['username']
    readonly_fields = ['created_at']
    
    def get_role_display(self, obj):
        return obj.role.get_name_display() if obj.role else '未分配'
    get_role_display.short_description = '角色名称'
    
    def get_employee_name(self, obj):
        employee = obj.employee
        return employee.name if employee else '未关联'
    get_employee_name.short_description = '关联员工'
    
    fieldsets = (
        ('基本信息', {
            'fields': ('username', 'password')
        }),
        ('角色信息', {
            'fields': ('role',)
        }),
        ('员工关联', {
            'fields': ('employee_id',)
        }),
        ('时间信息', {
            'fields': ('created_at',)
        }),
    )
