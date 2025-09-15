from django.db import models
from personal.models import Personal


class ClockInRecord(models.Model):
    """打卡记录模型"""
    CLOCK_TYPE_CHOICES = [
        ('IN', '上班'),
        ('OUT', '下班'),
    ]
    
    STATUS_CHOICES = [
        ('NORMAL', '正常'),
        ('LATE', '迟到'),
        ('EARLY', '早退'),
        ('MISSING', '缺卡'),
    ]
    
    employee = models.ForeignKey(Personal, on_delete=models.CASCADE, verbose_name='员工')
    clock_type = models.CharField(max_length=10, choices=CLOCK_TYPE_CHOICES, verbose_name='打卡类型')
    clock_time = models.DateTimeField(verbose_name='打卡时间戳')
    location = models.CharField(max_length=255, blank=True, null=True, verbose_name='打卡地点')
    device = models.CharField(max_length=100, verbose_name='打卡设备')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='NORMAL', verbose_name='打卡状态')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        db_table = 't_clock_in_record'
        verbose_name = '打卡记录'
        verbose_name_plural = '打卡记录管理'
        ordering = ['-clock_time']
    
    def __str__(self):
        return f"{self.employee.name} - {self.get_clock_type_display()} - {self.clock_time}"


class LeaveRecord(models.Model):
    """请假记录模型"""
    LEAVE_TYPE_CHOICES = [
        ('PERSONAL', '事假'),
        ('SICK', '病假'),
        ('ANNUAL', '年假'),
        ('MATERNITY', '产假'),
        ('PATERNITY', '陪产假'),
        ('MARRIAGE', '婚假'),
        ('FUNERAL', '丧假'),
        ('OTHER', '其他'),
    ]
    
    STATUS_CHOICES = [
        ('PENDING', '待审批'),
        ('APPROVED', '已批准'),
        ('REJECTED', '已拒绝'),
        ('CANCELLED', '已取消'),
    ]
    
    employee = models.ForeignKey(Personal, on_delete=models.CASCADE, verbose_name='员工')
    leave_type = models.CharField(max_length=20, choices=LEAVE_TYPE_CHOICES, verbose_name='请假类型')
    start_time = models.DateTimeField(verbose_name='请假开始时间')
    end_time = models.DateTimeField(verbose_name='请假结束时间')
    duration_hours = models.DecimalField(max_digits=6, decimal_places=2, verbose_name='请假时长(小时)')
    reason = models.TextField(verbose_name='请假原因')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING', verbose_name='审批状态')
    approver = models.ForeignKey(Personal, on_delete=models.SET_NULL, null=True, blank=True, 
                                related_name='approved_leaves', verbose_name='审批人')
    approved_at = models.DateTimeField(null=True, blank=True, verbose_name='审批时间')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        db_table = 't_leave_record'
        verbose_name = '请假记录'
        verbose_name_plural = '请假记录管理'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.employee.name} - {self.get_leave_type_display()} - {self.start_time.date()}"


class OvertimeRecord(models.Model):
    """加班记录模型"""
    OVERTIME_TYPE_CHOICES = [
        ('WEEKDAY', '工作日'),
        ('WEEKEND', '周末'),
        ('HOLIDAY', '节假日'),
    ]
    
    STATUS_CHOICES = [
        ('PENDING', '待审批'),
        ('APPROVED', '已批准'),
        ('REJECTED', '已拒绝'),
        ('CANCELLED', '已取消'),
    ]
    
    employee = models.ForeignKey(Personal, on_delete=models.CASCADE, verbose_name='员工')
    start_time = models.DateTimeField(verbose_name='加班开始时间')
    end_time = models.DateTimeField(verbose_name='加班结束时间')
    duration_hours = models.DecimalField(max_digits=6, decimal_places=2, verbose_name='加班时长(小时)')
    reason = models.TextField(verbose_name='加班原因')
    overtime_type = models.CharField(max_length=20, choices=OVERTIME_TYPE_CHOICES, verbose_name='加班类型')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING', verbose_name='审批状态')
    approver = models.ForeignKey(Personal, on_delete=models.SET_NULL, null=True, blank=True,
                                related_name='approved_overtimes', verbose_name='审批人')
    approved_at = models.DateTimeField(null=True, blank=True, verbose_name='审批时间')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        db_table = 't_overtime_record'
        verbose_name = '加班记录'
        verbose_name_plural = '加班记录管理'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.employee.name} - {self.get_overtime_type_display()} - {self.start_time.date()}"
