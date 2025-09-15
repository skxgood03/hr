#!/usr/bin/env python
import os
import sys
import django
from datetime import date

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hrms.settings')
django.setup()

from personal.models import Personal
from salary_management.models import EmployeeSalaryConfig, MonthlySalary
from django.db import connection

def check_lisi_bonus_source():
    """检查李四奖金和加班费的来源"""
    try:
        # 获取李四的信息
        emp = Personal.objects.get(name='李四')
        current_month = date.today().replace(day=1)
        
        print(f"员工: {emp.name} (ID: {emp.id})")
        print(f"当前月份: {current_month}")
        
        # 获取李四当前月份的薪资记录
        salary_record = MonthlySalary.objects.filter(
            employee=emp,
            salary_month=current_month
        ).first()
        
        if salary_record:
            print(f"\n=== 当前薪资记录详情 ===")
            print(f"记录ID: {salary_record.id}")
            print(f"创建时间: {salary_record.created_at}")
            print(f"更新时间: {salary_record.updated_at}")
            print(f"基本薪资: {salary_record.basic_salary}")
            print(f"绩效薪资: {salary_record.performance_salary}")
            print(f"津贴补助: {salary_record.allowance}")
            print(f"奖金: {salary_record.bonus}")
            print(f"加班费: {salary_record.overtime_pay}")
            print(f"应发薪资: {salary_record.gross_salary}")
            print(f"状态: {salary_record.status}")
            
            # 检查是否有其他相同配置的员工
            print(f"\n=== 检查其他员工的奖金设置 ===")
            other_salaries = MonthlySalary.objects.filter(
                salary_month=current_month
            ).exclude(employee=emp)
            
            for other_salary in other_salaries:
                if other_salary.bonus > 0 or other_salary.overtime_pay > 0:
                    print(f"{other_salary.employee.name}: 奖金={other_salary.bonus}, 加班费={other_salary.overtime_pay}")
            
            # 检查数据库中是否有默认的奖金设置
            print(f"\n=== 检查薪资等级是否有默认奖金 ===")
            config = EmployeeSalaryConfig.objects.filter(employee=emp, is_active=True).first()
            if config and config.salary_grade:
                print(f"薪资等级: {config.salary_grade.grade_name}")
                print(f"等级基本薪资: {config.salary_grade.basic_salary}")
                print(f"等级绩效薪资: {config.salary_grade.performance_salary}")
                print(f"等级津贴: {config.salary_grade.allowance}")
                
                # 检查是否有其他字段可能影响奖金
                with connection.cursor() as cursor:
                    cursor.execute("""
                        SELECT column_name, data_type 
                        FROM information_schema.columns 
                        WHERE table_name = 'salary_management_salarygrade'
                        AND table_schema = DATABASE()
                    """)
                    columns = cursor.fetchall()
                    print(f"\n薪资等级表字段:")
                    for col in columns:
                        print(f"  {col[0]}: {col[1]}")
            
            # 检查是否有批量设置奖金的逻辑
            print(f"\n=== 检查是否有批量奖金设置 ===")
            all_current_salaries = MonthlySalary.objects.filter(salary_month=current_month)
            bonus_stats = {}
            overtime_stats = {}
            
            for salary in all_current_salaries:
                bonus_key = str(salary.bonus)
                overtime_key = str(salary.overtime_pay)
                
                if bonus_key not in bonus_stats:
                    bonus_stats[bonus_key] = []
                bonus_stats[bonus_key].append(salary.employee.name)
                
                if overtime_key not in overtime_stats:
                    overtime_stats[overtime_key] = []
                overtime_stats[overtime_key].append(salary.employee.name)
            
            print(f"奖金分布:")
            for bonus, employees in bonus_stats.items():
                print(f"  {bonus}: {employees}")
                
            print(f"加班费分布:")
            for overtime, employees in overtime_stats.items():
                print(f"  {overtime}: {employees}")
                
        else:
            print("未找到当前月份的薪资记录")
            
    except Personal.DoesNotExist:
        print("未找到名为'李四'的员工")
    except Exception as e:
        print(f"查询出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    check_lisi_bonus_source()