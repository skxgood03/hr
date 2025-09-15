from django.core.paginator import Paginator
from django.db import IntegrityError
from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.views import APIView

from department.models import Department
from hr.decorators import admin_required
from hrms.ResultPageVo import ResultPageVo
from hrms.ResultVo import ResultVo
from personal.models import Personal
from station.models import Station
from station.serializer import StationSerializer


# 前端页面视图
@admin_required
def station_list(request):
    """岗位管理页面"""
    return render(request, 'station/list.html')


# Create your views here.
class StationAddView(APIView):
    def post(self, request):
        stationName = request.data['stationName']
        description = request.data['description']
        departmentId = request.data['departmentId']
        stations = Station.objects.filter(department=departmentId).filter(stationName__icontains=stationName)
        if stations:
            return Response(ResultVo.fail('添加失败,在相同部门下不能添加重复岗位'))
        try:
            department = Department.objects.get(id=departmentId)
            msg = Station.objects.create(stationName=stationName, description=description, department=department)
            if msg:
                return Response(ResultVo.success('添加成功'))
            return Response(ResultVo.fail('添加失败'))
        except Department.DoesNotExist:
            return Response(ResultVo.fail('添加失败'))

class StationListView(APIView):
    def get(self, request):
        pageNum = request.query_params.get('pageNum', '1')
        pageSize = request.query_params.get('pageSize', '10')
        departmentId = request.query_params.get('departmentId')
        stationName = request.query_params.get('stationName')
        
        # 处理分页参数
        try:
            pageNum = int(pageNum)
            pageSize = int(pageSize)
        except (ValueError, TypeError):
            pageNum = 1
            pageSize = 10
            
        stations = Station.objects.all().order_by('id')
        if departmentId:
            stations = stations.filter(department=departmentId)
        if stationName:
            stations = stations.filter(stationName__icontains=stationName)
        paginator = Paginator(stations, pageSize)
        page = paginator.page(pageNum)
        count = paginator.count
        serializer = StationSerializer(page, many=True)
        return Response(ResultPageVo.success('查询成功', count, serializer.data))

class GetStationByIdView(APIView):
    def get(self, request):
        id = request.query_params['id']
        try:
            station = Station.objects.get(id = id)
            serializer = StationSerializer(station)
            return Response(ResultVo.success('岗位获取成功', serializer.data))
        except Station.DoesNotExist:
            return Response(ResultVo.fail('岗位获取失败'))

class GetStatioinByDepartmentIdView(APIView):
    def get(self, request):
        departmentId = request.query_params.get('departmentId')
        stations = Station.objects.all()
        if departmentId:
            stations = stations.filter(department=departmentId)
        serializer = StationSerializer(stations, many=True)
        return Response(ResultVo.success('岗位获取成功', serializer.data))

class UpdateStationView(APIView):
    def put(self, request):
        id = request.data.get('id')
        stationName = request.data.get('stationName')
        description = request.data.get('description')
        departmentId = request.data.get('departmentId')
        
        if not id:
            return Response(ResultVo.fail('岗位ID不能为空'))
        # 获取要更新的岗位
        try:
            station = Station.objects.get(id=id)
        except Station.DoesNotExist:
            return Response(ResultVo.fail('岗位不存在'))
        # 检查是否没有任何修改
        if (station.stationName == stationName and
                station.description == description and
                str(station.department.id) == departmentId):
            return Response(ResultVo.success('更新成功（无变化）'))

        # 检查相同部门下是否存在相同岗位（排除自身）
        existing_station = Station.objects.filter(
            department_id=departmentId,
            stationName=stationName
        ).exclude(id=id).exists()

        if existing_station:
            return Response(ResultVo.fail('更新失败，在相同部门下不能有重复岗位'))

        # 更新岗位信息
        update_count = Station.objects.filter(id=id).update(
            stationName=stationName,
            description=description,
            department_id=departmentId
        )

        if update_count > 0:
            return Response(ResultVo.success('更新成功'))
        else:
            return Response(ResultVo.fail('更新失败'))

class DeleteStationView(APIView):
    def delete(self, request):
        id = request.data.get('id')
        
        if not id:
            return Response(ResultVo.fail('岗位ID不能为空'))
            
        try:
            # 检查该岗位下是否存在员工
            personal = Personal.objects.filter(station=id).first()
            if personal is not None:
                return Response(ResultVo.fail('该岗位下存在员工，无法删除'))
            
            station = Station.objects.get(id=id)
            if station.delete():
                return Response(ResultVo.success('删除成功'))
            return Response(ResultVo.fail('删除失败'))
        except Station.DoesNotExist:
            return Response(ResultVo.fail('岗位不存在'))
