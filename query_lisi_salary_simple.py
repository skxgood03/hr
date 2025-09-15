#!/usr/bin/env python
"""
简化版本的李四薪资查询脚本
替代用户提到的长shell命令
"""

import os
import sys
import django
from datetime import date

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hrms.settings')
django.setup()

from personal.models import Personal
from salary_management.models import EmployeeSalaryConfig, MonthlySalary

def main():
    try:
        # 获取李四的员工信息
        emp = Personal.objects.get(name='李四')
        current_month = date.today().replace(day=1)
        print(f"员工: {emp.name} (ID: {emp.id})")
        print(f"查询月份: {current_month}")
        
        # 获取李四的薪资配置
        config = EmployeeSalaryConfig.objects.filter(employee=emp, is_active=True).first()
        if config:
            print(f"李四薪资配置: 基本薪资={config.basic_salary}, 绩效={config.performance_salary}, 津贴={config.allowance}")
        else:
            print("未找到李四的薪资配置")
            return
        
        # 获取李四当前月份的薪资记录
        salary = MonthlySalary.objects.filter(employee=emp, salary_month=current_month).first()
        if salary:
            print(f"当前月份薪资记录: 应发={salary.gross_salary}, 基本={salary.basic_salary}, 绩效={salary.performance_salary}, 津贴={salary.allowance}, 奖金={salary.bonus}, 加班费={salary.overtime_pay}")
            print(f"扣除项: 社保={salary.social_insurance}, 公积金={salary.housing_fund}, 个税={salary.income_tax}, 其他={salary.other_deduction}, 总扣除={salary.total_deduction}")
            print(f"实发薪资: {salary.net_salary}")
            print(f"薪资状态: {salary.status}")
        else:
            print(f"未找到{current_month}月份的薪资记录")
            
        # 显示最新的薪资记录（用于对比）
        latest_salary = MonthlySalary.objects.filter(employee=emp).order_by('-created_at').first()
        if latest_salary and latest_salary.salary_month != current_month:
            print(f"\n最新历史记录 ({latest_salary.salary_month}): 应发={latest_salary.gross_salary}, 基本={latest_salary.basic_salary}")
            
    except Personal.DoesNotExist:
        print("未找到名为'李四'的员工")
    except Exception as e:
        print(f"查询出错: {e}")

if __name__ == '__main__':
    main()