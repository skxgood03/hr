#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
批量为员工创建用户账号脚本

功能：
1. 为所有没有关联用户的员工创建用户账号
2. 用户名规则：员工姓名的拼音首字母 + 员工ID后4位
3. 默认密码：123456
4. 默认角色：员工
"""

import os
import sys
import django
import re

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hrms.settings')
django.setup()

from personal.models import Personal
from hr.models import User, Role

def generate_username(name, employee_id):
    """生成用户名：姓名简化 + 员工ID后4位"""
    # 简单的中文姓名处理：取姓名前2个字符的ASCII码转换
    name_part = ''
    for char in name[:2]:  # 取前两个字符
        if '\u4e00' <= char <= '\u9fff':  # 中文字符
            # 使用字符的unicode编码后4位作为标识
            name_part += str(ord(char))[-2:]
        else:
            name_part += char.lower()
    
    # 如果name_part为空或太短，使用默认前缀
    if len(name_part) < 2:
        name_part = 'emp'
    
    # 员工ID后4位
    id_suffix = str(employee_id).zfill(4)[-4:]
    
    username = name_part[:4] + id_suffix
    
    # 确保用户名不超过10个字符（根据模型限制）
    if len(username) > 10:
        username = username[:6] + id_suffix[-4:]
    
    return username

def ensure_unique_username(base_username):
    """确保用户名唯一，如果重复则添加数字后缀"""
    username = base_username
    counter = 1
    
    while User.objects.filter(username=username).exists():
        # 如果用户名已存在，添加数字后缀
        suffix = str(counter)
        max_base_len = 10 - len(suffix)
        username = base_username[:max_base_len] + suffix
        counter += 1
        
        if counter > 99:  # 防止无限循环
            break
    
    return username

def create_employee_users():
    """批量创建员工用户"""
    print("开始批量创建员工用户账号...")
    
    # 获取默认员工角色
    try:
        employee_role = Role.objects.get(name='EMPLOYEE')
    except Role.DoesNotExist:
        print("错误：未找到员工角色，请先创建EMPLOYEE角色")
        return
    
    # 获取所有员工
    employees = Personal.objects.all()
    
    if not employees.exists():
        print("没有找到员工数据")
        return
    
    # 获取已经有用户账号的员工ID列表
    existing_user_employee_ids = set(
        User.objects.filter(employee_id__isnull=False)
        .values_list('employee_id', flat=True)
    )
    
    created_count = 0
    skipped_count = 0
    error_count = 0
    
    for employee in employees:
        try:
            # 检查该员工是否已经有用户账号
            if employee.id in existing_user_employee_ids:
                print(f"跳过员工 {employee.name}（ID: {employee.id}）- 已有用户账号")
                skipped_count += 1
                continue
            
            # 生成用户名
            base_username = generate_username(employee.name, employee.id)
            username = ensure_unique_username(base_username)
            
            # 创建用户
            user = User.objects.create(
                username=username,
                password='123456',  # 默认密码
                role=employee_role,
                employee_id=employee.id
            )
            
            print(f"✓ 为员工 {employee.name}（ID: {employee.id}）创建用户：{username}")
            created_count += 1
            
        except Exception as e:
            print(f"✗ 为员工 {employee.name}（ID: {employee.id}）创建用户失败：{str(e)}")
            error_count += 1
    
    print(f"\n批量创建完成！")
    print(f"成功创建：{created_count} 个用户")
    print(f"跳过：{skipped_count} 个员工（已有账号）")
    print(f"失败：{error_count} 个员工")
    print(f"\n默认密码：123456")
    print(f"建议员工首次登录后修改密码")

def list_created_users():
    """列出已创建的员工用户"""
    print("\n已创建的员工用户列表：")
    print("-" * 60)
    print(f"{'用户名':<12} {'员工姓名':<10} {'员工ID':<8} {'角色':<8}")
    print("-" * 60)
    
    users = User.objects.filter(employee_id__isnull=False).select_related('role')
    
    for user in users:
        employee = user.employee
        employee_name = employee.name if employee else '未知'
        role_name = user.role.get_name_display() if user.role else '无角色'
        
        print(f"{user.username:<12} {employee_name:<10} {user.employee_id:<8} {role_name:<8}")
    
    print("-" * 60)
    print(f"总计：{users.count()} 个用户")

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'list':
        list_created_users()
    else:
        create_employee_users()
        list_created_users()