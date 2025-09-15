from django.core.paginator import Paginator
from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.views import APIView

from hrms.ResultPageVo import ResultPageVo
from hrms.ResultVo import ResultVo
from personal.models import Personal
from train.models import Train
from train.serializer import TrainSerializer


# Create your views here.
class TrainAddView(APIView):
    def post(self, request, *args, **kwargs):
        personalId = request.data.get('personalId')
        trainContent = request.data.get('trainContent')
        trainCost = request.data.get('trainCost')
        beginDate = request.data.get('beginDate').replace('/','-')
        endDate = request.data.get('endDate').replace('/','-')
        try:
            personal = Personal.objects.get(id=personalId)
            msg = Train.objects.create(trainContent=trainContent, trainCost=trainCost,
                                       beginDate=beginDate,endDate=endDate,
                                       personal=personal)
            if msg:
                return Response(ResultVo.success('添加成功'))
            return Response(ResultVo.fail('添加失败'))
        except Personal.DoesNotExist:
            return Response(ResultVo.fail('添加失败'))

class TrainListView(APIView):
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
        # 员工姓名
        name = request.query_params.get('name')
        # 获取所有的培训信息
        trains = Train.objects.all().order_by("id")
        # 通过部门查询
        if name:
            #获取该部门下的所有岗位ID
            personalIds = Personal.objects.all().filter(name__icontains=name).values_list('id')
            trains = trains.filter(personal__in = personalIds)

        # 进行分页
        pagination = Paginator(trains, pageSize)
        page = pagination.page(pageNum)
        # 对查询出来的数据进行序列化
        trainsSerializer = TrainSerializer(page, many=True)
        return Response(ResultPageVo.success("查询成功", pagination.count, trainsSerializer.data))

#通过奖惩ID获取奖惩信息
class TrainDetailByIdView(APIView):
    def get(self, request):
        id = request.query_params.get('id')
        try:
            train = Train.objects.get(id = id)
            trainSerializer = TrainSerializer(train)
            return Response(ResultVo.success("获取成功", trainSerializer.data))
        except Train.DoesNotExit:
            return Response(ResultVo.fail('获取失败'))

class TrainUpdateByIdView(APIView):
    def put(self, request, *args, **kwargs):

        id = request.query_params.get('id')
        personalId = request.query_params.get('personalId')
        trainContent = request.query_params.get('trainContent')
        trainCost = request.query_params.get('trainCost')
        beginDate = request.query_params.get('beginDate').replace('/', '-')
        endDate = request.query_params.get('endDate').replace('/', '-')

        try:
            personal = Personal.objects.get(id = personalId)
            msg = Train.objects.filter(id = id).update(trainContent=trainContent, trainCost=trainCost,
                                       beginDate=beginDate,endDate=endDate,
                                       personal=personal)
            if msg:
                return Response(ResultVo.success('更新成功'))
        except Train.DoesNotExist:
            return Response(ResultVo.fail('更新失败'))


class TrainDeleteByIdView(APIView):
    def delete(self, request, *args, **kwargs):
        id = request.query_params.get('id')
        try:
            train = Train.objects.get(id = id)
            train.delete()
            return Response(ResultVo.success('删除成功'))
        except Train.DoesNotExit:
            return Response(ResultVo.fail('删除失败'))