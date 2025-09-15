from rest_framework import serializers

from station.models import Station


class StationSerializer(serializers.ModelSerializer):
    departmentName = serializers.CharField(source='department.departmentName')
    departmentId = serializers.IntegerField(source='department.id')
    class Meta:
        model = Station
        fields = '__all__'