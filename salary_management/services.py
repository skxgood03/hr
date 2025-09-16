from decimal import Decimal
from datetime import datetime, date, timedelta
from django.db.models import Sum, Avg, Count, Q
from django.db import transaction
from django.utils import timezone
from calendar import monthrange

from .models import SalaryGrade, EmployeeSalaryConfig, MonthlySalary, SalaryAdjustment
from .models import AttendanceCalculationRule, AttendanceSalaryDetail
from personal.models import Personal
from department.models import Department
from attendance.models import ClockInRecord, LeaveRecord, OvertimeRecord


class AttendanceSalaryCalculationService:
    """考勤薪资计算服务类"""
    
    def __init__(self, calculation_rule_id=None):
        """初始化计算服务
        
        Args:
            calculation_rule_id: 计算规则ID，如果为None则使用默认规则
        """
        if calculation_rule_id:
            self.calculation_rule = AttendanceCalculationRule.objects.get(
                id=calculation_rule_id, is_active=True
            )
        else:
            self.calculation_rule = AttendanceCalculationRule.objects.filter(
                is_active=True
            ).first()
            
        if not self.calculation_rule:
            raise ValueError("未找到有效的考勤计算规则")
    
    def calculate_monthly_attendance_salary(self, employee_id, salary_month):
        """计算员工月度考勤薪资
        
        Args:
            employee_id: 员工ID
            salary_month: 工资月份 (datetime.date)
            
        Returns:
            dict: 计算结果
        """
        employee = Personal.objects.get(id=employee_id)
        
        # 获取员工薪资配置
        salary_config = self._get_employee_salary_config(employee, salary_month)
        if not salary_config:
            raise ValueError(f"员工 {employee.name} 在 {salary_month} 没有有效的薪资配置")
        
        # 计算月份的天数和工作日
        month_info = self._get_month_info(salary_month)
        
        # 统计考勤数据
        attendance_stats = self._calculate_attendance_stats(
            employee, salary_month, month_info
        )
        
        # 计算各项薪资
        salary_calculations = self._calculate_salary_components(
            salary_config, attendance_stats
        )
        
        # 合并结果
        result = {
            'employee': employee,
            'salary_month': salary_month,
            'salary_config': salary_config,
            'calculation_rule': self.calculation_rule,
            'month_info': month_info,
            **attendance_stats,
            **salary_calculations
        }
        
        return result
    
    def _get_employee_salary_config(self, employee, salary_month):
        """获取员工在指定月份的薪资配置"""
        return EmployeeSalaryConfig.objects.filter(
            employee=employee,
            effective_date__lte=salary_month,
            is_active=True
        ).filter(
            Q(end_date__isnull=True) | Q(end_date__gte=salary_month)
        ).order_by('-effective_date').first()
    
    def _get_month_info(self, salary_month):
        """获取月份信息"""
        year = salary_month.year
        month = salary_month.month
        
        # 计算月份天数
        _, days_in_month = monthrange(year, month)
        
        # 计算工作日（简化处理，实际应考虑节假日）
        work_days = 0
        for day in range(1, days_in_month + 1):
            date = datetime(year, month, day).date()
            # 周一到周五为工作日
            if date.weekday() < 5:
                work_days += 1
        
        return {
            'year': year,
            'month': month,
            'days_in_month': days_in_month,
            'work_days': work_days,
            'standard_work_hours': work_days * self.calculation_rule.standard_work_hours_per_day
        }
    
    def _calculate_attendance_stats(self, employee, salary_month, month_info):
        """统计考勤数据"""
        year = month_info['year']
        month = month_info['month']
        
        # 月份开始和结束日期
        month_start = datetime(year, month, 1).date()
        month_end = datetime(year, month, month_info['days_in_month']).date()
        
        # 统计打卡记录
        clock_stats = self._calculate_clock_stats(employee, month_start, month_end)
        
        # 统计请假记录
        leave_stats = self._calculate_leave_stats(employee, month_start, month_end)
        
        # 统计加班记录
        overtime_stats = self._calculate_overtime_stats(employee, month_start, month_end)
        
        return {
            **clock_stats,
            **leave_stats,
            **overtime_stats
        }
    
    def _calculate_clock_stats(self, employee, month_start, month_end):
        """统计打卡数据"""
        clock_records = ClockInRecord.objects.filter(
            employee=employee,
            clock_time__date__range=[month_start, month_end]
        )
        
        # 统计各种状态的打卡次数
        normal_count = clock_records.filter(status='NORMAL').count()
        late_count = clock_records.filter(status='LATE').count()
        early_count = clock_records.filter(status='EARLY').count()
        missing_count = clock_records.filter(status='MISSING').count()
        
        # 计算实际工作天数（简化处理）
        actual_work_days = clock_records.filter(
            clock_type='IN'
        ).values('clock_time__date').distinct().count()
        
        # 计算迟到和早退分钟数（简化处理）
        late_minutes = late_count * 30  # 假设平均迟到30分钟
        early_leave_minutes = early_count * 30  # 假设平均早退30分钟
        
        return {
            'actual_work_days': actual_work_days,
            'actual_work_hours': actual_work_days * self.calculation_rule.standard_work_hours_per_day,
            'late_minutes': late_minutes,
            'early_leave_minutes': early_leave_minutes,
            'missing_clock_days': missing_count // 2  # 假设缺卡是成对的（上班+下班）
        }
    
    def _calculate_leave_stats(self, employee, month_start, month_end):
        """统计请假数据"""
        leave_records = LeaveRecord.objects.filter(
            employee=employee,
            status='APPROVED',
            start_time__date__lte=month_end,
            end_time__date__gte=month_start
        )
        
        personal_leave_hours = Decimal('0')
        sick_leave_hours = Decimal('0')
        annual_leave_hours = Decimal('0')
        other_leave_hours = Decimal('0')
        
        for leave in leave_records:
            # 计算在当月的请假时长
            leave_start = max(leave.start_time.date(), month_start)
            leave_end = min(leave.end_time.date(), month_end)
            
            if leave_start <= leave_end:
                # 简化处理：按天计算，每天8小时
                days = (leave_end - leave_start).days + 1
                hours = Decimal(str(days * 8))
                
                if leave.leave_type == 'PERSONAL':
                    personal_leave_hours += hours
                elif leave.leave_type == 'SICK':
                    sick_leave_hours += hours
                elif leave.leave_type == 'ANNUAL':
                    annual_leave_hours += hours
                else:
                    other_leave_hours += hours
        
        return {
            'personal_leave_hours': personal_leave_hours,
            'sick_leave_hours': sick_leave_hours,
            'annual_leave_hours': annual_leave_hours,
            'other_leave_hours': other_leave_hours
        }
    
    def _calculate_overtime_stats(self, employee, month_start, month_end):
        """统计加班数据"""
        overtime_records = OvertimeRecord.objects.filter(
            employee=employee,
            status='APPROVED',
            start_time__date__range=[month_start, month_end]
        )
        
        weekday_overtime_hours = Decimal('0')
        weekend_overtime_hours = Decimal('0')
        holiday_overtime_hours = Decimal('0')
        
        for overtime in overtime_records:
            if overtime.overtime_type == 'WEEKDAY':
                weekday_overtime_hours += overtime.duration_hours
            elif overtime.overtime_type == 'WEEKEND':
                weekend_overtime_hours += overtime.duration_hours
            elif overtime.overtime_type == 'HOLIDAY':
                holiday_overtime_hours += overtime.duration_hours
        
        return {
            'weekday_overtime_hours': weekday_overtime_hours,
            'weekend_overtime_hours': weekend_overtime_hours,
            'holiday_overtime_hours': holiday_overtime_hours
        }
    
    def _calculate_salary_components(self, salary_config, attendance_stats):
        """计算薪资组成部分"""
        # 计算小时工资
        hourly_rate = salary_config.basic_salary / Decimal(str(
            self.calculation_rule.standard_work_days_per_month * 
            self.calculation_rule.standard_work_hours_per_day
        ))
        
        # 1. 正常出勤工资
        normal_work_pay = self._calculate_normal_work_pay(
            salary_config, attendance_stats, hourly_rate
        )
        
        # 2. 请假扣款
        leave_deduction = self._calculate_leave_deduction(
            attendance_stats, hourly_rate
        )
        
        # 3. 加班工资
        overtime_pay = self._calculate_overtime_pay(
            attendance_stats, hourly_rate
        )
        
        # 4. 迟到早退扣款
        late_early_deduction = self._calculate_late_early_deduction(
            attendance_stats
        )
        
        return {
            'hourly_rate': hourly_rate,
            'normal_work_pay': normal_work_pay,
            'leave_deduction': leave_deduction,
            'overtime_pay': overtime_pay,
            'late_early_deduction': late_early_deduction
        }
    
    def _calculate_normal_work_pay(self, salary_config, attendance_stats, hourly_rate):
        """计算正常出勤工资"""
        # 基于实际工作时长计算
        actual_hours = attendance_stats['actual_work_hours']
        return hourly_rate * actual_hours
    
    def _calculate_leave_deduction(self, attendance_stats, hourly_rate):
        """计算请假扣款"""
        total_deduction = Decimal('0')
        
        # 事假扣款
        personal_deduction = (
            attendance_stats['personal_leave_hours'] * hourly_rate * 
            self.calculation_rule.personal_leave_deduction_rate
        )
        
        # 病假扣款
        sick_deduction = (
            attendance_stats['sick_leave_hours'] * hourly_rate * 
            self.calculation_rule.sick_leave_deduction_rate
        )
        
        # 年假扣款
        annual_deduction = (
            attendance_stats['annual_leave_hours'] * hourly_rate * 
            self.calculation_rule.annual_leave_deduction_rate
        )
        
        # 其他假期按事假处理
        other_deduction = (
            attendance_stats['other_leave_hours'] * hourly_rate * 
            self.calculation_rule.personal_leave_deduction_rate
        )
        
        total_deduction = personal_deduction + sick_deduction + annual_deduction + other_deduction
        return total_deduction
    
    def _calculate_overtime_pay(self, attendance_stats, hourly_rate):
        """计算加班工资"""
        total_overtime_pay = Decimal('0')
        
        # 工作日加班
        weekday_pay = (
            attendance_stats['weekday_overtime_hours'] * hourly_rate * 
            self.calculation_rule.weekday_overtime_rate
        )
        
        # 周末加班
        weekend_pay = (
            attendance_stats['weekend_overtime_hours'] * hourly_rate * 
            self.calculation_rule.weekend_overtime_rate
        )
        
        # 节假日加班
        holiday_pay = (
            attendance_stats['holiday_overtime_hours'] * hourly_rate * 
            self.calculation_rule.holiday_overtime_rate
        )
        
        total_overtime_pay = weekday_pay + weekend_pay + holiday_pay
        return total_overtime_pay
    
    def _calculate_late_early_deduction(self, attendance_stats):
        """计算迟到早退扣款"""
        late_deduction = (
            Decimal(str(attendance_stats['late_minutes'])) * 
            self.calculation_rule.late_deduction_per_minute
        )
        
        early_deduction = (
            Decimal(str(attendance_stats['early_leave_minutes'])) * 
            self.calculation_rule.early_leave_deduction_per_minute
        )
        
        return late_deduction + early_deduction
    
    def save_attendance_salary_detail(self, monthly_salary, calculation_result):
        """保存考勤薪资明细"""
        detail, created = AttendanceSalaryDetail.objects.get_or_create(
            monthly_salary=monthly_salary,
            defaults={
                'calculation_rule': self.calculation_rule,
                'actual_work_days': calculation_result['actual_work_days'],
                'actual_work_hours': calculation_result['actual_work_hours'],
                'personal_leave_hours': calculation_result['personal_leave_hours'],
                'sick_leave_hours': calculation_result['sick_leave_hours'],
                'annual_leave_hours': calculation_result['annual_leave_hours'],
                'other_leave_hours': calculation_result['other_leave_hours'],
                'weekday_overtime_hours': calculation_result['weekday_overtime_hours'],
                'weekend_overtime_hours': calculation_result['weekend_overtime_hours'],
                'holiday_overtime_hours': calculation_result['holiday_overtime_hours'],
                'late_minutes': calculation_result['late_minutes'],
                'early_leave_minutes': calculation_result['early_leave_minutes'],
                'missing_clock_days': calculation_result['missing_clock_days'],
                'normal_work_pay': calculation_result['normal_work_pay'],
                'leave_deduction': calculation_result['leave_deduction'],
                'overtime_pay': calculation_result['overtime_pay'],
                'late_early_deduction': calculation_result['late_early_deduction'],
            }
        )
        
        if not created:
            # 更新现有记录
            for field, value in {
                'calculation_rule': self.calculation_rule,
                'actual_work_days': calculation_result['actual_work_days'],
                'actual_work_hours': calculation_result['actual_work_hours'],
                'personal_leave_hours': calculation_result['personal_leave_hours'],
                'sick_leave_hours': calculation_result['sick_leave_hours'],
                'annual_leave_hours': calculation_result['annual_leave_hours'],
                'other_leave_hours': calculation_result['other_leave_hours'],
                'weekday_overtime_hours': calculation_result['weekday_overtime_hours'],
                'weekend_overtime_hours': calculation_result['weekend_overtime_hours'],
                'holiday_overtime_hours': calculation_result['holiday_overtime_hours'],
                'late_minutes': calculation_result['late_minutes'],
                'early_leave_minutes': calculation_result['early_leave_minutes'],
                'missing_clock_days': calculation_result['missing_clock_days'],
                'normal_work_pay': calculation_result['normal_work_pay'],
                'leave_deduction': calculation_result['leave_deduction'],
                'overtime_pay': calculation_result['overtime_pay'],
                'late_early_deduction': calculation_result['late_early_deduction'],
            }.items():
                setattr(detail, field, value)
            detail.save()
        
        return detail
    
    @classmethod
    def batch_calculate_attendance_salary(cls, salary_month, employee_ids=None):
        """批量计算考勤薪资
        
        Args:
            salary_month: 工资月份 (datetime.date)
            employee_ids: 员工ID列表，如果为None则计算所有在职员工
            
        Returns:
            tuple: (成功结果列表, 错误信息列表)
        """
        results = []
        errors = []
        
        # 获取要计算的员工列表
        if employee_ids:
            employees = Personal.objects.filter(id__in=employee_ids, workStatus=1)
        else:
            employees = Personal.objects.filter(workStatus=1)
        
        service = cls()
        
        for employee in employees:
            try:
                result = service.calculate_monthly_attendance_salary(
                    employee.id, salary_month
                )
                
                # 创建或更新月度工资记录
                monthly_salary, created = MonthlySalary.objects.get_or_create(
                    employee=employee,
                    salary_month=salary_month,
                    defaults={
                        'basic_salary': result['salary_config'].basic_salary,
                        'performance_salary': result['salary_config'].performance_salary,
                        'allowance': Decimal('0'),
                        'overtime_pay': result['overtime_pay'],
                        'deduction': result['leave_deduction'] + result['late_early_deduction'],
                        'bonus': Decimal('0'),
                        'social_insurance': Decimal('0'),
                        'housing_fund': Decimal('0'),
                        'tax': Decimal('0'),
                        'status': 'DRAFT'
                    }
                )
                
                if not created:
                    # 更新现有记录的考勤相关字段
                    monthly_salary.overtime_pay = result['overtime_pay']
                    monthly_salary.deduction = result['leave_deduction'] + result['late_early_deduction']
                    monthly_salary.save()
                
                # 保存考勤薪资明细
                detail = service.save_attendance_salary_detail(monthly_salary, result)
                
                results.append({
                    'employee': employee,
                    'monthly_salary': monthly_salary,
                    'detail': detail,
                    'calculation_result': result
                })
                
            except Exception as e:
                errors.append(f'{employee.name}：{str(e)}')
        
        return results, errors
    
    @classmethod
    def calculate_employee_attendance_salary(cls, employee_id, salary_month, save=True):
        """计算单个员工的考勤薪资
        
        Args:
            employee_id: 员工ID
            salary_month: 工资月份
            save: 是否保存到数据库
            
        Returns:
            dict: 计算结果
        """
        service = cls()
        result = service.calculate_monthly_attendance_salary(employee_id, salary_month)
        
        if save:
            employee = Personal.objects.get(id=employee_id)
            
            # 创建或更新月度工资记录
            monthly_salary, created = MonthlySalary.objects.get_or_create(
                employee=employee,
                salary_month=salary_month,
                defaults={
                    'basic_salary': result['salary_config'].basic_salary,
                    'performance_salary': result['salary_config'].performance_salary,
                    'allowance': Decimal('0'),
                    'overtime_pay': result['overtime_pay'],
                    'deduction': result['leave_deduction'] + result['late_early_deduction'],
                    'bonus': Decimal('0'),
                    'social_insurance': Decimal('0'),
                    'housing_fund': Decimal('0'),
                    'tax': Decimal('0'),
                    'status': 'DRAFT'
                }
            )
            
            if not created:
                monthly_salary.overtime_pay = result['overtime_pay']
                monthly_salary.deduction = result['leave_deduction'] + result['late_early_deduction']
                monthly_salary.save()
            
            # 保存考勤薪资明细
            detail = service.save_attendance_salary_detail(monthly_salary, result)
            result['monthly_salary'] = monthly_salary
            result['detail'] = detail
        
        # 添加汇总字段
        result['attendance_salary'] = result['normal_work_pay']
        result['overtime_salary'] = result['overtime_pay']
        result['deduction_amount'] = result['leave_deduction'] + result['late_early_deduction']
        result['final_salary'] = (
            result['attendance_salary'] + result['overtime_salary'] - result['deduction_amount']
        )
        
        return result


