from django.db import models

# Create your models here.
class Role(models.Model):
    ROLE_CHOICES = [
        ('HR', 'HR'),
        ('FINANCE', '财务'),
        ('EMPLOYEE', '员工'),
    ]
    
    name = models.CharField(max_length=20, choices=ROLE_CHOICES, unique=True, verbose_name='角色名称')
    description = models.CharField(max_length=100, blank=True, verbose_name='角色描述')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    
    class Meta:
        db_table = 't_role'
        verbose_name = '角色'
        verbose_name_plural = '角色管理'
    
    def __str__(self):
        return self.get_name_display()

class User(models.Model):
    username = models.CharField(max_length=10, unique=True)
    password = models.CharField(max_length=10)
    role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='角色')
    employee_id = models.IntegerField(null=True, blank=True, verbose_name='关联员工ID', help_text='与员工表的弱关联')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    
    class Meta:
        db_table = 't_user'
        verbose_name = '用户'
        verbose_name_plural = '用户管理'
        unique_together = [['employee_id']]  # 确保一个员工只能对应一个用户
    
    def __str__(self):
        return self.username
    
    @property
    def employee(self):
        """获取关联的员工对象"""
        if self.employee_id:
            from personal.models import Personal
            try:
                return Personal.objects.get(id=self.employee_id)
            except Personal.DoesNotExist:
                return None
        return None
