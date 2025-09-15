from django.db import models

# Create your models here.
class Department(models.Model):
    departmentName = models.CharField(max_length=255, unique=True)
    description = models.TextField()
    class Meta:
        db_table = 't_department'