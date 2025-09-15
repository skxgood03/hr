#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import django

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hrms.settings')
django.setup()

from django.db import connection

def fix_migration_history():
    """修复迁移历史记录"""
    with connection.cursor() as cursor:
        # 删除attendance应用的迁移记录
        cursor.execute("DELETE FROM django_migrations WHERE app = 'attendance'")
        print("已删除attendance应用的迁移记录")
        
        # 查看当前迁移状态
        cursor.execute("SELECT app, name FROM django_migrations ORDER BY app, name")
        migrations = cursor.fetchall()
        
        print("\n当前数据库中的迁移记录:")
        for app, name in migrations:
            print(f"  {app}: {name}")

if __name__ == '__main__':
    fix_migration_history()
    print("\n迁移记录修复完成，现在可以重新运行迁移命令")