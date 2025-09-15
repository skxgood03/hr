from rest_framework import serializers

from personal.models import Personal


class PersonalSerializer(serializers.ModelSerializer):
    #岗位名称
    stationName =serializers.CharField(source='station.stationName')
    departmentName =serializers.CharField(source='station.department.departmentName')
    stationId = serializers.IntegerField(source='station.id')
    departmentId = serializers.IntegerField(source='station.department.id')
    class Meta:
        model = Personal
        fields = '__all__'