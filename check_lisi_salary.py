#!/usr/bin/env python
import os
import sys
import django

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hrms.settings')
django.setup()

from personal.models import Personal
from salary_management.models import EmployeeSalaryConfig, MonthlySalary
from decimal import Decimal

def check_lisi_salary():
    """检查李四的薪资配置和计算详情"""
    try:
        # 获取李四的信息
        emp = Personal.objects.get(name='李四')
        print(f"员工信息: {emp.name} (ID: {emp.id})")
        
        # 获取李四的薪资配置
        config = EmployeeSalaryConfig.objects.filter(employee=emp, is_active=True).first()
        if config:
            print(f"\n=== 薪资配置 ===")
            print(f"基本薪资: {config.basic_salary}")
            print(f"绩效薪资: {config.performance_salary}")
            print(f"津贴补助: {config.allowance}")
            print(f"薪资等级: {config.salary_grade.grade_name if config.salary_grade else '无'}")
            print(f"生效日期: {config.effective_date}")
            
            # 计算预期应发薪资
            expected_gross = config.basic_salary + config.performance_salary + config.allowance
            print(f"预期应发薪资: {expected_gross} (基本+绩效+津贴)")
        else:
            print("未找到李四的薪资配置")
            return
        
        # 获取李四最新的薪资记录
        salary = MonthlySalary.objects.filter(employee=emp).order_by('-created_at').first()
        if salary:
            print(f"\n=== 最新薪资记录 ({salary.salary_month}) ===")
            print(f"应发薪资: {salary.gross_salary}")
            print(f"  - 基本薪资: {salary.basic_salary}")
            print(f"  - 绩效薪资: {salary.performance_salary}")
            print(f"  - 津贴补助: {salary.allowance}")
            print(f"  - 奖金: {salary.bonus}")
            print(f"  - 加班费: {salary.overtime_pay}")
            
            print(f"\n=== 扣除项详情 ===")
            print(f"社会保险: {salary.social_insurance}")
            print(f"住房公积金: {salary.housing_fund}")
            print(f"个人所得税: {salary.income_tax}")
            print(f"其他扣除: {salary.other_deduction}")
            print(f"总扣除: {salary.total_deduction}")
            
            print(f"\n=== 计算验证 ===")
            calculated_gross = salary.basic_salary + salary.performance_salary + salary.allowance + salary.bonus + salary.overtime_pay
            print(f"计算的应发薪资: {calculated_gross}")
            print(f"记录的应发薪资: {salary.gross_salary}")
            print(f"差异: {salary.gross_salary - calculated_gross}")
            
            calculated_deduction = salary.social_insurance + salary.housing_fund + salary.income_tax + salary.other_deduction
            print(f"计算的总扣除: {calculated_deduction}")
            print(f"记录的总扣除: {salary.total_deduction}")
            
            net_salary = salary.gross_salary - salary.total_deduction
            print(f"实发薪资: {net_salary}")
            print(f"记录的实发薪资: {salary.net_salary}")
            
            # 分析差异原因
            if salary.gross_salary != expected_gross:
                print(f"\n=== 应发薪资差异分析 ===")
                print(f"配置总额: {expected_gross}")
                print(f"实际应发: {salary.gross_salary}")
                print(f"差异: {salary.gross_salary - expected_gross}")
                
                if salary.bonus > 0:
                    print(f"包含奖金: {salary.bonus}")
                if salary.overtime_pay > 0:
                    print(f"包含加班费: {salary.overtime_pay}")
        else:
            print("未找到李四的薪资记录")
            
    except Personal.DoesNotExist:
        print("未找到名为'李四'的员工")
    except Exception as e:
        print(f"查询出错: {e}")

if __name__ == '__main__':
    check_lisi_salary()