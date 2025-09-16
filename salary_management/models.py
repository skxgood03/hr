from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal
from personal.models import Personal


class SalaryGrade(models.Model):
    """薪资等级表"""
    grade_name = models.CharField(max_length=50, verbose_name='等级名称')
    min_salary = models.DecimalField(
        max_digits=10, decimal_places=2, 
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name='最低薪资'
    )
    max_salary = models.DecimalField(
        max_digits=10, decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name='最高薪资'
    )
    description = models.TextField(blank=True, verbose_name='描述')
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    
    class Meta:
        db_table = 't_salary_grade'
        verbose_name = '薪资等级'
        verbose_name_plural = '薪资等级'
        ordering = ['min_salary']
    
    def __str__(self):
        return f"{self.grade_name} ({self.min_salary}-{self.max_salary})"


class EmployeeSalaryConfig(models.Model):
    """员工薪资配置表"""
    employee = models.ForeignKey(
        Personal, on_delete=models.CASCADE, 
        verbose_name='员工', related_name='salary_configs'
    )
    salary_grade = models.ForeignKey(
        SalaryGrade, on_delete=models.CASCADE,
        verbose_name='薪资等级'
    )
    basic_salary = models.DecimalField(
        max_digits=10, decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name='基本工资'
    )
    performance_salary = models.DecimalField(
        max_digits=10, decimal_places=2, default=0,
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name='绩效工资'
    )
    allowance = models.DecimalField(
        max_digits=10, decimal_places=2, default=0,
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name='津贴补贴'
    )
    housing_fund_rate = models.DecimalField(
        max_digits=5, decimal_places=4, default=Decimal('0.12'),
        validators=[MinValueValidator(Decimal('0')), MaxValueValidator(Decimal('1'))],
        verbose_name='住房公积金缴费比例'
    )
    effective_date = models.DateField(verbose_name='生效日期')
    end_date = models.DateField(null=True, blank=True, verbose_name='结束日期')
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    
    class Meta:
        db_table = 't_employee_salary_config'
        verbose_name = '员工薪资配置'
        verbose_name_plural = '员工薪资配置'
        ordering = ['-effective_date']
        unique_together = ['employee', 'effective_date']
    
    def __str__(self):
        return f"{self.employee.name} - {self.basic_salary}"


class MonthlySalary(models.Model):
    """月度工资记录表"""
    STATUS_CHOICES = [
        ('DRAFT', '草稿'),
        ('CALCULATED', '已计算'),
        ('APPROVED', '已审批'),
        ('PAID', '已发放'),
    ]
    
    employee = models.ForeignKey(
        Personal, on_delete=models.CASCADE,
        verbose_name='员工', related_name='monthly_salaries'
    )
    salary_month = models.DateField(verbose_name='工资月份')
    basic_salary = models.DecimalField(
        max_digits=10, decimal_places=2,
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name='基本工资'
    )
    performance_salary = models.DecimalField(
        max_digits=10, decimal_places=2, default=0,
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name='绩效工资'
    )
    allowance = models.DecimalField(
        max_digits=10, decimal_places=2, default=0,
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name='津贴补贴'
    )
    bonus = models.DecimalField(
        max_digits=10, decimal_places=2, default=0,
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name='奖金'
    )
    overtime_pay = models.DecimalField(
        max_digits=10, decimal_places=2, default=0,
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name='加班费'
    )
    gross_salary = models.DecimalField(
        max_digits=10, decimal_places=2,
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name='应发工资'
    )
    social_insurance = models.DecimalField(
        max_digits=10, decimal_places=2, default=0,
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name='社会保险'
    )
    housing_fund = models.DecimalField(
        max_digits=10, decimal_places=2, default=0,
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name='住房公积金'
    )
    income_tax = models.DecimalField(
        max_digits=10, decimal_places=2, default=0,
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name='个人所得税'
    )
    other_deduction = models.DecimalField(
        max_digits=10, decimal_places=2, default=0,
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name='其他扣款'
    )
    total_deduction = models.DecimalField(
        max_digits=10, decimal_places=2,
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name='扣款合计'
    )
    net_salary = models.DecimalField(
        max_digits=10, decimal_places=2,
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name='实发工资'
    )
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, 
        default='DRAFT', verbose_name='状态'
    )
    pay_date = models.DateField(null=True, blank=True, verbose_name='发放日期')
    bank_account = models.CharField(
        max_length=50, blank=True, verbose_name='银行账号'
    )
    remarks = models.TextField(blank=True, verbose_name='备注')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        db_table = 't_monthly_salary'
        verbose_name = '月度工资记录'
        verbose_name_plural = '月度工资记录'
        ordering = ['-salary_month', 'employee__name']
        unique_together = ['employee', 'salary_month']
    
    def __str__(self):
        return f"{self.employee.name} - {self.salary_month.strftime('%Y-%m')}"
    
    def save(self, *args, **kwargs):
        # 自动计算应发工资和实发工资
        self.gross_salary = (
            self.basic_salary + self.performance_salary + 
            self.allowance + self.bonus + self.overtime_pay
        )
        self.total_deduction = (
            self.social_insurance + self.housing_fund + 
            self.income_tax + self.other_deduction
        )
        self.net_salary = self.gross_salary - self.total_deduction
        super().save(*args, **kwargs)


