#!/usr/bin/env python
import os
import sys
import django
import requests
import json

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hrms.settings')
django.setup()

from salary_management.models import MonthlySalary

def test_delete_api():
    """测试删除API"""
    # 获取一个草稿状态的记录
    draft_record = MonthlySalary.objects.filter(status='DRAFT').first()
    
    if not draft_record:
        print("没有找到草稿状态的记录")
        return
    
    print(f"找到草稿记录: ID={draft_record.id}, 员工={draft_record.employee.name}")
    
    # 测试删除API
    url = 'http://127.0.0.1:8000/salary/api/delete-record/'
    data = {
        'record_id': draft_record.id
    }
    
    try:
        response = requests.post(url, json=data, headers={
            'Content-Type': 'application/json',
            'X-CSRFToken': 'test'  # 在测试中使用简单的token
        })
        
        print(f"响应状态码: {response.status_code}")
        print(f"响应内容: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print("✅ 删除成功!")
                # 验证记录是否真的被删除
                if not MonthlySalary.objects.filter(id=draft_record.id).exists():
                    print("✅ 记录已从数据库中删除")
                else:
                    print("❌ 记录仍然存在于数据库中")
            else:
                print(f"❌ 删除失败: {result.get('error')}")
        else:
            print(f"❌ API调用失败: {response.status_code}")
            
    except Exception as e:
        print(f"❌ 请求异常: {e}")

if __name__ == '__main__':
    test_delete_api()