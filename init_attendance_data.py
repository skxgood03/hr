#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import django
import random
from datetime import datetime, timedelta, time
from decimal import Decimal

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hrms.settings')
django.setup()

from personal.models import Personal
from attendance.models import ClockInRecord, LeaveRecord, OvertimeRecord

def clear_existing_data():
    """清除现有的考勤数据"""
    print("清除现有考勤数据...")
    ClockInRecord.objects.all().delete()
    LeaveRecord.objects.all().delete()
    OvertimeRecord.objects.all().delete()
    print("清除完成")

def generate_clock_in_records():
    """生成打卡记录"""
    print("\n生成打卡记录...")
    employees = Personal.objects.filter(workStatus=1)  # 在职员工
    
    # 生成最近30天的打卡记录
    start_date = datetime.now() - timedelta(days=30)
    
    devices = ['考勤机001', '考勤机002', '手机APP', '电脑端']
    locations = ['公司大门', '办公楼A座', '办公楼B座', '分公司']
    
    records_created = 0
    
    for employee in employees:
        for day in range(30):
            current_date = start_date + timedelta(days=day)
            
            # 跳过周末（简单处理）
            if current_date.weekday() >= 5:  # 5=周六, 6=周日
                continue
            
            # 80%的概率正常打卡
            if random.random() < 0.8:
                # 上班打卡 (8:00-9:30之间)
                clock_in_hour = random.randint(8, 9)
                clock_in_minute = random.randint(0, 59) if clock_in_hour == 8 else random.randint(0, 30)
                clock_in_time = current_date.replace(hour=clock_in_hour, minute=clock_in_minute, second=0)
                
                # 判断打卡状态
                if clock_in_hour > 9 or (clock_in_hour == 9 and clock_in_minute > 0):
                    status = 'LATE'
                else:
                    status = 'NORMAL'
                
                ClockInRecord.objects.create(
                    employee=employee,
                    clock_type='IN',
                    clock_time=clock_in_time,
                    location=random.choice(locations),
                    device=random.choice(devices),
                    status=status
                )
                records_created += 1
                
                # 下班打卡 (17:30-19:00之间)
                clock_out_hour = random.randint(17, 18)
                clock_out_minute = random.randint(30, 59) if clock_out_hour == 17 else random.randint(0, 59)
                clock_out_time = current_date.replace(hour=clock_out_hour, minute=clock_out_minute, second=0)
                
                # 判断下班状态
                if clock_out_hour < 17 or (clock_out_hour == 17 and clock_out_minute < 30):
                    out_status = 'EARLY'
                else:
                    out_status = 'NORMAL'
                
                ClockInRecord.objects.create(
                    employee=employee,
                    clock_type='OUT',
                    clock_time=clock_out_time,
                    location=random.choice(locations),
                    device=random.choice(devices),
                    status=out_status
                )
                records_created += 1
            else:
                # 20%的概率缺卡
                if random.random() < 0.5:  # 上班缺卡
                    ClockInRecord.objects.create(
                        employee=employee,
                        clock_type='IN',
                        clock_time=current_date.replace(hour=9, minute=0, second=0),
                        location='',
                        device='系统记录',
                        status='MISSING'
                    )
                    records_created += 1
                else:  # 下班缺卡
                    ClockInRecord.objects.create(
                        employee=employee,
                        clock_type='OUT',
                        clock_time=current_date.replace(hour=18, minute=0, second=0),
                        location='',
                        device='系统记录',
                        status='MISSING'
                    )
                    records_created += 1
    
    print(f"生成了 {records_created} 条打卡记录")

