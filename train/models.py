from django.db import models

from personal.models import Personal


# Create your models here.
class Train(models.Model):
    beginDate = models.DateField(verbose_name='培训开始时间')
    endDate = models.DateField(verbose_name='培训结束时间')
    trainContent = models.CharField(max_length=255, verbose_name='培训内容')
    trainCost = models.FloatField(verbose_name='培训费用')
    personal = models.ForeignKey(Personal, db_column='personalId', on_delete=models.CASCADE, verbose_name='关联人员表')
    class Meta:
        db_table = 't_train'