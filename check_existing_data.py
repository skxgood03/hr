#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import django

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hrms.settings')
django.setup()

from personal.models import Personal
from hr.models import User

def main():
    print("=== 现有数据统计 ===")
    
    # 查看员工数据
    employees = Personal.objects.all()
    print(f"员工总数: {employees.count()}")
    print("\n员工列表:")
    for emp in employees[:10]:
        print(f"ID: {emp.id}, 姓名: {emp.name}, 状态: {emp.get_workStatus_display()}")
    
    # 查看用户数据
    users = User.objects.all()
    print(f"\n用户总数: {users.count()}")
    print("\n用户列表:")
    for user in users[:10]:
        employee_name = user.employee.name if user.employee else "无关联员工"
        print(f"用户名: {user.username}, 角色: {user.role}, 关联员工: {employee_name}")
    
    # 统计在职员工
    active_employees = Personal.objects.filter(workStatus=1)  # 1表示在职
    print(f"\n在职员工数量: {active_employees.count()}")
    
if __name__ == '__main__':
    main()