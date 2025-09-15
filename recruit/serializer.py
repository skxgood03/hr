from rest_framework import serializers

from recruit.models import Recruit


class RecruitSerializer(serializers.ModelSerializer):
    stationName = serializers.CharField(source='station.stationName')
    departmentName = serializers.CharField(source='station.department.departmentName')
    stationId = serializers.IntegerField(source='station.id')
    departmentId = serializers.IntegerField(source='station.department.id')
    class Meta:
        model = Recruit
        fields = '__all__'