class SalaryCalculationService:
    """工资计算服务"""
    
    # 个人所得税税率表（2023年标准）
    TAX_BRACKETS = [
        (0, 3000, Decimal('0.03'), 0),
        (3000, 12000, Decimal('0.10'), 210),
        (12000, 25000, Decimal('0.20'), 1410),
        (25000, 35000, Decimal('0.25'), 2660),
        (35000, 55000, Decimal('0.30'), 4410),
        (55000, 80000, Decimal('0.35'), 7160),
        (80000, float('inf'), Decimal('0.45'), 15160),
    ]
    
    # 社保费率（示例，实际应根据当地政策调整）
    SOCIAL_INSURANCE_RATES = {
        'pension': Decimal('0.08'),      # 养老保险个人缴费比例
        'medical': Decimal('0.02'),      # 医疗保险个人缴费比例
        'unemployment': Decimal('0.005'), # 失业保险个人缴费比例
    }
    
    # 住房公积金费率
    HOUSING_FUND_RATE = Decimal('0.12')
    
    @classmethod
    def calculate_monthly_salary(cls, employee_id, salary_month, include_attendance=True):
        """计算月度工资（整合考勤数据）"""
        try:
            employee = Personal.objects.get(id=employee_id)
            
            # 获取员工当前薪资配置
            salary_config = cls._get_current_salary_config(employee_id, salary_month)
            if not salary_config:
                raise ValueError(f"员工 {employee.name} 在 {salary_month} 没有有效的薪资配置")
            
            # 检查是否已存在该月工资记录
            monthly_salary, created = MonthlySalary.objects.get_or_create(
                employee=employee,
                salary_month=salary_month,
                defaults={
                    'basic_salary': salary_config.basic_salary,
                    'performance_salary': salary_config.performance_salary,
                    'allowance': salary_config.allowance,
                    'bonus': Decimal('0'),
                    'overtime_pay': Decimal('0'),
                    'other_deduction': Decimal('0'),
                }
            )
            
            if not created:
                # 更新基础薪资信息
                monthly_salary.basic_salary = salary_config.basic_salary
                monthly_salary.performance_salary = salary_config.performance_salary
                monthly_salary.allowance = salary_config.allowance
            
            # 如果启用考勤计算，则基于考勤数据调整薪资
            if include_attendance:
                attendance_result = cls._calculate_attendance_based_salary(
                    employee, salary_month, salary_config
                )
                
                # 更新基于考勤的薪资组成
                monthly_salary.basic_salary = attendance_result['adjusted_basic_salary']
                monthly_salary.overtime_pay = attendance_result['overtime_pay']
                monthly_salary.deduction = attendance_result['total_deduction']
            
            # 计算应发工资
            gross_salary = (
                monthly_salary.basic_salary + 
                monthly_salary.performance_salary + 
                monthly_salary.allowance + 
                monthly_salary.bonus + 
                monthly_salary.overtime_pay
            )
            
            # 计算社会保险
            social_insurance = cls.calculate_social_insurance(monthly_salary.basic_salary)
            
            # 计算住房公积金
            housing_fund = cls.calculate_housing_fund(monthly_salary.basic_salary, salary_config.housing_fund_rate)
            
            # 计算个人所得税
            taxable_income = gross_salary - social_insurance - housing_fund - Decimal('5000')  # 5000为起征点
            income_tax = cls.calculate_income_tax(taxable_income)
            
            # 更新工资记录
            monthly_salary.gross_salary = gross_salary
            monthly_salary.social_insurance = social_insurance
            monthly_salary.housing_fund = housing_fund
            monthly_salary.income_tax = income_tax
            monthly_salary.total_deduction = (
                social_insurance + housing_fund + income_tax + monthly_salary.other_deduction
            )
            monthly_salary.net_salary = gross_salary - monthly_salary.total_deduction
            monthly_salary.status = 'CALCULATED'
            monthly_salary.save()
            
            return monthly_salary
            
        except Personal.DoesNotExist:
            raise ValueError(f"员工ID {employee_id} 不存在")
        except Exception as e:
            raise ValueError(f"计算工资时发生错误: {str(e)}")
    
    @classmethod
    def _get_current_salary_config(cls, employee_id, salary_month):
        """获取员工当前有效的薪资配置"""
        return EmployeeSalaryConfig.objects.filter(
            employee_id=employee_id,
            effective_date__lte=salary_month,
            is_active=True
        ).filter(
            Q(end_date__isnull=True) | Q(end_date__gte=salary_month)
        ).order_by('-effective_date').first()
    
    @classmethod
    def calculate_income_tax(cls, taxable_income):
        """计算个人所得税"""
        if taxable_income <= 0:
            return Decimal('0')
        
        for min_income, max_income, rate, deduction in cls.TAX_BRACKETS:
            if min_income < taxable_income <= max_income:
                tax = taxable_income * rate - deduction
                return max(Decimal('0'), tax)
        
        return Decimal('0')
    
    @classmethod
    def calculate_social_insurance(cls, basic_salary):
        """计算社会保险个人缴费部分"""
        total_rate = sum(cls.SOCIAL_INSURANCE_RATES.values())
        return basic_salary * total_rate
    
    @classmethod
    def calculate_housing_fund(cls, basic_salary, housing_fund_rate=None):
        """计算住房公积金个人缴费部分"""
        if housing_fund_rate is None:
            housing_fund_rate = cls.HOUSING_FUND_RATE
        return basic_salary * housing_fund_rate
    
    @classmethod
    def _calculate_attendance_based_salary(cls, employee, salary_month, salary_config):
        """基于考勤数据计算薪资调整"""
        from calendar import monthrange
        
        # 获取考勤计算规则
        calculation_rule = AttendanceCalculationRule.objects.filter(
            is_active=True
        ).first()
        
        if not calculation_rule:
            # 如果没有考勤规则，返回原始薪资
            return {
                'adjusted_basic_salary': salary_config.basic_salary,
                'overtime_pay': Decimal('0'),
                'total_deduction': Decimal('0')
            }
        
        # 计算月份信息
        year = salary_month.year
        month = salary_month.month
        _, days_in_month = monthrange(year, month)
        
        # 计算标准工作日
        work_days = 0
        for day in range(1, days_in_month + 1):
            date_obj = datetime(year, month, day).date()
            if date_obj.weekday() < 5:  # 周一到周五
                work_days += 1
        
        standard_work_hours = work_days * calculation_rule.standard_work_hours_per_day
        
        # 月份开始和结束日期
        month_start = datetime(year, month, 1).date()
        month_end = datetime(year, month, days_in_month).date()
        
        # 统计考勤数据
        attendance_stats = cls._get_attendance_stats(employee, month_start, month_end)
        
        # 计算小时工资
        hourly_rate = salary_config.basic_salary / Decimal(str(standard_work_hours))
        
        # 计算调整后的基本工资（基于实际出勤）
        actual_work_hours = attendance_stats['actual_work_hours']
        adjusted_basic_salary = hourly_rate * actual_work_hours
        
        # 计算加班工资
        overtime_pay = cls._calculate_overtime_pay(
            attendance_stats, hourly_rate, calculation_rule
        )
        
        # 计算扣款（请假、迟到早退）
        leave_deduction = cls._calculate_leave_deduction(
            attendance_stats, hourly_rate, calculation_rule
        )
        late_early_deduction = cls._calculate_late_early_deduction(
            attendance_stats, calculation_rule
        )
        
        total_deduction = leave_deduction + late_early_deduction
        
        return {
            'adjusted_basic_salary': adjusted_basic_salary,
            'overtime_pay': overtime_pay,
            'total_deduction': total_deduction,
            'attendance_stats': attendance_stats
        }
    
    @classmethod
    def _get_attendance_stats(cls, employee, month_start, month_end):
        """获取考勤统计数据"""
        # 统计打卡记录
        clock_records = ClockInRecord.objects.filter(
            employee=employee,
            clock_time__date__range=[month_start, month_end]
        )
        
        # 计算实际工作天数
        actual_work_days = clock_records.filter(
            clock_type='IN'
        ).values('clock_time__date').distinct().count()
        
        # 统计迟到早退
        late_count = clock_records.filter(status='LATE').count()
        early_count = clock_records.filter(status='EARLY').count()
        
        # 统计请假记录
        leave_records = LeaveRecord.objects.filter(
            employee=employee,
            status='APPROVED',
            start_time__date__lte=month_end,
            end_time__date__gte=month_start
        )
        
        personal_leave_hours = Decimal('0')
        sick_leave_hours = Decimal('0')
        annual_leave_hours = Decimal('0')
        
        for leave in leave_records:
            leave_start = max(leave.start_time.date(), month_start)
            leave_end = min(leave.end_time.date(), month_end)
            
            if leave_start <= leave_end:
                days = (leave_end - leave_start).days + 1
                hours = Decimal(str(days * 8))  # 假设每天8小时
                
                if leave.leave_type == 'PERSONAL':
                    personal_leave_hours += hours
                elif leave.leave_type == 'SICK':
                    sick_leave_hours += hours
                elif leave.leave_type == 'ANNUAL':
                    annual_leave_hours += hours
        
        # 统计加班记录
        overtime_records = OvertimeRecord.objects.filter(
            employee=employee,
            status='APPROVED',
            start_time__date__range=[month_start, month_end]
        )
        
        weekday_overtime_hours = Decimal('0')
        weekend_overtime_hours = Decimal('0')
        holiday_overtime_hours = Decimal('0')
        
        for overtime in overtime_records:
            if overtime.overtime_type == 'WEEKDAY':
                weekday_overtime_hours += overtime.duration_hours
            elif overtime.overtime_type == 'WEEKEND':
                weekend_overtime_hours += overtime.duration_hours
            elif overtime.overtime_type == 'HOLIDAY':
                holiday_overtime_hours += overtime.duration_hours
        
        return {
            'actual_work_days': actual_work_days,
            'actual_work_hours': actual_work_days * 8,  # 假设每天8小时
            'late_minutes': late_count * 30,  # 假设平均迟到30分钟
            'early_leave_minutes': early_count * 30,  # 假设平均早退30分钟
            'personal_leave_hours': personal_leave_hours,
            'sick_leave_hours': sick_leave_hours,
            'annual_leave_hours': annual_leave_hours,
            'weekday_overtime_hours': weekday_overtime_hours,
            'weekend_overtime_hours': weekend_overtime_hours,
            'holiday_overtime_hours': holiday_overtime_hours
        }
    
    @classmethod
    def _calculate_overtime_pay(cls, attendance_stats, hourly_rate, calculation_rule):
        """计算加班工资"""
        overtime_pay = Decimal('0')
        
        # 工作日加班
        overtime_pay += (
            attendance_stats['weekday_overtime_hours'] * hourly_rate * 
            calculation_rule.weekday_overtime_rate
        )
        
        # 周末加班
        overtime_pay += (
            attendance_stats['weekend_overtime_hours'] * hourly_rate * 
            calculation_rule.weekend_overtime_rate
        )
        
        # 节假日加班
        overtime_pay += (
            attendance_stats['holiday_overtime_hours'] * hourly_rate * 
            calculation_rule.holiday_overtime_rate
        )
        
        return overtime_pay
    
    @classmethod
    def _calculate_leave_deduction(cls, attendance_stats, hourly_rate, calculation_rule):
        """计算请假扣款"""
        total_deduction = Decimal('0')
        
        # 事假扣款
        total_deduction += (
            attendance_stats['personal_leave_hours'] * hourly_rate * 
            calculation_rule.personal_leave_deduction_rate
        )
        
        # 病假扣款
        total_deduction += (
            attendance_stats['sick_leave_hours'] * hourly_rate * 
            calculation_rule.sick_leave_deduction_rate
        )
        
        # 年假扣款
        total_deduction += (
            attendance_stats['annual_leave_hours'] * hourly_rate * 
            calculation_rule.annual_leave_deduction_rate
        )
        
        return total_deduction
    
    @classmethod
    def _calculate_late_early_deduction(cls, attendance_stats, calculation_rule):
        """计算迟到早退扣款"""
        late_deduction = Decimal(str(attendance_stats['late_minutes'])) * calculation_rule.late_deduction_per_minute
        early_leave_deduction = Decimal(str(attendance_stats['early_leave_minutes'])) * calculation_rule.early_leave_deduction_per_minute
        return late_deduction + early_leave_deduction
    
    @classmethod
    def batch_calculate_monthly_salary(cls, salary_month, employee_ids=None):
        """批量计算月度工资"""
        if employee_ids is None:
            # 获取所有有薪资配置的员工
            employee_ids = EmployeeSalaryConfig.objects.filter(
                effective_date__lte=salary_month,
                is_active=True
            ).filter(
                Q(end_date__isnull=True) | Q(end_date__gte=salary_month)
            ).values_list('employee_id', flat=True).distinct()
        
        results = []
        errors = []
        
        for employee_id in employee_ids:
            try:
                monthly_salary = cls.calculate_monthly_salary(employee_id, salary_month)
                results.append(monthly_salary)
            except Exception as e:
                errors.append(f"员工ID {employee_id}: {str(e)}")
        
        return results, errors


