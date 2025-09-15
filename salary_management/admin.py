from django.contrib import admin
from .models import SalaryGrade, EmployeeSalaryConfig, MonthlySalary, SalaryAdjustment


@admin.register(SalaryGrade)
class SalaryGradeAdmin(admin.ModelAdmin):
    list_display = ('grade_name', 'min_salary', 'max_salary', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('grade_name', 'description')
    ordering = ('min_salary',)
    
    fieldsets = (
        ('基本信息', {
            'fields': ('grade_name', 'description')
        }),
        ('薪资范围', {
            'fields': ('min_salary', 'max_salary')
        }),
        ('状态', {
            'fields': ('is_active',)
        }),
    )


@admin.register(EmployeeSalaryConfig)
class EmployeeSalaryConfigAdmin(admin.ModelAdmin):
    list_display = ('employee', 'salary_grade', 'basic_salary', 'is_active', 'effective_date')
    list_filter = ('is_active', 'salary_grade', 'effective_date')
    search_fields = ('employee__name', 'employee__employeeId')
    ordering = ('-effective_date',)
    
    fieldsets = (
        ('员工信息', {
            'fields': ('employee', 'salary_grade')
        }),
        ('薪资配置', {
            'fields': ('basic_salary', 'performance_salary', 'allowance')
        }),
        ('生效信息', {
            'fields': ('effective_date', 'is_active')
        }),

    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('employee', 'salary_grade')


@admin.register(MonthlySalary)
class MonthlySalaryAdmin(admin.ModelAdmin):
    list_display = ('employee', 'salary_month', 'gross_salary', 'net_salary', 'status', 'created_at')
    list_filter = ('status', 'salary_month', 'created_at')
    search_fields = ('employee__name', 'employee__employeeId')
    ordering = ('-salary_month', 'employee__name')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('基本信息', {
            'fields': ('employee', 'salary_month')
        }),
        ('薪资明细', {
            'fields': ('basic_salary', 'performance_salary', 'allowance', 'bonus', 'overtime_pay')
        }),
        ('扣除项目', {
            'fields': ('social_insurance', 'housing_fund', 'income_tax', 'other_deduction')
        }),
        ('汇总', {
            'fields': ('gross_salary', 'total_deduction', 'net_salary')
        }),
        ('状态信息', {
            'fields': ('status', 'pay_date')
        }),
        ('时间戳', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('employee')
    
    def has_delete_permission(self, request, obj=None):
        # 已发放的工资不允许删除
        if obj and obj.status == 'PAID':
            return False
        return super().has_delete_permission(request, obj)


@admin.register(SalaryAdjustment)
class SalaryAdjustmentAdmin(admin.ModelAdmin):
    list_display = ('employee', 'adjustment_type', 'old_salary', 'new_salary', 'effective_date', 'created_at')
    list_filter = ('adjustment_type', 'effective_date', 'created_at')
    search_fields = ('employee__name', 'employee__employeeId', 'reason')
    ordering = ('-effective_date',)
    readonly_fields = ('created_at',)
    
    fieldsets = (
        ('员工信息', {
            'fields': ('employee',)
        }),
        ('调整信息', {
            'fields': ('adjustment_type', 'old_salary', 'new_salary', 'effective_date')
        }),
        ('审批信息', {
            'fields': ('reason', 'approver_id', 'approval_date')
        }),
        ('时间戳', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('employee', 'approver')
    
    def save_model(self, request, obj, form, change):
        if not change:  # 新建时
            if not obj.approver:
                obj.approver = request.user
        super().save_model(request, obj, form, change)