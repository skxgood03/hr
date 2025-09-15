from django.core.paginator import Paginator
from rest_framework.response import Response
from rest_framework.views import APIView

from hrms.ResultPageVo import ResultPageVo
from hrms.ResultVo import ResultVo
from recruit.models import Recruit
from recruit.serializer import RecruitSerializer
from station.models import Station


# Create your views here.
class RecruitAddView(APIView):
    def post(self, request, *args, **kwargs):
        stationId = request.data.get('stationId')
        needNum = request.data.get('needNum')
        demand = request.data.get('demand')
        needEducation = request.data.get('needEducation')
        recruitStatus = request.data.get('recruitStatus')
        startDate = request.data.get('startDate').replace('/','-')
        endDate = request.data.get('endDate').replace('/','-')
        try:
            station = Station.objects.get(id=stationId)
            msg = Recruit.objects.create(needNum=needNum,demand=demand,needEducation=needEducation,
                                         recruitStatus=recruitStatus,
                                         startDate=startDate,endDate=endDate,station=station)
            if msg:
                return Response(ResultVo.success('添加成功'))
            return Response(ResultVo.fail('添加失败'))
        except Station.DoesNotExist:
            return Response(ResultVo.fail('添加失败'))

class RecruitListView(APIView):
    def get(self, request, *args, **kwargs):
        # 获取请求参数
        # 页数
        pageNum = request.query_params.get('pageNum', '1')
        # 获取每页显示条数
        pageSize = request.query_params.get('pageSize', '10')
        
        # 处理分页参数
        try:
            pageNum = int(pageNum)
            pageSize = int(pageSize)
        except (ValueError, TypeError):
            pageNum = 1
            pageSize = 10
        # 部门ID
        departmentId = request.query_params.get('departmentId')
        recruitStatus = request.query_params.get('recruitStatus')
        # 获取所有的招聘信息
        recruits = Recruit.objects.all().order_by("id")
        # 通过部门查询
        if departmentId:
            #获取该部门下的所有岗位ID
            stationId = Station.objects.all().filter(department = departmentId).values_list('id')
            recruits = recruits.filter(station__in = stationId)

        if recruitStatus:
            recruits = recruits.filter(recruitStatus = recruitStatus)

        # 进行分页
        pagination = Paginator(recruits, pageSize)
        page = pagination.page(pageNum)
        # 对查询出来的数据进行序列化
        recruitsSerializer = RecruitSerializer(page, many=True)
        return Response(ResultPageVo.success("查询成功", pagination.count, recruitsSerializer.data))

#通过奖惩ID获取奖惩信息
class RecruitDetailByIdView(APIView):
    def get(self, request, *args, **kwargs):
        id = request.query_params.get('id')
        try:
            recruit = Recruit.objects.get(id = id)
            recruitSerializer = RecruitSerializer(recruit)
            return Response(ResultVo.success("获取成功", recruitSerializer.data))
        except Recruit.DoesNotExit:
            return Response(ResultVo.fail('获取失败'))

#修改惩罚数据
class RecruitUpdateByIdView(APIView):
    def put(self, request, *args, **kwargs):

        id = request.query_params.get('id')
        stationId = request.query_params.get('stationId')
        needNum = request.query_params.get('needNum')
        demand = request.query_params.get('demand')
        needEducation = request.query_params.get('needEducation')
        recruitStatus = request.query_params.get('recruitStatus')
        startDate = request.query_params.get('startDate').replace('/', '-')
        endDate = request.query_params.get('endDate').replace('/', '-')

        try:
            station = Station.objects.get(id = stationId)
            msg = Recruit.objects.filter(id = id).update(needNum=needNum,demand=demand,
                                                         needEducation=needEducation,recruitStatus=recruitStatus,
                                                         startDate=startDate,endDate=endDate,station=station)
            if msg:
                return Response(ResultVo.success('更新成功'))
        except Station.DoesNotExist:
            return Response(ResultVo.fail('更新失败'))


class RecruitDeleteByIdView(APIView):
    def delete(self, request, *args, **kwargs):
        id = request.query_params.get('id')
        try:
            recruit = Recruit.objects.get(id = id)
            recruit.delete()
            return Response(ResultVo.success('删除成功'))
        except Recruit.DoesNotExit:
            return Response(ResultVo.fail('删除失败'))