class SalaryReportService:
    """工资报表服务"""
    
    @classmethod
    def generate_department_report(cls, department_id, salary_month):
        """生成部门工资报表"""
        try:
            department = Department.objects.get(id=department_id)
            
            # 获取部门员工的工资记录
            salary_records = MonthlySalary.objects.filter(
                employee__station__department=department,
                salary_month=salary_month
            ).select_related('employee', 'employee__station')
            
            # 统计数据
            stats = salary_records.aggregate(
                total_employees=Count('id'),
                total_gross_salary=Sum('gross_salary'),
                total_net_salary=Sum('net_salary'),
                avg_gross_salary=Avg('gross_salary'),
                avg_net_salary=Avg('net_salary'),
                total_deduction=Sum('total_deduction')
            )
            
            return {
                'department': department,
                'salary_month': salary_month,
                'salary_records': salary_records,
                'statistics': stats
            }
            
        except Department.DoesNotExist:
            raise ValueError(f"部门ID {department_id} 不存在")
    
    @classmethod
    def generate_salary_slip(cls, employee_id, salary_month):
        """生成工资条"""
        try:
            employee = Personal.objects.get(id=employee_id)
            monthly_salary = MonthlySalary.objects.get(
                employee=employee,
                salary_month=salary_month
            )
            
            return {
                'employee': employee,
                'monthly_salary': monthly_salary,
                'salary_month': salary_month,
                'department': employee.station.department if employee.station else None,
                'station': employee.station
            }
            
        except Personal.DoesNotExist:
            raise ValueError(f"员工ID {employee_id} 不存在")
        except MonthlySalary.DoesNotExist:
            raise ValueError(f"员工 {employee.name} 在 {salary_month} 没有工资记录")
    
    @classmethod
    def generate_company_summary(cls, salary_month):
        """生成公司工资汇总报表"""
        # 按部门统计
        department_stats = []
        departments = Department.objects.all()
        
        for dept in departments:
            dept_records = MonthlySalary.objects.filter(
                employee__station__department=dept,
                salary_month=salary_month
            )
            
            if dept_records.exists():
                stats = dept_records.aggregate(
                    employee_count=Count('id'),
                    total_gross=Sum('gross_salary'),
                    total_net=Sum('net_salary'),
                    avg_gross=Avg('gross_salary')
                )
                stats['department'] = dept
                department_stats.append(stats)
        
        # 公司总计
        company_stats = MonthlySalary.objects.filter(
            salary_month=salary_month
        ).aggregate(
            total_employees=Count('id'),
            total_gross_salary=Sum('gross_salary'),
            total_net_salary=Sum('net_salary'),
            total_deduction=Sum('total_deduction'),
            avg_gross_salary=Avg('gross_salary'),
            avg_net_salary=Avg('net_salary')
        )
        
        return {
            'salary_month': salary_month,
            'department_statistics': department_stats,
            'company_statistics': company_stats
        }
    
    @classmethod
    def generate_salary_trend_report(cls, employee_id, start_month, end_month):
        """生成员工工资趋势报表"""
        try:
            employee = Personal.objects.get(id=employee_id)
            
            salary_records = MonthlySalary.objects.filter(
                employee=employee,
                salary_month__gte=start_month,
                salary_month__lte=end_month
            ).order_by('salary_month')
            
            # 计算趋势数据
            trend_data = []
            for record in salary_records:
                trend_data.append({
                    'month': record.salary_month,
                    'gross_salary': record.gross_salary,
                    'net_salary': record.net_salary,
                    'deduction': record.total_deduction
                })
            
            return {
                'employee': employee,
                'start_month': start_month,
                'end_month': end_month,
                'trend_data': trend_data
            }
            
        except Personal.DoesNotExist:
            raise ValueError(f"员工ID {employee_id} 不存在")


