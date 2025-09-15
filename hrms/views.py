from django.shortcuts import render
from django.db.models import Count
from department.models import Department
from personal.models import Personal
from station.models import Station
from recruit.models import Recruit
from hr.decorators import login_required

@login_required
def home(request):
    """
    首页视图
    显示系统概览和统计信息
    """
    # 获取各模块统计数据
    context = {
        'department_count': Department.objects.count(),
        'employee_count': Personal.objects.count(),
        'station_count': Station.objects.count(),
        'recruit_count': Recruit.objects.count(),
        'online_users': 1,  # 暂时固定为1，后续可以实现真实的在线用户统计
        'recent_activities': [],  # 暂时为空，后续可以添加活动日志功能
    }
    
    return render(request, 'home.html', context)