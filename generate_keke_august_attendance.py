#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
为员工"可可"生成8月份考勤记录的脚本
包括：整月打卡记录 + 3天事假
"""

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

def clear_keke_august_data():
    """清除可可8月份的考勤数据"""
    print("清除可可8月份的考勤数据...")
    
    try:
        keke = Personal.objects.get(id=15, name='可可')
        
        # 8月份日期范围
        august_start = datetime(2024, 8, 1)
        august_end = datetime(2024, 8, 31, 23, 59, 59)
        
        # 删除8月份的记录
        clock_deleted = ClockInRecord.objects.filter(
            employee=keke,
            clock_time__gte=august_start,
            clock_time__lte=august_end
        ).delete()[0]
        
        leave_deleted = LeaveRecord.objects.filter(
            employee=keke,
            start_time__gte=august_start,
            start_time__lte=august_end
        ).delete()[0]
        
        overtime_deleted = OvertimeRecord.objects.filter(
            employee=keke,
            start_time__gte=august_start,
            start_time__lte=august_end
        ).delete()[0]
        
        print(f"删除了可可8月份的记录：打卡{clock_deleted}条，请假{leave_deleted}条，加班{overtime_deleted}条")
        
    except Personal.DoesNotExist:
        print("错误：未找到员工'可可'")
        return False
    
    return True

def generate_keke_august_attendance():
    """为可可生成8月份考勤记录"""
    print("\n开始为可可生成8月份考勤记录...")
    
    try:
        keke = Personal.objects.get(id=15, name='可可')
    except Personal.DoesNotExist:
        print("错误：未找到员工'可可'")
        return
    
    # 8月份工作日（排除周末）
    august_2024 = datetime(2024, 8, 1)
    work_days = []
    
    # 生成8月份所有工作日
    for day in range(1, 32):  # 8月有31天
        current_date = datetime(2024, 8, day)
        # 跳过周末
        if current_date.weekday() < 5:  # 0-4是周一到周五
            work_days.append(current_date)
    
    print(f"8月份共有{len(work_days)}个工作日")
    
    # 随机选择3天作为请假日期（事假）
    leave_days = random.sample(work_days, 3)
    leave_days.sort()
    
    print(f"请假日期：{[day.strftime('%Y-%m-%d') for day in leave_days]}")
    
    # 生成请假记录
    generate_leave_records(keke, leave_days)
    
    # 生成其他工作日的打卡记录
    work_days_without_leave = [day for day in work_days if day not in leave_days]
    generate_clock_records(keke, work_days_without_leave)
    
    # 生成少量加班记录
    generate_overtime_records(keke, work_days_without_leave)
    
    print("\n可可8月份考勤记录生成完成！")

def generate_leave_records(employee, leave_days):
    """生成请假记录"""
    print("\n生成请假记录...")
    
    # 获取一个审批人（随机选择其他员工）
    approvers = Personal.objects.filter(workStatus=1).exclude(id=employee.id)
    if approvers.exists():
        approver = random.choice(approvers)
    else:
        approver = None
    
    records_created = 0
    
    for leave_day in leave_days:
        # 每天8小时事假
        start_time = leave_day.replace(hour=9, minute=0, second=0)
        end_time = leave_day.replace(hour=17, minute=0, second=0)
        
        leave_record = LeaveRecord.objects.create(
            employee=employee,
            leave_type='PERSONAL',  # 事假
            start_time=start_time,
            end_time=end_time,
            duration_hours=Decimal('8.0'),
            reason='个人事务处理',
            status='APPROVED',  # 已批准
            approver=approver,
            approved_at=leave_day - timedelta(days=random.randint(1, 3))  # 提前1-3天批准
        )
        records_created += 1
        print(f"创建请假记录：{leave_day.strftime('%Y-%m-%d')} - 事假8小时")
    
    print(f"共生成了 {records_created} 条请假记录")

def generate_clock_records(employee, work_days):
    """生成打卡记录"""
    print("\n生成打卡记录...")
    
    devices = ['考勤机001', '考勤机002', '手机APP', '电脑端']
    locations = ['公司大门', '办公楼A座', '办公楼B座']
    
    records_created = 0
    
    for work_day in work_days:
        # 90%的概率正常打卡
        if random.random() < 0.9:
            # 上班打卡 (8:00-9:15之间)
            clock_in_hour = random.randint(8, 9)
            if clock_in_hour == 8:
                clock_in_minute = random.randint(0, 59)
            else:
                clock_in_minute = random.randint(0, 15)  # 9点后最多迟到15分钟
            
            clock_in_time = work_day.replace(hour=clock_in_hour, minute=clock_in_minute, second=0)
            
            # 判断打卡状态
            if clock_in_hour > 9 or (clock_in_hour == 9 and clock_in_minute > 0):
                status = 'LATE'
            else:
                status = 'NORMAL'
            
            # 创建上班打卡记录
            ClockInRecord.objects.create(
                employee=employee,
                clock_type='IN',
                clock_time=clock_in_time,
                location=random.choice(locations),
                device=random.choice(devices),
                status=status
            )
            records_created += 1
            
            # 下班打卡 (17:30-18:30之间)
            clock_out_hour = random.randint(17, 18)
            if clock_out_hour == 17:
                clock_out_minute = random.randint(30, 59)
            else:
                clock_out_minute = random.randint(0, 30)
            
            clock_out_time = work_day.replace(hour=clock_out_hour, minute=clock_out_minute, second=0)
            
            # 判断下班状态
            if clock_out_hour < 17 or (clock_out_hour == 17 and clock_out_minute < 30):
                out_status = 'EARLY'
            else:
                out_status = 'NORMAL'
            
            # 创建下班打卡记录
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
            # 10%的概率缺卡（上班或下班）
            if random.random() < 0.5:  # 上班缺卡
                ClockInRecord.objects.create(
                    employee=employee,
                    clock_type='IN',
                    clock_time=work_day.replace(hour=9, minute=0, second=0),
                    location='',
                    device='系统记录',
                    status='MISSING'
                )
                records_created += 1
            else:  # 下班缺卡
                ClockInRecord.objects.create(
                    employee=employee,
                    clock_type='OUT',
                    clock_time=work_day.replace(hour=18, minute=0, second=0),
                    location='',
                    device='系统记录',
                    status='MISSING'
                )
                records_created += 1
    
    print(f"共生成了 {records_created} 条打卡记录")

def generate_overtime_records(employee, work_days):
    """生成少量加班记录"""
    print("\n生成加班记录...")
    
    # 随机选择2-4天加班
    overtime_count = random.randint(2, 4)
    overtime_days = random.sample(work_days, min(overtime_count, len(work_days)))
    
    # 获取审批人
    approvers = Personal.objects.filter(workStatus=1).exclude(id=employee.id)
    if approvers.exists():
        approver = random.choice(approvers)
    else:
        approver = None
    
    records_created = 0
    reasons = [
        '项目紧急需要加班完成',
        '处理客户紧急需求',
        '月末报表整理',
        '重要会议准备'
    ]
    
    for overtime_day in overtime_days:
        # 加班开始时间（18:00-19:00）
        start_hour = random.randint(18, 19)
        start_time = overtime_day.replace(hour=start_hour, minute=0, second=0)
        
        # 加班时长2-4小时
        duration_hours = Decimal(str(random.randint(2, 4)))
        end_time = start_time + timedelta(hours=float(duration_hours))
        
        overtime_record = OvertimeRecord.objects.create(
            employee=employee,
            start_time=start_time,
            end_time=end_time,
            duration_hours=duration_hours,
            reason=random.choice(reasons),
            overtime_type='WEEKDAY',
            status='APPROVED',
            approver=approver,
            approved_at=overtime_day - timedelta(days=random.randint(0, 2))
        )
        records_created += 1
        print(f"创建加班记录：{overtime_day.strftime('%Y-%m-%d')} - {duration_hours}小时")
    
    print(f"共生成了 {records_created} 条加班记录")

def print_summary():
    """打印可可8月份考勤统计"""
    print("\n=== 可可8月份考勤统计 ===")
    
    try:
        keke = Personal.objects.get(id=15, name='可可')
        
        # 8月份日期范围
        august_start = datetime(2024, 8, 1)
        august_end = datetime(2024, 8, 31, 23, 59, 59)
        
        # 统计打卡记录
        clock_records = ClockInRecord.objects.filter(
            employee=keke,
            clock_time__gte=august_start,
            clock_time__lte=august_end
        )
        
        print(f"打卡记录总数: {clock_records.count()}")
        print("打卡状态统计:")
        for status_code, status_name in ClockInRecord.STATUS_CHOICES:
            count = clock_records.filter(status=status_code).count()
            if count > 0:
                print(f"  {status_name}: {count}")
        
        # 统计请假记录
        leave_records = LeaveRecord.objects.filter(
            employee=keke,
            start_time__gte=august_start,
            start_time__lte=august_end
        )
        
        print(f"\n请假记录总数: {leave_records.count()}")
        for leave in leave_records:
            print(f"  {leave.start_time.strftime('%Y-%m-%d')}: {leave.get_leave_type_display()} - {leave.duration_hours}小时")
        
        # 统计加班记录
        overtime_records = OvertimeRecord.objects.filter(
            employee=keke,
            start_time__gte=august_start,
            start_time__lte=august_end
        )
        
        print(f"\n加班记录总数: {overtime_records.count()}")
        total_overtime_hours = sum(record.duration_hours for record in overtime_records)
        print(f"总加班时长: {total_overtime_hours}小时")
        
    except Personal.DoesNotExist:
        print("错误：未找到员工'可可'")

def main():
    print("开始为员工'可可'生成8月份考勤数据...")
    print("包括：整月打卡记录 + 3天事假 + 少量加班")
    
    # 清除现有8月份数据
    if not clear_keke_august_data():
        return
    
    # 生成新的考勤记录
    generate_keke_august_attendance()
    
    # 打印统计信息
    print_summary()
    
    print("\n可可8月份考勤数据生成完成！")

if __name__ == '__main__':
    main()