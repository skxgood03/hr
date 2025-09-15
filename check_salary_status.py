#!/usr/bin/env python
import os
import sys
import django

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hrms.settings')
django.setup()

from salary_management.models import MonthlySalary
from django.db.models import Count

print('=== 工资记录状态统计 ===')
print(f'总记录数: {MonthlySalary.objects.count()}')
print(f'草稿状态记录数: {MonthlySalary.objects.filter(status="DRAFT").count()}')

print('\n各状态统计:')
stats = MonthlySalary.objects.values('status').annotate(count=Count('id'))
for stat in stats:
    print(f'  {stat["status"]}: {stat["count"]}')

print('\n草稿状态记录详情:')
draft_records = MonthlySalary.objects.filter(status='DRAFT')[:5]
for record in draft_records:
    print(f'  ID: {record.id}, 员工: {record.employee.name}, 月份: {record.salary_month}')

if draft_records.count() == 0:
    print('  没有草稿状态的记录')