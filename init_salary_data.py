#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
工资管理系统数据初始化脚本
用于创建薪资等级、员工薪资配置等基础数据
"""

import os
import sys
import django
from datetime import date, datetime
from decimal import Decimal

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hrms.settings')
django.setup()

from salary_management.models import SalaryGrade, EmployeeSalaryConfig, MonthlySalary, SalaryAdjustment
from personal.models import Personal
from department.models import Department
from station.models import Station

def init_salary_grades():
    """初始化薪资等级数据"""
    print("正在初始化薪资等级数据...")
    
    salary_grades = [
        {
            'grade_name': '实习生',
            'min_salary': Decimal('3000.00'),
            'max_salary': Decimal('4500.00'),
            'description': '实习期员工薪资等级'
        },
        {
            'grade_name': '初级',
            'min_salary': Decimal('4500.00'),
            'max_salary': Decimal('8000.00'),
            'description': '初级员工薪资等级'
        },
        {
            'grade_name': '中级',
            'min_salary': Decimal('8000.00'),
            'max_salary': Decimal('15000.00'),
            'description': '中级员工薪资等级'
        },
        {
            'grade_name': '高级',
            'min_salary': Decimal('15000.00'),
            'max_salary': Decimal('25000.00'),
            'description': '高级员工薪资等级'
        },
        {
            'grade_name': '专家',
            'min_salary': Decimal('25000.00'),
            'max_salary': Decimal('40000.00'),
            'description': '专家级员工薪资等级'
        },
        {
            'grade_name': '管理层',
            'min_salary': Decimal('20000.00'),
            'max_salary': Decimal('50000.00'),
            'description': '管理层薪资等级'
        }
    ]
    
    for grade_data in salary_grades:
        grade, created = SalaryGrade.objects.get_or_create(
            grade_name=grade_data['grade_name'],
            defaults=grade_data
        )
        if created:
            print(f"  创建薪资等级: {grade.grade_name}")
        else:
            print(f"  薪资等级已存在: {grade.grade_name}")
    
    print(f"薪资等级初始化完成，共 {len(salary_grades)} 个等级\n")

def init_employee_salary_configs():
    """初始化员工薪资配置数据"""
    print("正在初始化员工薪资配置数据...")
    
    # 获取所有员工
    employees = Personal.objects.all()
    if not employees.exists():
        print("  警告: 没有找到员工数据，请先初始化员工数据")
        return
    
    # 获取薪资等级
    grades = {grade.grade_name: grade for grade in SalaryGrade.objects.all()}
    
    # 为每个员工创建薪资配置
    configs_created = 0
    for employee in employees:
        # 根据员工职位分配薪资等级
        if hasattr(employee, 'station') and employee.station:
            station_name = employee.station.stationName.lower()
            if '实习' in station_name:
                grade = grades.get('实习生')
                basic_salary = Decimal('3500.00')
            elif '经理' in station_name or '主管' in station_name:
                grade = grades.get('管理层')
                basic_salary = Decimal('25000.00')
            elif '高级' in station_name or '资深' in station_name:
                grade = grades.get('高级')
                basic_salary = Decimal('18000.00')
            elif '中级' in station_name:
                grade = grades.get('中级')
                basic_salary = Decimal('12000.00')
            else:
                grade = grades.get('初级')
                basic_salary = Decimal('6000.00')
        else:
            grade = grades.get('初级')
            basic_salary = Decimal('6000.00')
        
        # 创建薪资配置
        config, created = EmployeeSalaryConfig.objects.get_or_create(
            employee=employee,
            defaults={
                'salary_grade': grade,
                'basic_salary': basic_salary,
                'performance_salary': basic_salary * Decimal('0.2'),  # 绩效工资为基本工资的20%
                'allowance': basic_salary * Decimal('0.1'),  # 津贴为基本工资的10%
                'effective_date': date.today(),
                'is_active': True
            }
        )
        
        if created:
            configs_created += 1
            print(f"  为员工 {employee.name} 创建薪资配置: {basic_salary}元")
    
    print(f"员工薪资配置初始化完成，共创建 {configs_created} 个配置\n")

def init_monthly_salary_records():
    """初始化月度工资记录数据"""
    print("正在初始化月度工资记录数据...")
    
    # 获取所有有薪资配置的员工
    configs = EmployeeSalaryConfig.objects.filter(is_active=True)
    if not configs.exists():
        print("  警告: 没有找到活跃的薪资配置，请先初始化薪资配置")
        return
    
    # 为最近3个月创建工资记录
    from datetime import datetime, timedelta
    import calendar
    
    records_created = 0
    for i in range(3):  # 最近3个月
        # 计算月份
        target_date = datetime.now() - timedelta(days=30*i)
        year = target_date.year
        month = target_date.month
        
        for config in configs:
            # 检查是否已存在记录
            salary_month = datetime(year, month, 1).date()
            existing = MonthlySalary.objects.filter(
                employee=config.employee,
                salary_month=salary_month
            ).exists()
            
            if not existing:
                # 计算工资
                basic_salary = config.basic_salary
                performance_salary = config.performance_salary
                allowance = config.allowance
                bonus = Decimal('1000.00')  # 固定奖金
                overtime_pay = Decimal('500.00')  # 固定加班费
                
                # 计算应发工资
                gross_salary = basic_salary + performance_salary + allowance + bonus + overtime_pay
                
                # 计算扣除项
                social_insurance = gross_salary * Decimal('0.105')  # 社保10.5%
                housing_fund = gross_salary * Decimal('0.12')  # 公积金12%
                income_tax = max(Decimal('0.00'), (gross_salary - social_insurance - housing_fund - Decimal('5000')) * Decimal('0.1'))  # 简化个税计算
                other_deduction = Decimal('0.00')
                
                total_deduction = social_insurance + housing_fund + income_tax + other_deduction
                net_salary = gross_salary - total_deduction
                
                # 创建工资记录
                salary_record = MonthlySalary.objects.create(
                    employee=config.employee,
                    salary_month=salary_month,
                    basic_salary=basic_salary,
                    performance_salary=performance_salary,
                    allowance=allowance,
                    bonus=bonus,
                    overtime_pay=overtime_pay,
                    gross_salary=gross_salary,
                    social_insurance=social_insurance,
                    housing_fund=housing_fund,
                    income_tax=income_tax,
                    other_deduction=other_deduction,
                    total_deduction=total_deduction,
                    net_salary=net_salary,
                    pay_date=datetime(year, month, 25).date(),  # 每月25号发工资
                    status='PAID'  # 使用模型中定义的状态值
                )
                
                records_created += 1
    
    print(f"月度工资记录初始化完成，共创建 {records_created} 条记录\n")

def init_salary_adjustments():
    """初始化薪资调整记录数据"""
    print("正在初始化薪资调整记录数据...")
    
    # 获取部分员工进行薪资调整示例
    employees = Personal.objects.all()[:3]  # 取前3个员工作为示例
    
    adjustments_created = 0
    for i, employee in enumerate(employees):
        config = EmployeeSalaryConfig.objects.filter(employee=employee, is_active=True).first()
        if config:
            # 创建薪资调整记录
            old_salary = config.basic_salary
            adjustment_amount = Decimal('1000.00') * (i + 1)  # 不同的调整金额
            new_salary = old_salary + adjustment_amount
            
            adjustment = SalaryAdjustment.objects.create(
                employee=employee,
                adjustment_type='ANNUAL',  # 使用模型中定义的选择值
                old_salary=old_salary,
                new_salary=new_salary,
                adjustment_amount=adjustment_amount,
                reason=f'年度调薪 - 基于绩效表现调整',
                effective_date=date.today(),
                approver_id=1,  # 假设ID为1的用户是审批人
                approval_date=datetime.now()
            )
            
            adjustments_created += 1
            print(f"  为员工 {employee.name} 创建薪资调整记录: {old_salary} -> {new_salary}")
    
    print(f"薪资调整记录初始化完成，共创建 {adjustments_created} 条记录\n")

def main():
    """主函数"""
    print("=" * 50)
    print("工资管理系统数据初始化开始")
    print("=" * 50)
    
    try:
        # 1. 初始化薪资等级
        init_salary_grades()
        
        # 2. 初始化员工薪资配置
        init_employee_salary_configs()
        
        # 3. 初始化月度工资记录
        init_monthly_salary_records()
        
        # 4. 初始化薪资调整记录
        init_salary_adjustments()
        
        print("=" * 50)
        print("数据初始化完成！")
        print("=" * 50)
        print("\n现在您可以：")
        print("1. 访问 Django 管理后台查看数据: http://127.0.0.1:8000/admin/")
        print("2. 访问工资管理系统: http://127.0.0.1:8000/salary/")
        print("3. 查看系统流程图: http://127.0.0.1:8000/salary/workflow/")
        
    except Exception as e:
        print(f"初始化过程中出现错误: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()