class AttendanceCalculationRule(models.Model):
    """考勤计算规则配置表"""
    rule_name = models.CharField(max_length=100, verbose_name='规则名称')
    description = models.TextField(blank=True, verbose_name='规则描述')
    
    # 正常工作时间配置
    standard_work_hours_per_day = models.DecimalField(
        max_digits=4, decimal_places=2, default=8,
        verbose_name='标准工作时长(小时/天)'
    )
    standard_work_days_per_month = models.IntegerField(
        default=22, verbose_name='标准工作天数(天/月)'
    )
    
    # 请假扣款规则
    personal_leave_deduction_rate = models.DecimalField(
        max_digits=5, decimal_places=4, default=1.0,
        verbose_name='事假扣款比例(1.0=全扣)'
    )
    sick_leave_deduction_rate = models.DecimalField(
        max_digits=5, decimal_places=4, default=0.5,
        verbose_name='病假扣款比例'
    )
    annual_leave_deduction_rate = models.DecimalField(
        max_digits=5, decimal_places=4, default=0.0,
        verbose_name='年假扣款比例'
    )
    
    # 加班工资倍率
    weekday_overtime_rate = models.DecimalField(
        max_digits=4, decimal_places=2, default=1.5,
        verbose_name='工作日加班倍率'
    )
    weekend_overtime_rate = models.DecimalField(
        max_digits=4, decimal_places=2, default=2.0,
        verbose_name='周末加班倍率'
    )
    holiday_overtime_rate = models.DecimalField(
        max_digits=4, decimal_places=2, default=3.0,
        verbose_name='节假日加班倍率'
    )
    
    # 迟到早退扣款
    late_deduction_per_minute = models.DecimalField(
        max_digits=6, decimal_places=2, default=5.0,
        verbose_name='迟到扣款(元/分钟)'
    )
    early_leave_deduction_per_minute = models.DecimalField(
        max_digits=6, decimal_places=2, default=5.0,
        verbose_name='早退扣款(元/分钟)'
    )
    
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        db_table = 't_attendance_calculation_rule'
        verbose_name = '考勤计算规则'
        verbose_name_plural = '考勤计算规则'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.rule_name


