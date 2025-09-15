from rest_framework import serializers

from train.models import Train


class TrainSerializer(serializers.ModelSerializer):
    stationName = serializers.CharField(source='personal.station.stationName')
    departmentName = serializers.CharField(source='personal.station.department.departmentName')
    stationId = serializers.IntegerField(source='personal.station.id')
    departmentId = serializers.IntegerField(source='personal.station.department.id')
    # 关联人员ID
    personalId = serializers.IntegerField(source='personal.id')
    # 关联员工姓名
    name = serializers.CharField(source='personal.name')
    class Meta:
        model = Train
        fields = '__all__'