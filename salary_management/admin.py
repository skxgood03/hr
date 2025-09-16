from django.contrib import admin
from .models import SalaryGrade, EmployeeSalaryConfig, MonthlySalary, SalaryAdjustment, AttendanceCalculationRule, AttendanceSalaryDetail


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


@admin.register(AttendanceCalculationRule)
class AttendanceCalculationRuleAdmin(admin.ModelAdmin):
    list_display = ('rule_name', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('rule_name', 'description')
    ordering = ('rule_name',)
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('基本信息', {
            'fields': ('rule_name', 'description', 'is_active')
        }),
        ('工作时间设置', {
            'fields': ('standard_work_hours_per_day', 'standard_work_days_per_month')
        }),
        ('加班费率', {
            'fields': ('weekday_overtime_rate', 'weekend_overtime_rate', 'holiday_overtime_rate')
        }),
        ('扣款设置', {
            'fields': ('late_deduction_per_minute', 'early_leave_deduction_per_minute')
        }),
        ('请假设置', {
            'fields': ('personal_leave_deduction_rate', 'sick_leave_deduction_rate')
        }),
        ('时间戳', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(AttendanceSalaryDetail)
class AttendanceSalaryDetailAdmin(admin.ModelAdmin):
    list_display = ('get_employee_name', 'get_salary_month', 'actual_work_days', 'normal_work_pay', 'overtime_pay', 'leave_deduction', 'created_at')
    list_filter = ('created_at', 'monthly_salary__salary_month')
    search_fields = ('monthly_salary__employee__name',)
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at')
    
    def get_employee_name(self, obj):
        return obj.monthly_salary.employee.name
    get_employee_name.short_description = '员工姓名'
    
    def get_salary_month(self, obj):
        return obj.monthly_salary.salary_month.strftime('%Y-%m')
    get_salary_month.short_description = '工资月份'
    
    fieldsets = (
        ('关联信息', {
            'fields': ('monthly_salary', 'calculation_rule')
        }),
        ('出勤统计', {
            'fields': ('actual_work_days', 'actual_work_hours')
        }),
        ('请假统计', {
            'fields': ('personal_leave_hours', 'sick_leave_hours', 'annual_leave_hours', 'other_leave_hours')
        }),
        ('加班统计', {
            'fields': ('weekday_overtime_hours', 'weekend_overtime_hours', 'holiday_overtime_hours')
        }),
        ('异常统计', {
            'fields': ('late_minutes', 'early_leave_minutes', 'missing_clock_days')
        }),
        ('计算结果', {
            'fields': ('normal_work_pay', 'leave_deduction', 'overtime_pay', 'late_early_deduction')
        }),
        ('时间戳', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('monthly_salary__employee', 'calculation_rule')