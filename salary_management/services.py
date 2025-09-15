from decimal import Decimal
from datetime import datetime, date
from django.db.models import Sum, Avg, Count, Q
from django.db import transaction
from .models import SalaryGrade, EmployeeSalaryConfig, MonthlySalary, SalaryAdjustment
from personal.models import Personal
from department.models import Department


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
    def calculate_monthly_salary(cls, employee_id, salary_month):
        """计算月度工资"""
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
                }
            )
            
            if not created:
                # 更新基础薪资信息
                monthly_salary.basic_salary = salary_config.basic_salary
                monthly_salary.performance_salary = salary_config.performance_salary
                monthly_salary.allowance = salary_config.allowance
            
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