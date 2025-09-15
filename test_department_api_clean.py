#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
部门管理API接口测试脚本 - 简洁版
测试所有部门管理相关的CRUD操作
"""

import requests
import json
import sys
from datetime import datetime

class DepartmentAPITester:
    def __init__(self, base_url="http://127.0.0.1:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.test_results = []
        
    def log_result(self, test_name, success, message, response_data=None):
        """记录测试结果"""
        result = {
            'test_name': test_name,
            'success': success,
            'message': message,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        self.test_results.append(result)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {message}")
        if response_data and not success:
            print(f"   错误详情: {response_data.get('message', '无详细信息')}")
    
    def make_request(self, method, url, **kwargs):
        """统一的请求处理方法"""
        try:
            response = self.session.request(method, url, **kwargs)
            if response.status_code == 200:
                try:
                    return response.json(), None
                except json.JSONDecodeError:
                    return None, "响应不是有效的JSON格式"
            else:
                return None, f"HTTP错误: {response.status_code}"
        except Exception as e:
            return None, f"请求异常: {str(e)}"
    
    def test_add_department(self, department_name, description="测试部门描述"):
        """测试添加部门接口"""
        url = f"{self.base_url}/department/insert/"
        data = {"departmentName": department_name, "description": description}
        
        response_data, error = self.make_request('POST', url, json=data)
        if error:
            self.log_result("添加部门", False, error)
            return False
        
        if response_data.get('code') == 2000:
            self.log_result("添加部门", True, f"成功添加部门: {department_name}")
            return True
        else:
            self.log_result("添加部门", False, f"添加失败", response_data)
            return False
    
    def test_get_department_list(self, department_name=None, page_num=1, page_size=10):
        """测试获取部门列表接口"""
        url = f"{self.base_url}/department/getList/"
        params = {"pageNum": page_num, "pageSize": page_size}
        if department_name:
            params["departmentName"] = department_name
        
        response_data, error = self.make_request('GET', url, params=params)
        if error:
            self.log_result("获取部门列表", False, error)
            return []
        
        if response_data.get('code') == 2000:
            data_list = response_data.get('data', [])
            total = response_data.get('total', len(data_list))
            self.log_result("获取部门列表", True, f"成功获取 {len(data_list)} 条记录，总计 {total} 条")
            return data_list
        else:
            self.log_result("获取部门列表", False, "获取失败", response_data)
            return []
    
    def test_get_all_departments(self):
        """测试获取所有部门接口"""
        url = f"{self.base_url}/department/getDepartments/"
        
        response_data, error = self.make_request('GET', url)
        if error:
            self.log_result("获取所有部门", False, error)
            return []
        
        if response_data.get('code') == 2000:
            data_list = response_data.get('data', [])
            self.log_result("获取所有部门", True, f"成功获取 {len(data_list)} 个部门")
            return data_list
        else:
            self.log_result("获取所有部门", False, "获取失败", response_data)
            return []
    
    def test_update_department(self, department_id, department_name, description):
        """测试更新部门接口"""
        url = f"{self.base_url}/department/update/"
        params = {
            "id": department_id,
            "departmentName": department_name,
            "description": description
        }
        
        response_data, error = self.make_request('PUT', url, json=params)
        if error:
            self.log_result("更新部门", False, error)
            return False
        
        if response_data.get('code') == 2000:
            self.log_result("更新部门", True, f"成功更新部门ID: {department_id}")
            return True
        else:
            self.log_result("更新部门", False, "更新失败", response_data)
            return False
    
    def test_delete_department(self, department_id):
        """测试删除部门接口"""
        url = f"{self.base_url}/department/delete/"
        params = {"id": department_id}
        
        response_data, error = self.make_request('DELETE', url, json=params)
        if error:
            self.log_result("删除部门", False, error)
            return False
        
        if response_data.get('code') == 2000:
            self.log_result("删除部门", True, f"成功删除部门ID: {department_id}")
            return True
        else:
            self.log_result("删除部门", False, "删除失败", response_data)
            return False
    
    def run_comprehensive_test(self):
        """运行完整的测试套件"""
        print("=" * 80)
        print("部门管理API接口测试")
        print(f"测试服务器: {self.base_url}")
        print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
        
        # 1. 测试获取所有部门（初始状态）
        print("\n1. 测试获取所有部门（初始状态）")
        initial_departments = self.test_get_all_departments()
        
        # 2. 测试获取部门列表（分页）
        print("\n2. 测试获取部门列表（分页）")
        self.test_get_department_list(page_num=1, page_size=5)
        
        # 3. 测试添加部门
        print("\n3. 测试添加新部门")
        test_dept_name = f"测试部门_{datetime.now().strftime('%H%M%S')}"
        add_success = self.test_add_department(test_dept_name, "API测试创建的部门")
        
        if add_success:
            # 4. 测试重复添加部门（应该失败）
            print("\n4. 测试重复添加部门（预期失败）")
            self.test_add_department(test_dept_name, "重复的部门名称")
            
            # 5. 获取新添加的部门信息
            print("\n5. 验证部门添加结果")
            updated_departments = self.test_get_all_departments()
            new_department = None
            for dept in updated_departments:
                if dept.get('departmentName') == test_dept_name:
                    new_department = dept
                    break
            
            if new_department:
                dept_id = new_department.get('id')
                print(f"   找到新添加的部门: ID={dept_id}, 名称={test_dept_name}")
                
                # 6. 测试更新部门
                print("\n6. 测试更新部门")
                updated_name = f"{test_dept_name}_已更新"
                update_success = self.test_update_department(dept_id, updated_name, "更新后的部门描述")
                
                if update_success:
                    # 7. 验证更新结果
                    print("\n7. 验证部门更新结果")
                    self.test_get_department_list(department_name=updated_name)
                
                # 8. 测试删除部门（注意：如果有外键约束可能会失败）
                print("\n8. 测试删除部门")
                delete_success = self.test_delete_department(dept_id)
                
                if delete_success:
                    # 9. 验证删除结果
                    print("\n9. 验证部门删除结果")
                    final_departments = self.test_get_all_departments()
                    deleted = True
                    for dept in final_departments:
                        if dept.get('id') == dept_id:
                            deleted = False
                            break
                    
                    if deleted:
                        self.log_result("删除验证", True, "部门已成功从数据库中删除")
                    else:
                        self.log_result("删除验证", False, "部门仍然存在于数据库中")
                else:
                    print("   注意：删除失败可能是由于存在外键约束（如该部门下有岗位）")
        
        # 10. 测试搜索功能
        print("\n10. 测试部门搜索功能")
        if initial_departments:
            # 使用现有部门名称的一部分进行搜索
            search_term = initial_departments[0].get('departmentName', '')[:2]
            if search_term:
                self.test_get_department_list(department_name=search_term)
        
        # 输出测试总结
        self.print_test_summary()
    
    def print_test_summary(self):
        """打印测试总结"""
        print("\n" + "=" * 80)
        print("测试总结")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        
        print(f"总测试数: {total_tests}")
        print(f"通过: {passed_tests} ✅")
        print(f"失败: {failed_tests} ❌")
        print(f"成功率: {(passed_tests/total_tests*100):.1f}%")
        
        if failed_tests > 0:
            print("\n失败的测试:")
            for result in self.test_results:
                if not result['success']:
                    print(f"  - {result['test_name']}: {result['message']}")
        
        print("\n" + "=" * 80)
        
        # 总体评估
        if passed_tests == total_tests:
            print("🎉 所有测试通过！部门管理API功能完全正常。")
        elif passed_tests / total_tests >= 0.8:
            print("✅ 大部分测试通过！部门管理API基本功能正常。")
        elif passed_tests / total_tests >= 0.5:
            print("⚠️  部分测试通过，部门管理API存在一些问题需要修复。")
        else:
            print("❌ 大部分测试失败，部门管理API存在严重问题。")

def main():
    """主函数"""
    # 检查服务器是否运行
    base_url = "http://127.0.0.1:8000"
    
    try:
        response = requests.get(base_url, timeout=5)
        print(f"✅ 服务器连接正常: {base_url}")
    except requests.exceptions.RequestException as e:
        print(f"❌ 无法连接到服务器: {base_url}")
        print(f"错误信息: {e}")
        print("请确保Django开发服务器正在运行 (python manage.py runserver)")
        sys.exit(1)
    
    # 创建测试实例并运行测试
    tester = DepartmentAPITester(base_url)
    tester.run_comprehensive_test()

if __name__ == "__main__":
    main()