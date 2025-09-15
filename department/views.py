from django.core.paginator import Paginator
from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Count

from department.models import Department
from hr.decorators import admin_required
from department.serializers import DepartmentSerializer
from hrms.ResultPageVo import ResultPageVo
from hrms.ResultVo import ResultVo
from station.models import Station
from personal.models import Personal


# Create your views here.
class DepartmentAddView(APIView):
    def post(self, request):
        import json
        try:
            # 处理JSON数据
            if request.content_type == 'application/json':
                data = json.loads(request.body)
            else:
                data = request.data
            
            departmentName = data.get('departmentName') or data.get('name')
            description = data.get('description', '')
            
            if not departmentName:
                return Response(ResultVo.fail('部门名称不能为空'))
            
            # 检查部门是否已存在
            if Department.objects.filter(departmentName=departmentName).exists():
                return Response(ResultVo.fail(departmentName + '部门已存在，请重新输入部门名称'))
            
            # 创建部门
            department_data = {
                'departmentName': departmentName,
                'description': description
            }
            serializer = DepartmentSerializer(data=department_data)
            if serializer.is_valid():
                serializer.save()
                return Response(ResultVo.success('添加成功'))
            else:
                return Response(ResultVo.fail('数据验证失败'))
        except Exception as e:
            return Response(ResultVo.fail('添加失败：' + str(e)))

class DepartmentListView(APIView):

    def get(self, request):
        # 获取查询的条件
        departmentName = request.query_params.get('departmentName')
        # 获取分页的页码参数
        pageNum = int(request.query_params.get('pageNum', 1))
        # 获取每页显示的条数
        pageSize = int(request.query_params.get('pageSize', 10))
        # 先获取所有的数据
        departments = Department.objects.all().order_by('id')
        if departmentName:
            # 进行模糊查询
            departments = departments.filter(departmentName__contains=departmentName)

        # 进行分页
        # 创建Paginator的对象并且设置分页的数据Paginator(data,每页显示的条数).page(页码)
        paginator_obj = Paginator(departments, pageSize)
        paginator = paginator_obj.page(pageNum)
        # 获取总条数
        count = paginator.paginator.count
        # 进行序列化
        serializer = DepartmentSerializer(paginator, many=True)
        return Response(ResultPageVo.success('列表查询成功', count, serializer.data))

class DepartmentUpdateView(APIView):
    def post(self, request):
        return self._update_department(request)
    
    def put(self, request):
        return self._update_department(request)
    
    def _update_department(self, request):
        import json
        try:
            # 处理JSON数据
            if request.content_type == 'application/json':
                data = json.loads(request.body)
            else:
                data = request.data
            
            id = data.get('id')
            departmentName = data.get('departmentName') or data.get('name')
            description = data.get('description', '')
            
            if not id or not departmentName:
                return Response(ResultVo.fail('部门ID和名称不能为空'))
            
            # 检查部门是否存在
            try:
                department = Department.objects.get(id=id)
            except Department.DoesNotExist:
                return Response(ResultVo.fail('部门不存在'))
            
            # 检查部门名称是否与其他部门重复
            existing_dept = Department.objects.filter(departmentName=departmentName).exclude(id=id).first()
            if existing_dept:
                return Response(ResultVo.fail(departmentName + '部门已存在'))
            
            # 更新部门信息
            department.departmentName = departmentName
            department.description = description
            department.save()
            
            return Response(ResultVo.success('更新成功'))
        except Exception as e:
            return Response(ResultVo.fail('更新失败：' + str(e)))
class DepartmentDeleteView(APIView):
    def post(self, request):
        return self._delete_department(request)
    
    def delete(self, request):
        return self._delete_department(request)
    
    def _delete_department(self, request):
        import json
        try:
            # 处理JSON数据
            if request.content_type == 'application/json':
                data = json.loads(request.body)
            else:
                data = request.data
            
            id = data.get('id')
            if not id:
                return Response(ResultVo.fail('部门ID不能为空'))
            
            # 检查部门下是否存在岗位
            station = Station.objects.filter(department=id).first()
            if station is not None:
                return Response(ResultVo.fail('该部门下存在岗位，无法删除'))
            
            # 删除部门
            try:
                department = Department.objects.get(id=id)
                department.delete()
                return Response(ResultVo.success('删除成功'))
            except Department.DoesNotExist:
                return Response(ResultVo.fail('部门不存在'))
        except Exception as e:
            return Response(ResultVo.fail('删除失败：' + str(e)))
class DepartmentBatchDeleteView(APIView):
    def post(self, request):
        import json
        try:
            # 处理JSON数据
            if request.content_type == 'application/json':
                data = json.loads(request.body)
            else:
                data = request.data
            
            ids = data.get('ids', [])
            if not ids:
                return Response(ResultVo.fail('请选择要删除的部门'))
            
            # 检查是否有部门下存在岗位
            departments_with_stations = []
            for dept_id in ids:
                station = Station.objects.filter(department=dept_id).first()
                if station:
                    try:
                        dept = Department.objects.get(id=dept_id)
                        departments_with_stations.append(dept.departmentName)
                    except Department.DoesNotExist:
                        pass
            
            if departments_with_stations:
                return Response(ResultVo.fail(f'以下部门下存在岗位，无法删除：{", ".join(departments_with_stations)}'))
            
            # 批量删除部门
            deleted_count = Department.objects.filter(id__in=ids).delete()[0]
            return Response(ResultVo.success(f'成功删除 {deleted_count} 个部门'))
            
        except Exception as e:
            return Response(ResultVo.fail('批量删除失败：' + str(e)))

class DepartmentDetailView(APIView):
    def get(self, request):
        departments = Department.objects.all()
        serializer = DepartmentSerializer(departments, many=True)
        return Response(ResultVo.success('获取成功', serializer.data))


# 前端页面视图函数
@admin_required
def department_list(request):
    """
    部门管理页面
    """
    # 获取所有部门并计算每个部门的员工数量
    departments = Department.objects.all().order_by('id')
    
    # 为每个部门添加员工数量
    departments_with_count = []
    for dept in departments:
        # 通过岗位关联统计员工数量
        employee_count = Personal.objects.filter(station__department=dept).count()
        dept.employee_count = employee_count
        departments_with_count.append(dept)
    
    return render(request, 'department/list.html', {'departments': departments_with_count})

@admin_required
def department_employees(request, department_id):
    """
    部门员工详情页面
    """
    try:
        department = Department.objects.get(id=department_id)
        # 获取该部门的所有员工
        employees = Personal.objects.filter(station__department=department).select_related('station')
        
        context = {
            'department': department,
            'employees': employees,
            'employee_count': employees.count()
        }
        return render(request, 'department/employees.html', context)
    except Department.DoesNotExist:
        return render(request, 'department/employees.html', {
            'error': '部门不存在',
            'department': None,
            'employees': [],
            'employee_count': 0
        })

@admin_required
def employee_detail(request, employee_id):
    """
    员工详细信息页面
    """
    try:
        employee = Personal.objects.select_related('station', 'station__department').get(id=employee_id)
        context = {
            'employee': employee
        }
        return render(request, 'personal/detail.html', context)
    except Personal.DoesNotExist:
        return render(request, 'personal/detail.html', {
            'error': '员工不存在',
            'employee': None
        })
