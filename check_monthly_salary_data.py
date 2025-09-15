#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import django
from datetime import date, datetime

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hrms.settings')
django.setup()

from salary_management.models import MonthlySalary, EmployeeSalaryConfig
from personal.models import Personal

def main():
    print("=== 月度薪资记录数据检查 ===")
    print()
    
    # 1. 检查总记录数
    total_records = MonthlySalary.objects.count()
    print(f"薪资记录总数: {total_records}")
    
    if total_records == 0:
        print("数据库中没有薪资记录")
        return
    
    # 2. 按月份统计
    print("\n=== 按月份统计 ===")
    monthly_stats = MonthlySalary.objects.values('salary_month').distinct().order_by('-salary_month')
    for stat in monthly_stats:
        month = stat['salary_month']
        count = MonthlySalary.objects.filter(salary_month=month).count()
        print(f"{month.strftime('%Y年%m月')}: {count} 条记录")
    
    # 3. 按状态统计
    print("\n=== 按状态统计 ===")
    status_stats = {}
    for status_code, status_name in MonthlySalary.STATUS_CHOICES:
        count = MonthlySalary.objects.filter(status=status_code).count()
        if count > 0:
            status_stats[status_name] = count
            print(f"{status_name}: {count} 条记录")
    
    # 4. 显示最近的几条记录
    print("\n=== 最近的薪资记录 ===")
    recent_records = MonthlySalary.objects.select_related(
        'employee', 'employee__station', 'employee__station__department'
    ).order_by('-created_at')[:5]
    
    for record in recent_records:
        print(f"员工: {record.employee.name} (ID: {record.employee.id})")
        print(f"部门: {record.employee.station.department.departmentName}")
        print(f"月份: {record.salary_month.strftime('%Y年%m月')}")
        print(f"应发: ¥{record.gross_salary}, 实发: ¥{record.net_salary}")
        print(f"状态: {record.get_status_display()}")
        print(f"创建时间: {record.created_at}")
        print("-" * 50)
    
    # 5. 检查当前月份的记录
    current_month = date.today().replace(day=1)
    current_month_records = MonthlySalary.objects.filter(salary_month=current_month)
    print(f"\n=== 当前月份 ({current_month.strftime('%Y年%m月')}) 记录 ===")
    print(f"记录数: {current_month_records.count()}")
    
    if current_month_records.exists():
        for record in current_month_records[:3]:  # 只显示前3条
            print(f"- {record.employee.name}: 应发¥{record.gross_salary}, 实发¥{record.net_salary}")
    
    # 6. 检查员工薪资配置
    print("\n=== 员工薪资配置统计 ===")
    total_employees = Personal.objects.count()
    active_configs = EmployeeSalaryConfig.objects.filter(is_active=True).count()
    print(f"员工总数: {total_employees}")
    print(f"有效薪资配置: {active_configs}")
    
    # 7. 检查是否有测试数据
    print("\n=== 数据来源分析 ===")
    if MonthlySalary.objects.filter(employee__name__contains='测试').exists():
        print("发现测试数据")
    
    # 检查是否有初始化脚本创建的数据
    if MonthlySalary.objects.filter(created_at__date=date.today()).exists():
        today_records = MonthlySalary.objects.filter(created_at__date=date.today()).count()
        print(f"今天创建的记录: {today_records} 条")

if __name__ == '__main__':
    main()