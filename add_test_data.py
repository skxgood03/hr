#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
批量添加岗位管理和薪资管理测试数据
"""

import os
import sys
import django
from decimal import Decimal

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hrms.settings')
django.setup()

from department.models import Department
from personal.models import Personal
from station.models import Station
from salary.models import Salary

def add_station_data():
    """添加岗位管理测试数据"""
    print("开始添加岗位管理测试数据...")
    
    # 获取所有部门
    departments = Department.objects.all()
    
    # 岗位数据
    station_data = [
        # 人力资源部岗位
        {"stationName": "人力资源经理", "description": "负责人力资源战略规划、组织架构设计、人才招聘等工作", "department_id": 1},
        {"stationName": "招聘专员", "description": "负责公司各岗位人员招聘、面试安排、入职手续办理等工作", "department_id": 1},
        {"stationName": "培训专员", "description": "负责员工培训计划制定、培训课程组织、培训效果评估等工作", "department_id": 1},
        {"stationName": "薪酬福利专员", "description": "负责薪酬体系设计、福利政策制定、绩效考核管理等工作", "department_id": 1},
        
        # 技术部岗位
        {"stationName": "技术总监", "description": "负责技术团队管理、技术架构设计、技术发展规划等工作", "department_id": 2},
        {"stationName": "高级软件工程师", "description": "负责核心系统开发、技术难题攻关、代码审查等工作", "department_id": 2},
        {"stationName": "前端开发工程师", "description": "负责前端页面开发、用户体验优化、前端技术选型等工作", "department_id": 2},
        {"stationName": "后端开发工程师", "description": "负责后端服务开发、数据库设计、API接口开发等工作", "department_id": 2},
        {"stationName": "测试工程师", "description": "负责软件测试、测试用例编写、自动化测试等工作", "department_id": 2},
        
        # 市场部岗位
        {"stationName": "市场总监", "description": "负责市场战略制定、品牌推广、市场活动策划等工作", "department_id": 3},
        {"stationName": "市场专员", "description": "负责市场调研、竞品分析、营销方案执行等工作", "department_id": 3},
        {"stationName": "品牌经理", "description": "负责品牌形象建设、品牌传播、公关活动等工作", "department_id": 3},
        
        # 销售部岗位
        {"stationName": "销售总监", "description": "负责销售团队管理、销售目标制定、大客户维护等工作", "department_id": 4},
        {"stationName": "销售经理", "description": "负责区域销售管理、客户关系维护、销售业绩达成等工作", "department_id": 4},
        {"stationName": "销售代表", "description": "负责客户开发、产品销售、合同签订等工作", "department_id": 4},
        
        # 财务部岗位
        {"stationName": "财务总监", "description": "负责财务战略规划、财务风险控制、投资决策等工作", "department_id": 5},
        {"stationName": "会计", "description": "负责日常账务处理、财务报表编制、税务申报等工作", "department_id": 5},
        {"stationName": "出纳", "description": "负责现金管理、银行业务办理、资金收付等工作", "department_id": 5},
    ]
    
    created_count = 0
    for data in station_data:
        try:
            department = Department.objects.get(id=data['department_id'])
            station, created = Station.objects.get_or_create(
                stationName=data['stationName'],
                department=department,
                defaults={'description': data['description']}
            )
            if created:
                created_count += 1
                print(f"创建岗位: {station.stationName} - {department.departmentName}")
            else:
                print(f"岗位已存在: {station.stationName} - {department.departmentName}")
        except Department.DoesNotExist:
            print(f"部门ID {data['department_id']} 不存在，跳过岗位 {data['stationName']}")
        except Exception as e:
            print(f"创建岗位 {data['stationName']} 时出错: {str(e)}")
    
    print(f"岗位管理测试数据添加完成，共创建 {created_count} 个新岗位")
    return created_count

def add_salary_data():
    """添加薪资管理测试数据"""
    print("\n开始添加薪资管理测试数据...")
    
    # 获取所有员工
    personals = Personal.objects.all()
    
    if not personals.exists():
        print("没有找到员工数据，无法创建薪资数据")
        return 0
    
    # 薪资数据模板（根据不同岗位设置不同薪资水平）
    salary_templates = {
        # 高级管理岗位
        '总监': {'basic_min': 15000, 'basic_max': 25000, 'subsidy_min': 2000, 'subsidy_max': 5000},
        '经理': {'basic_min': 10000, 'basic_max': 18000, 'subsidy_min': 1500, 'subsidy_max': 3000},
        
        # 技术岗位
        '高级软件工程师': {'basic_min': 12000, 'basic_max': 20000, 'subsidy_min': 1000, 'subsidy_max': 2500},
        '软件工程师': {'basic_min': 8000, 'basic_max': 15000, 'subsidy_min': 800, 'subsidy_max': 2000},
        '前端开发工程师': {'basic_min': 8000, 'basic_max': 15000, 'subsidy_min': 800, 'subsidy_max': 2000},
        '后端开发工程师': {'basic_min': 8000, 'basic_max': 15000, 'subsidy_min': 800, 'subsidy_max': 2000},
        '测试工程师': {'basic_min': 7000, 'basic_max': 12000, 'subsidy_min': 600, 'subsidy_max': 1500},
        
        # 专员岗位
        '专员': {'basic_min': 5000, 'basic_max': 8000, 'subsidy_min': 500, 'subsidy_max': 1200},
        '代表': {'basic_min': 4000, 'basic_max': 7000, 'subsidy_min': 400, 'subsidy_max': 1000},
        
        # 财务岗位
        '会计': {'basic_min': 6000, 'basic_max': 10000, 'subsidy_min': 600, 'subsidy_max': 1500},
        '出纳': {'basic_min': 4500, 'basic_max': 7000, 'subsidy_min': 400, 'subsidy_max': 1000},
        
        # 默认薪资
        'default': {'basic_min': 5000, 'basic_max': 8000, 'subsidy_min': 500, 'subsidy_max': 1200}
    }
    
    import random
    created_count = 0
    
    for personal in personals:
        try:
            # 检查是否已有薪资记录
            if Salary.objects.filter(personal=personal).exists():
                print(f"员工 {personal.name} 已有薪资记录，跳过")
                continue
            
            # 根据岗位名称确定薪资模板
            station_name = getattr(personal, 'stationName', '') or ''
            template_key = 'default'
            
            for key in salary_templates.keys():
                if key != 'default' and key in station_name:
                    template_key = key
                    break
            
            template = salary_templates[template_key]
            
            # 随机生成薪资
            basic_salary = random.randint(template['basic_min'], template['basic_max'])
            subsidy_salary = random.randint(template['subsidy_min'], template['subsidy_max'])
            
            # 创建薪资记录
            salary = Salary.objects.create(
                personal=personal,
                basicSalary=basic_salary,
                subsidySalary=subsidy_salary
            )
            
            created_count += 1
            print(f"创建薪资记录: {personal.name} - 基本工资: {basic_salary}, 补助工资: {subsidy_salary}")
            
        except Exception as e:
            print(f"为员工 {personal.name} 创建薪资记录时出错: {str(e)}")
    
    print(f"薪资管理测试数据添加完成，共创建 {created_count} 条薪资记录")
    return created_count

def main():
    """主函数"""
    print("=" * 50)
    print("批量添加岗位管理和薪资管理测试数据")
    print("=" * 50)
    
    try:
        # 添加岗位数据
        station_count = add_station_data()
        
        # 添加薪资数据
        salary_count = add_salary_data()
        
        print("\n" + "=" * 50)
        print("数据添加完成！")
        print(f"共创建 {station_count} 个岗位")
        print(f"共创建 {salary_count} 条薪资记录")
        print("=" * 50)
        
    except Exception as e:
        print(f"执行过程中出现错误: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main()