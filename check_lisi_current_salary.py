#!/usr/bin/env python
import os
import sys
import django
from datetime import date

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hrms.settings')
django.setup()

from personal.models import Personal
from salary_management.models import EmployeeSalaryConfig, MonthlySalary
from salary_management.services import SalaryCalculationService
from decimal import Decimal

def check_lisi_current_salary():
    """检查李四当前月份的薪资计算"""
    try:
        # 获取李四的信息
        emp = Personal.objects.get(name='李四')
        current_month = date.today().replace(day=1)
        print(f"员工: {emp.name} (ID: {emp.id})")
        print(f"当前月份: {current_month}")
        
        # 检查李四的所有薪资配置
        configs = EmployeeSalaryConfig.objects.filter(employee=emp).order_by('-effective_date')
        print(f"\n=== 所有薪资配置 ===")
        for i, config in enumerate(configs):
            print(f"{i+1}. 生效日期: {config.effective_date}, 基本薪资: {config.basic_salary}, 绩效: {config.performance_salary}, 津贴: {config.allowance}, 活跃: {config.is_active}")
        
        # 获取当前有效的薪资配置
        current_config = SalaryCalculationService._get_current_salary_config(emp.id, current_month)
        if current_config:
            print(f"\n=== 当前有效配置 ===")
            print(f"生效日期: {current_config.effective_date}")
            print(f"基本薪资: {current_config.basic_salary}")
            print(f"绩效薪资: {current_config.performance_salary}")
            print(f"津贴补助: {current_config.allowance}")
            print(f"活跃状态: {current_config.is_active}")
        else:
            print("\n未找到当前有效的薪资配置")
        
        # 检查当前月份的薪资记录
        current_salary = MonthlySalary.objects.filter(
            employee=emp, 
            salary_month=current_month
        ).first()
        
        if current_salary:
            print(f"\n=== 当前月份薪资记录 ({current_month}) ===")
            print(f"应发薪资: {current_salary.gross_salary}")
            print(f"基本薪资: {current_salary.basic_salary}")
            print(f"绩效薪资: {current_salary.performance_salary}")
            print(f"津贴补助: {current_salary.allowance}")
            print(f"奖金: {current_salary.bonus}")
            print(f"加班费: {current_salary.overtime_pay}")
            print(f"状态: {current_salary.status}")
        else:
            print(f"\n未找到当前月份 ({current_month}) 的薪资记录")
            
            # 尝试计算当前月份薪资
            print("\n=== 尝试计算当前月份薪资 ===")
            try:
                result = SalaryCalculationService.calculate_monthly_salary(emp.id, current_month)
                if result['success']:
                    salary_data = result['data']
                    print(f"计算成功:")
                    print(f"应发薪资: {salary_data['gross_salary']}")
                    print(f"基本薪资: {salary_data['basic_salary']}")
                    print(f"绩效薪资: {salary_data['performance_salary']}")
                    print(f"津贴补助: {salary_data['allowance']}")
                    print(f"社会保险: {salary_data['social_insurance']}")
                    print(f"住房公积金: {salary_data['housing_fund']}")
                    print(f"个人所得税: {salary_data['income_tax']}")
                    print(f"实发薪资: {salary_data['net_salary']}")
                else:
                    print(f"计算失败: {result['error']}")
            except Exception as e:
                print(f"计算异常: {e}")
        
        # 检查所有薪资记录
        all_salaries = MonthlySalary.objects.filter(employee=emp).order_by('-salary_month')
        print(f"\n=== 所有薪资记录 ===")
        for salary in all_salaries:
            print(f"{salary.salary_month}: 应发={salary.gross_salary}, 基本={salary.basic_salary}, 状态={salary.status}")
            
    except Personal.DoesNotExist:
        print("未找到名为'李四'的员工")
    except Exception as e:
        print(f"查询出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    check_lisi_current_salary()