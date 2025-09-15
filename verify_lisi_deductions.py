#!/usr/bin/env python
import os
import sys
import django
from datetime import date
from decimal import Decimal

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hrms.settings')
django.setup()

from personal.models import Personal
from salary_management.models import MonthlySalary
from salary_management.services import SalaryCalculationService

def verify_lisi_deductions():
    """验证李四的扣除项计算"""
    try:
        # 获取李四的信息
        emp = Personal.objects.get(name='李四')
        current_month = date.today().replace(day=1)
        
        print(f"员工: {emp.name} (ID: {emp.id})")
        print(f"当前月份: {current_month}")
        
        # 获取李四当前月份的薪资记录
        salary_record = MonthlySalary.objects.filter(
            employee=emp,
            salary_month=current_month
        ).first()
        
        if salary_record:
            print(f"\n=== 薪资构成分析 ===")
            print(f"基本薪资: {salary_record.basic_salary}")
            print(f"绩效薪资: {salary_record.performance_salary}")
            print(f"津贴补助: {salary_record.allowance}")
            print(f"奖金: {salary_record.bonus} (来源: init_salary_data.py 硬编码)")
            print(f"加班费: {salary_record.overtime_pay} (来源: init_salary_data.py 硬编码)")
            print(f"应发薪资: {salary_record.gross_salary}")
            
            # 验证应发薪资计算
            calculated_gross = (
                salary_record.basic_salary + 
                salary_record.performance_salary + 
                salary_record.allowance + 
                salary_record.bonus + 
                salary_record.overtime_pay
            )
            print(f"\n=== 应发薪资验证 ===")
            print(f"计算结果: {calculated_gross}")
            print(f"记录值: {salary_record.gross_salary}")
            print(f"是否一致: {'是' if calculated_gross == salary_record.gross_salary else '否'}")
            
            print(f"\n=== 扣除项分析 ===")
            print(f"社会保险: {salary_record.social_insurance}")
            print(f"住房公积金: {salary_record.housing_fund}")
            print(f"个人所得税: {salary_record.income_tax}")
            print(f"其他扣除: {salary_record.other_deduction}")
            print(f"总扣除: {salary_record.total_deduction}")
            print(f"实发薪资: {salary_record.net_salary}")
            
            # 验证扣除项计算 (根据init_salary_data.py的逻辑)
            print(f"\n=== 扣除项计算验证 (init_salary_data.py逻辑) ===")
            init_social_insurance = salary_record.gross_salary * Decimal('0.105')  # 10.5%
            init_housing_fund = salary_record.gross_salary * Decimal('0.12')  # 12%
            init_income_tax = max(Decimal('0.00'), (salary_record.gross_salary - init_social_insurance - init_housing_fund - Decimal('5000')) * Decimal('0.1'))
            init_total_deduction = init_social_insurance + init_housing_fund + init_income_tax
            init_net_salary = salary_record.gross_salary - init_total_deduction
            
            print(f"社保 (10.5%): 计算={init_social_insurance:.2f}, 记录={salary_record.social_insurance}")
            print(f"公积金 (12%): 计算={init_housing_fund:.2f}, 记录={salary_record.housing_fund}")
            print(f"个税 (简化): 计算={init_income_tax:.2f}, 记录={salary_record.income_tax}")
            print(f"总扣除: 计算={init_total_deduction:.2f}, 记录={salary_record.total_deduction}")
            print(f"实发: 计算={init_net_salary:.2f}, 记录={salary_record.net_salary}")
            
            # 验证扣除项计算 (根据SalaryCalculationService的逻辑)
            print(f"\n=== 扣除项计算验证 (SalaryCalculationService逻辑) ===")
            service_social_insurance = SalaryCalculationService.calculate_social_insurance(salary_record.basic_salary)
            service_housing_fund = SalaryCalculationService.calculate_housing_fund(salary_record.basic_salary)
            taxable_income = salary_record.gross_salary - service_social_insurance - service_housing_fund - Decimal('5000')
            service_income_tax = SalaryCalculationService.calculate_income_tax(taxable_income)
            service_total_deduction = service_social_insurance + service_housing_fund + service_income_tax
            service_net_salary = salary_record.gross_salary - service_total_deduction
            
            print(f"社保 (基于基本薪资): 计算={service_social_insurance:.2f}, 记录={salary_record.social_insurance}")
            print(f"公积金 (基于基本薪资): 计算={service_housing_fund:.2f}, 记录={salary_record.housing_fund}")
            print(f"个税 (累进税率): 计算={service_income_tax:.2f}, 记录={salary_record.income_tax}")
            print(f"总扣除: 计算={service_total_deduction:.2f}, 记录={salary_record.total_deduction}")
            print(f"实发: 计算={service_net_salary:.2f}, 记录={salary_record.net_salary}")
            
            print(f"\n=== 结论 ===")
            print(f"1. 李四的薪资配置: 基本薪资3100 + 绩效100 + 津贴100 = 3300")
            print(f"2. 应发薪资4800的原因: 3300 + 奖金1000 + 加班费500 = 4800")
            print(f"3. 奖金和加班费来源: init_salary_data.py脚本中硬编码设置")
            print(f"4. 扣除项计算: 使用了init_salary_data.py中的简化算法")
            print(f"5. 如需修改奖金和加班费，可以通过薪资管理界面手动调整")
            
        else:
            print("未找到当前月份的薪资记录")
            
    except Personal.DoesNotExist:
        print("未找到名为'李四'的员工")
    except Exception as e:
        print(f"查询出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    verify_lisi_deductions()