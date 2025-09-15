#!/usr/bin/env python
import os
import sys
import django
from datetime import date
from decimal import Decimal

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hrms.settings')
django.setup()

from salary_management.models import MonthlySalary
from personal.models import Personal

print('=== 创建草稿状态的工资记录 ===')

# 获取前3个员工（假设workStatus=1表示在职）
employees = Personal.objects.filter(workStatus=1)[:3]

if not employees:
    print('没有找到在职的员工，使用所有员工')
    employees = Personal.objects.all()[:3]
    
if not employees:
    print('没有找到任何员工')
    sys.exit(1)

current_month = date.today().replace(day=1)

for employee in employees:
    # 检查是否已存在当月记录
    existing = MonthlySalary.objects.filter(
        employee=employee,
        salary_month=current_month
    ).first()
    
    if existing:
        # 如果存在，更新为草稿状态
        existing.status = 'DRAFT'
        existing.save()
        print(f'更新 {employee.name} 的工资记录为草稿状态')
    else:
        # 创建新的草稿记录
        salary_record = MonthlySalary.objects.create(
            employee=employee,
            salary_month=current_month,
            basic_salary=Decimal('5000.00'),
            performance_salary=Decimal('1000.00'),
            allowance=Decimal('500.00'),
            overtime_pay=Decimal('0.00'),
            bonus=Decimal('0.00'),
            deduction=Decimal('200.00'),
            net_salary=Decimal('6300.00'),
            status='DRAFT'
        )
        print(f'创建 {employee.name} 的草稿工资记录，ID: {salary_record.id}')

print('\n=== 验证创建结果 ===')
draft_count = MonthlySalary.objects.filter(status='DRAFT').count()
print(f'草稿状态记录数: {draft_count}')

if draft_count > 0:
    print('\n草稿记录详情:')
    for record in MonthlySalary.objects.filter(status='DRAFT'):
        print(f'  ID: {record.id}, 员工: {record.employee.name}, 月份: {record.salary_month}, 净工资: {record.net_salary}')
else:
    print('没有草稿记录被创建')