class SalaryAdjustmentService:
    """工资调整服务"""
    
    @classmethod
    @transaction.atomic
    def create_salary_adjustment(cls, employee_id, adjustment_type, new_salary, 
                               effective_date, reason='', approver_id=None):
        """创建工资调整记录"""
        try:
            employee = Personal.objects.get(id=employee_id)
            
            # 获取当前薪资配置
            current_config = EmployeeSalaryConfig.objects.filter(
                employee=employee,
                is_active=True
            ).order_by('-effective_date').first()
            
            if not current_config:
                raise ValueError(f"员工 {employee.name} 没有当前薪资配置")
            
            old_salary = current_config.basic_salary
            
            # 创建调整记录
            adjustment = SalaryAdjustment.objects.create(
                employee=employee,
                adjustment_type=adjustment_type,
                old_salary=old_salary,
                new_salary=new_salary,
                effective_date=effective_date,
                reason=reason,
                approver_id=approver_id,
                approval_date=datetime.now() if approver_id else None
            )
            
            # 结束当前薪资配置
            current_config.end_date = effective_date
            current_config.save()
            
            # 创建新的薪资配置
            new_config = EmployeeSalaryConfig.objects.create(
                employee=employee,
                salary_grade=current_config.salary_grade,
                basic_salary=new_salary,
                performance_salary=current_config.performance_salary,
                allowance=current_config.allowance,
                effective_date=effective_date
            )
            
            return adjustment, new_config
            
        except Personal.DoesNotExist:
            raise ValueError(f"员工ID {employee_id} 不存在")