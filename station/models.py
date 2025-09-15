from django.db import models

from department.models import Department


# Create your models here.
class Station(models.Model):
    stationName = models.CharField(max_length=50)
    description = models.TextField()
    department = models.ForeignKey(Department,db_column='departmentId', on_delete=models.CASCADE)
    
    def __str__(self):
        return self.stationName
    
    class Meta:
        db_table = 't_station'
