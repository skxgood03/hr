from django.db import models

from station.models import Station


# Create your models here.
class Recruit(models.Model):
    needNum = models.IntegerField(verbose_name='招聘人数')
    demand = models.CharField(verbose_name='招聘说明',max_length=255)
    needEducation = models.IntegerField(verbose_name='所需学历')
    startDate = models.DateField(verbose_name='开始时间')
    endDate = models.DateField(verbose_name='结束时间')
    recruitStatus = models.IntegerField(verbose_name='招聘状态')
    station = models.ForeignKey(Station, db_column='stationId', on_delete=models.CASCADE)
    class Meta:
        db_table = 't_recruit'
        verbose_name='招聘表'