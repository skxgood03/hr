from functools import wraps
from django.http import JsonResponse
from django.shortcuts import redirect
from .models import User

def employee_required(view_func):
    """员工权限装饰器 - 只允许员工角色访问"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        # 检查是否登录
        if not request.session.get('user_id'):
            is_ajax = (request.headers.get('X-Requested-With') == 'XMLHttpRequest' or 
                      request.headers.get('Content-Type') == 'application/json' or
                      '/api/' in request.path or request.path.startswith('/hr/employee/salary/'))
            if is_ajax:
                return JsonResponse({'code': 4001, 'message': '请先登录'})
            return redirect('/login/')
        
        try:
            user = User.objects.get(id=request.session['user_id'])
            
            # 检查是否为员工角色
            if user.role.name != 'EMPLOYEE':
                is_ajax = (request.headers.get('X-Requested-With') == 'XMLHttpRequest' or 
                          request.headers.get('Content-Type') == 'application/json' or
                          '/api/' in request.path or request.path.startswith('/hr/employee/salary/'))
                if is_ajax:
                    return JsonResponse({'code': 4003, 'message': '权限不足，只有员工可以访问'})
                return redirect('/')
            
            # 检查是否关联了员工信息
            if not user.employee_id:
                is_ajax = (request.headers.get('X-Requested-With') == 'XMLHttpRequest' or 
                          request.headers.get('Content-Type') == 'application/json' or
                          '/api/' in request.path or request.path.startswith('/hr/employee/salary/'))
                if is_ajax:
                    return JsonResponse({'code': 4004, 'message': '员工信息未关联，请联系管理员'})
                return redirect('/')
            
            return view_func(request, *args, **kwargs)
            
        except User.DoesNotExist:
            is_ajax = (request.headers.get('X-Requested-With') == 'XMLHttpRequest' or 
                      request.headers.get('Content-Type') == 'application/json' or
                      '/api/' in request.path or request.path.startswith('/hr/employee/salary/'))
            if is_ajax:
                return JsonResponse({'code': 4002, 'message': '用户不存在'})
            return redirect('/login/')
    
    return wrapper

def login_required(view_func):
    """登录装饰器 - 要求用户必须登录"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.session.get('user_id'):
            # 检查是否为AJAX请求或API请求
            is_ajax = (request.headers.get('X-Requested-With') == 'XMLHttpRequest' or 
                      request.headers.get('Content-Type') == 'application/json' or
                      '/api/' in request.path)
            if is_ajax:
                return JsonResponse({'code': 4001, 'message': '请先登录'})
            return redirect('/login/')
        
        try:
            user = User.objects.get(id=request.session['user_id'])
            return view_func(request, *args, **kwargs)
        except User.DoesNotExist:
            if request.headers.get('Content-Type') == 'application/json':
                return JsonResponse({'success': False, 'message': '用户不存在'})
            return redirect('/login/')
    
    return wrapper

def admin_required(view_func):
    """管理员权限装饰器 - 只允许管理员角色访问"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.session.get('user_id'):
            if request.headers.get('Content-Type') == 'application/json':
                return JsonResponse({'success': False, 'message': '请先登录'})
            return redirect('/login/')
        
        try:
            user = User.objects.get(id=request.session['user_id'])
            
            if user.role.name not in ['HR', 'FINANCE']:
                if request.headers.get('Content-Type') == 'application/json':
                    return JsonResponse({'success': False, 'message': '权限不足，需要管理员权限'})
                return redirect('/')
            
            return view_func(request, *args, **kwargs)
            
        except User.DoesNotExist:
            if request.headers.get('Content-Type') == 'application/json':
                return JsonResponse({'success': False, 'message': '用户不存在'})
            return redirect('/login/')
    
    return wrapper