def generate_leave_records():
    """生成请假记录"""
    print("\n生成请假记录...")
    employees = Personal.objects.filter(workStatus=1)
    
    leave_types = ['PERSONAL', 'SICK', 'ANNUAL', 'OTHER']
    statuses = ['PENDING', 'APPROVED', 'REJECTED']
    reasons = [
        '家中有事需要处理',
        '身体不适需要休息',
        '年假休息',
        '陪同家人就医',
        '处理个人事务',
        '参加培训学习'
    ]
    
    records_created = 0
    
    # 为每个员工随机生成1-3条请假记录
    for employee in employees:
        leave_count = random.randint(1, 3)
        
        for _ in range(leave_count):
            # 随机选择最近60天内的日期
            start_date = datetime.now() - timedelta(days=random.randint(1, 60))
            
            # 请假时长1-5天
            duration_days = random.randint(1, 5)
            end_date = start_date + timedelta(days=duration_days)
            duration_hours = Decimal(str(duration_days * 8))  # 按8小时/天计算
            
            # 随机选择审批人（从其他员工中选择）
            approver = random.choice(employees.exclude(id=employee.id))
            
            leave_record = LeaveRecord.objects.create(
                employee=employee,
                leave_type=random.choice(leave_types),
                start_time=start_date,
                end_time=end_date,
                duration_hours=duration_hours,
                reason=random.choice(reasons),
                status=random.choice(statuses),
                approver=approver if random.random() < 0.8 else None,
                approved_at=datetime.now() - timedelta(days=random.randint(1, 30)) if random.random() < 0.8 else None
            )
            records_created += 1
    
    print(f"生成了 {records_created} 条请假记录")

def generate_overtime_records():
    """生成加班记录"""
    print("\n生成加班记录...")
    employees = Personal.objects.filter(workStatus=1)
    
    overtime_types = ['WEEKDAY', 'WEEKEND', 'HOLIDAY']
    statuses = ['PENDING', 'APPROVED', 'REJECTED']
    reasons = [
        '项目紧急需要加班完成',
        '处理客户紧急需求',
        '系统维护升级',
        '月末报表整理',
        '重要会议准备',
        '产品发布准备工作'
    ]
    
    records_created = 0
    
    # 为每个员工随机生成1-4条加班记录
    for employee in employees:
        overtime_count = random.randint(1, 4)
        
        for _ in range(overtime_count):
            # 随机选择最近30天内的日期
            base_date = datetime.now() - timedelta(days=random.randint(1, 30))
            
            # 加班开始时间（18:00-20:00）
            start_hour = random.randint(18, 20)
            start_time = base_date.replace(hour=start_hour, minute=0, second=0)
            
            # 加班时长2-6小时
            duration_hours = Decimal(str(random.randint(2, 6)))
            end_time = start_time + timedelta(hours=float(duration_hours))
            
            # 根据日期判断加班类型
            if base_date.weekday() >= 5:  # 周末
                overtime_type = 'WEEKEND'
            else:
                overtime_type = 'WEEKDAY'
            
            # 随机选择审批人
            approver = random.choice(employees.exclude(id=employee.id))
            
            overtime_record = OvertimeRecord.objects.create(
                employee=employee,
                start_time=start_time,
                end_time=end_time,
                duration_hours=duration_hours,
                reason=random.choice(reasons),
                overtime_type=overtime_type,
                status=random.choice(statuses),
                approver=approver if random.random() < 0.8 else None,
                approved_at=datetime.now() - timedelta(days=random.randint(1, 15)) if random.random() < 0.8 else None
            )
            records_created += 1
    
    print(f"生成了 {records_created} 条加班记录")

def print_summary():
    """打印数据统计"""
    print("\n=== 数据初始化完成 ===")
    print(f"打卡记录总数: {ClockInRecord.objects.count()}")
    print(f"请假记录总数: {LeaveRecord.objects.count()}")
    print(f"加班记录总数: {OvertimeRecord.objects.count()}")
    
    print("\n打卡状态统计:")
    for status_code, status_name in ClockInRecord.STATUS_CHOICES:
        count = ClockInRecord.objects.filter(status=status_code).count()
        print(f"  {status_name}: {count}")
    
    print("\n请假状态统计:")
    for status_code, status_name in LeaveRecord.STATUS_CHOICES:
        count = LeaveRecord.objects.filter(status=status_code).count()
        print(f"  {status_name}: {count}")
    
    print("\n加班状态统计:")
    for status_code, status_name in OvertimeRecord.STATUS_CHOICES:
        count = OvertimeRecord.objects.filter(status=status_code).count()
        print(f"  {status_name}: {count}")

def main():
    print("开始初始化考勤数据...")
    
    # 清除现有数据
    clear_existing_data()
    
    # 生成各类记录
    generate_clock_in_records()
    generate_leave_records()
    generate_overtime_records()
    
    # 打印统计信息
    print_summary()
    
    print("\n考勤数据初始化完成！")

if __name__ == '__main__':
    main()