#!/usr/bin/env python
"""
删除所有员工的工资记录
用于薪资管理系统重构后的数据清理
"""

import os
import sys
import django

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hrms.settings')
django.setup()

from salary_management.models import MonthlySalary
from django.db import transaction

def main():
    try:
        # 获取所有薪资记录的统计信息
        total_records = MonthlySalary.objects.count()
        print(f"删除前总记录数: {total_records}")
        
        if total_records == 0:
            print("没有薪资记录需要删除")
            return
        
        # 按状态统计
        status_counts = {}
        for status_choice in MonthlySalary.STATUS_CHOICES:
            status = status_choice[0]
            count = MonthlySalary.objects.filter(status=status).count()
            if count > 0:
                status_counts[status] = count
                print(f"  {status}: {count} 条记录")
        
        # 确认删除操作
        print(f"\n即将删除所有 {total_records} 条薪资记录")
        print("这个操作不可逆转！")
        
        # 执行删除操作
        with transaction.atomic():
            deleted_count, deleted_details = MonthlySalary.objects.all().delete()
            print(f"\n删除操作完成:")
            print(f"  总删除记录数: {deleted_count}")
            
            # 显示删除的详细信息
            if deleted_details:
                for model, count in deleted_details.items():
                    print(f"  {model}: {count} 条")
        
        # 验证删除结果
        remaining_records = MonthlySalary.objects.count()
        print(f"\n删除后剩余记录数: {remaining_records}")
        
        if remaining_records == 0:
            print("✅ 所有薪资记录已成功删除")
        else:
            print(f"⚠️  仍有 {remaining_records} 条记录未删除")
            
    except Exception as e:
        print(f"删除操作失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()