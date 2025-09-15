from django.db import models

from station.models import Station


# Create your models here.
class Personal(models.Model):
    GENDER_CHOICES = [
        (1, '男'),
        (2, '女'),
    ]
    
    EDUCATION_CHOICES = [
        (1, '小学'),
        (2, '初中'),
        (3, '高中'),
        (4, '中专'),
        (5, '大专'),
        (6, '本科'),
        (7, '硕士'),
        (8, '博士'),
    ]
    
    WORK_STATUS_CHOICES = [
        (1, '在职'),
        (2, '离职'),
        (3, '休假'),
        (4, '试用期'),
    ]
    
    name = models.CharField(max_length=255, verbose_name='员工姓名')
    gender = models.IntegerField(choices=GENDER_CHOICES, verbose_name='性别(1:男，2:女)')
    birthday = models.CharField(max_length=255, verbose_name='生日')
    phone = models.CharField(max_length=255, verbose_name='电话号码')
    age = models.IntegerField(verbose_name='年龄')
    email = models.EmailField(verbose_name='Email')
    identity = models.CharField(max_length=255, verbose_name='身份证号')
    education = models.IntegerField(choices=EDUCATION_CHOICES, verbose_name='学历')
    school = models.CharField(max_length=255, verbose_name='毕业院校')
    beginDate = models.CharField(max_length=255, verbose_name='入职日期')
    workStatus = models.IntegerField(choices=WORK_STATUS_CHOICES, verbose_name='工作状态')
    station = models.ForeignKey(Station, db_column='stationId', on_delete=models.CASCADE)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 't_personal'
        verbose_name = '员工表'