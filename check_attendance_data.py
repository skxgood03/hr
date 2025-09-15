#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import django

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hrms.settings')
django.setup()

from attendance.models import ClockInRecord, LeaveRecord, OvertimeRecord
from personal.models import Personal

def check_attendance_data():
    """检查考勤数据"""
    print("=== 考勤数据统计 ===")
    
    # 员工总数
    employee_count = Personal.objects.filter(workStatus=1).count()
    print(f"在职员工总数: {employee_count}")
    
    # 打卡记录统计
    clock_in_count = ClockInRecord.objects.count()
    print(f"\n打卡记录总数: {clock_in_count}")
    
    if clock_in_count > 0:
        print("打卡状态分布:")
        for status_code, status_name in ClockInRecord.STATUS_CHOICES:
            count = ClockInRecord.objects.filter(status=status_code).count()
            if count > 0:
                print(f"  {status_name}: {count}")
        
        print("打卡类型分布:")
        in_count = ClockInRecord.objects.filter(clock_type='IN').count()
        out_count = ClockInRecord.objects.filter(clock_type='OUT').count()
        print(f"  上班打卡: {in_count}")
        print(f"  下班打卡: {out_count}")
    
    # 请假记录统计
    leave_count = LeaveRecord.objects.count()
    print(f"\n请假记录总数: {leave_count}")
    
    if leave_count > 0:
        print("请假状态分布:")
        for status_code, status_name in LeaveRecord.STATUS_CHOICES:
            count = LeaveRecord.objects.filter(status=status_code).count()
            if count > 0:
                print(f"  {status_name}: {count}")
        
        print("请假类型分布:")
        for leave_type_code, leave_type_name in LeaveRecord.LEAVE_TYPE_CHOICES:
            count = LeaveRecord.objects.filter(leave_type=leave_type_code).count()
            if count > 0:
                print(f"  {leave_type_name}: {count}")
    
    # 加班记录统计
    overtime_count = OvertimeRecord.objects.count()
    print(f"\n加班记录总数: {overtime_count}")
    
    if overtime_count > 0:
        print("加班状态分布:")
        for status_code, status_name in OvertimeRecord.STATUS_CHOICES:
            count = OvertimeRecord.objects.filter(status=status_code).count()
            if count > 0:
                print(f"  {status_name}: {count}")
        
        print("加班类型分布:")
        for overtime_type_code, overtime_type_name in OvertimeRecord.OVERTIME_TYPE_CHOICES:
            count = OvertimeRecord.objects.filter(overtime_type=overtime_type_code).count()
            if count > 0:
                print(f"  {overtime_type_name}: {count}")
    
    # 显示部分样本数据
    print("\n=== 样本数据 ===")
    
    # 最近的打卡记录
    recent_clocks = ClockInRecord.objects.order_by('-clock_time')[:3]
    if recent_clocks:
        print("\n最近的打卡记录:")
        for record in recent_clocks:
            print(f"  {record.employee.name} - {record.get_clock_type_display()} - {record.clock_time.strftime('%Y-%m-%d %H:%M')} - {record.get_status_display()}")
    
    # 最近的请假记录
    recent_leaves = LeaveRecord.objects.order_by('-created_at')[:3]
    if recent_leaves:
        print("\n最近的请假记录:")
        for record in recent_leaves:
            print(f"  {record.employee.name} - {record.get_leave_type_display()} - {record.start_time.strftime('%Y-%m-%d')} 至 {record.end_time.strftime('%Y-%m-%d')} - {record.get_status_display()}")
    
    # 最近的加班记录
    recent_overtimes = OvertimeRecord.objects.order_by('-created_at')[:3]
    if recent_overtimes:
        print("\n最近的加班记录:")
        for record in recent_overtimes:
            print(f"  {record.employee.name} - {record.get_overtime_type_display()} - {record.start_time.strftime('%Y-%m-%d %H:%M')} - {record.duration_hours}小时 - {record.get_status_display()}")

if __name__ == '__main__':
    check_attendance_data()