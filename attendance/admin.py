from django.contrib import admin
from .models import ClockInRecord, LeaveRecord, OvertimeRecord


@admin.register(ClockInRecord)
class ClockInRecordAdmin(admin.ModelAdmin):
    """打卡记录管理"""
    list_display = ['employee', 'clock_type', 'clock_time', 'location', 'device', 'status', 'created_at']
    list_filter = ['clock_type', 'status', 'created_at', 'clock_time']
    search_fields = ['employee__name', 'employee__employee_id', 'location', 'device']
    date_hierarchy = 'clock_time'
    ordering = ['-clock_time']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('基本信息', {
            'fields': ('employee', 'clock_type', 'clock_time', 'status')
        }),
        ('详细信息', {
            'fields': ('location', 'device')
        }),
        ('时间信息', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(LeaveRecord)
class LeaveRecordAdmin(admin.ModelAdmin):
    """请假记录管理"""
    list_display = ['employee', 'leave_type', 'start_time', 'end_time', 'duration_hours', 'status', 'approver', 'created_at']
    list_filter = ['leave_type', 'status', 'created_at', 'start_time']
    search_fields = ['employee__name', 'employee__employee_id', 'reason', 'approver__name']
    date_hierarchy = 'start_time'
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('基本信息', {
            'fields': ('employee', 'leave_type', 'start_time', 'end_time', 'duration_hours')
        }),
        ('请假详情', {
            'fields': ('reason',)
        }),
        ('审批信息', {
            'fields': ('status', 'approver', 'approved_at')
        }),
        ('时间信息', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(OvertimeRecord)
class OvertimeRecordAdmin(admin.ModelAdmin):
    """加班记录管理"""
    list_display = ['employee', 'overtime_type', 'start_time', 'end_time', 'duration_hours', 'status', 'approver', 'created_at']
    list_filter = ['overtime_type', 'status', 'created_at', 'start_time']
    search_fields = ['employee__name', 'employee__employee_id', 'reason', 'approver__name']
    date_hierarchy = 'start_time'
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('基本信息', {
            'fields': ('employee', 'overtime_type', 'start_time', 'end_time', 'duration_hours')
        }),
        ('加班详情', {
            'fields': ('reason',)
        }),
        ('审批信息', {
            'fields': ('status', 'approver', 'approved_at')
        }),
        ('时间信息', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