class AttendanceSalaryDetail(models.Model):
    """考勤薪资明细表"""
    monthly_salary = models.OneToOneField(
        MonthlySalary, on_delete=models.CASCADE,
        verbose_name='月度工资记录', related_name='attendance_detail'
    )
    calculation_rule = models.ForeignKey(
        AttendanceCalculationRule, on_delete=models.CASCADE,
        verbose_name='计算规则'
    )
    
    # 出勤统计
    actual_work_days = models.IntegerField(default=0, verbose_name='实际工作天数')
    actual_work_hours = models.DecimalField(
        max_digits=6, decimal_places=2, default=0,
        verbose_name='实际工作时长'
    )
    
    # 请假统计
    personal_leave_hours = models.DecimalField(
        max_digits=6, decimal_places=2, default=0,
        verbose_name='事假时长(小时)'
    )
    sick_leave_hours = models.DecimalField(
        max_digits=6, decimal_places=2, default=0,
        verbose_name='病假时长(小时)'
    )
    annual_leave_hours = models.DecimalField(
        max_digits=6, decimal_places=2, default=0,
        verbose_name='年假时长(小时)'
    )
    other_leave_hours = models.DecimalField(
        max_digits=6, decimal_places=2, default=0,
        verbose_name='其他假期时长(小时)'
    )
    
    # 加班统计
    weekday_overtime_hours = models.DecimalField(
        max_digits=6, decimal_places=2, default=0,
        verbose_name='工作日加班时长(小时)'
    )
    weekend_overtime_hours = models.DecimalField(
        max_digits=6, decimal_places=2, default=0,
        verbose_name='周末加班时长(小时)'
    )
    holiday_overtime_hours = models.DecimalField(
        max_digits=6, decimal_places=2, default=0,
        verbose_name='节假日加班时长(小时)'
    )
    
    # 异常统计
    late_minutes = models.IntegerField(default=0, verbose_name='迟到分钟数')
    early_leave_minutes = models.IntegerField(default=0, verbose_name='早退分钟数')
    missing_clock_days = models.IntegerField(default=0, verbose_name='缺卡天数')
    
    # 计算结果
    normal_work_pay = models.DecimalField(
        max_digits=10, decimal_places=2, default=0,
        verbose_name='正常出勤工资'
    )
    leave_deduction = models.DecimalField(
        max_digits=10, decimal_places=2, default=0,
        verbose_name='请假扣款'
    )
    overtime_pay = models.DecimalField(
        max_digits=10, decimal_places=2, default=0,
        verbose_name='加班工资'
    )
    late_early_deduction = models.DecimalField(
        max_digits=10, decimal_places=2, default=0,
        verbose_name='迟到早退扣款'
    )
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        db_table = 't_attendance_salary_detail'
        verbose_name = '考勤薪资明细'
        verbose_name_plural = '考勤薪资明细'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.monthly_salary.employee.name} - {self.monthly_salary.salary_month.strftime('%Y-%m')}"


class SalaryAdjustment(models.Model):
    """工资调整记录表"""
    ADJUSTMENT_TYPES = [
        ('PROMOTION', '晋升调薪'),
        ('ANNUAL', '年度调薪'),
        ('PERFORMANCE', '绩效调薪'),
        ('MARKET', '市场调薪'),
        ('OTHER', '其他调薪'),
    ]
    
    employee = models.ForeignKey(
        Personal, on_delete=models.CASCADE,
        verbose_name='员工', related_name='salary_adjustments'
    )
    adjustment_type = models.CharField(
        max_length=20, choices=ADJUSTMENT_TYPES,
        verbose_name='调薪类型'
    )
    old_salary = models.DecimalField(
        max_digits=10, decimal_places=2,
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name='调整前工资'
    )
    new_salary = models.DecimalField(
        max_digits=10, decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name='调整后工资'
    )
    adjustment_amount = models.DecimalField(
        max_digits=10, decimal_places=2,
        verbose_name='调整金额'
    )
    effective_date = models.DateField(verbose_name='生效日期')
    reason = models.TextField(blank=True, verbose_name='调薪原因')
    approver_id = models.IntegerField(null=True, blank=True, verbose_name='审批人ID')
    approval_date = models.DateTimeField(null=True, blank=True, verbose_name='审批时间')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    
    class Meta:
        db_table = 't_salary_adjustment'
        verbose_name = '工资调整记录'
        verbose_name_plural = '工资调整记录'
        ordering = ['-effective_date']
    
    def __str__(self):
        return f"{self.employee.name} - {self.get_adjustment_type_display()}"
    
    def save(self, *args, **kwargs):
        # 自动计算调整金额
        self.adjustment_amount = self.new_salary - self.old_salary
        super().save(*args, **kwargs)