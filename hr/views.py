from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Q
from django.utils import timezone
from datetime import datetime
import json

from hr.models import User
from personal.models import Personal
from salary_management.models import MonthlySalary
from hrms.ResultVo import ResultVo

# 员工权限装饰器
def employee_required(view_func):
    def wrapper(request, *args, **kwargs):
        if 'username' not in request.session:
            return redirect('/login-page/')
        
        try:
            username = request.session['username']
            user = User.objects.get(username=username)
            if user.role.name != 'EMPLOYEE' or not user.employee:
                return JsonResponse({'success': False, 'message': '权限不足'})
            return view_func(request, *args, **kwargs)
        except User.DoesNotExist:
            return redirect('/login-page/')
    return wrapper


# Create your views here.
#创建一个视图类用来处理登陆
class LoginView(APIView):
    def post(self,request):
        username = request.data['username']
        password = request.data['password']
        if username and password:
            try:
                user = User.objects.get(username=username)
                 #登陆成功
                if user.password == password:
                    request.session['username'] = username
                    request.session['user_id'] = user.id
                    request.session['user_role'] = user.role.name if user.role else None
                    
                    # 为员工角色用户设置employee_id
                    if user.role and user.role.name == 'EMPLOYEE' and user.employee_id:
                        request.session['employee_id'] = user.employee_id
                    
                    # 根据用户角色确定重定向URL
                    redirect_url = '/hr/employee/center/' if user.role.name == 'EMPLOYEE' else '/'
                    return Response(ResultVo.success("登陆成功",{'username':username, 'redirect_url': redirect_url}))
                return Response(ResultVo.fail("你输入的密码不正确"))
            except User.DoesNotExist:
                return Response(ResultVo.fail("你输入的用户名不正确"))
        return Response(ResultVo.fail("请输入用户名或者密码"))

class LogoutView(APIView):
    def get(self, request):
        if 'username' in request.session:
            del request.session['username']
        return Response(ResultVo.success('退出成功'))

# 登录页面视图
def login_page(request):
    # 如果用户已经登录，重定向到首页
    if 'username' in request.session:
        # 根据用户角色重定向到不同页面
        try:
            username = request.session['username']
            user = User.objects.get(username=username)
            if user.role.name == 'EMPLOYEE':
                return redirect('/hr/employee/center/')  # 员工重定向到个人中心
            else:
                return redirect('/')  # 其他角色重定向到首页
        except User.DoesNotExist:
            pass
    return render(request, 'login.html')

# 员工个人中心视图
@employee_required
def employee_center(request):
    """员工个人中心页面"""
    username = request.session['username']
    try:
        user = User.objects.get(username=username)
        
        # 获取关联的员工信息
        employee = user.employee
        if not employee:
            return render(request, 'employee/center.html', {
                'error': '未找到关联的员工信息，请联系管理员'
            })
        
        # 获取最新的工资记录
        latest_salary = MonthlySalary.objects.filter(
            employee=employee,
            status__in=['APPROVED', 'PAID']
        ).order_by('-salary_month').first()
        
        context = {
            'user': user,
            'employee': employee,
            'latest_salary': latest_salary,
        }
        return render(request, 'employee/center.html', context)
        
    except User.DoesNotExist:
        return redirect('/login-page/')

# 员工工资单查看API
@employee_required
def employee_salary_list(request):
    """获取员工工资单列表"""
    username = request.session['username']
    try:
        user = User.objects.get(username=username)
        
        # 获取分页参数
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 10))
        
        # 获取员工的工资记录
        salary_records = MonthlySalary.objects.filter(
            employee=user.employee,
            status__in=['APPROVED', 'PAID']
        ).order_by('-salary_month')
        
        # 计算分页
        total = salary_records.count()
        start = (page - 1) * page_size
        end = start + page_size
        records = salary_records[start:end]
        
        # 构造返回数据
        data = []
        for record in records:
            data.append({
                'id': record.id,
                'salary_month': record.salary_month.strftime('%Y年%m月'),
                'gross_salary': float(record.gross_salary),
                'net_salary': float(record.net_salary),
                'status': record.get_status_display(),
                'pay_date': record.pay_date.strftime('%Y-%m-%d') if record.pay_date else None,
            })
        
        return JsonResponse({
            'success': True,
            'data': data,
            'total': total,
            'page': page,
            'page_size': page_size,
            'total_pages': (total + page_size - 1) // page_size,
            'has_next': page * page_size < total,
            'has_previous': page > 1,
        })
        
    except User.DoesNotExist:
        return JsonResponse({'success': False, 'message': '用户不存在'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'查询失败: {str(e)}'})

# 员工工资单详情API
@employee_required
def employee_salary_detail(request, salary_id):
    """获取员工工资单详情"""
    username = request.session['username']
    try:
        user = User.objects.get(username=username)
        
        # 获取工资记录，确保只能查看自己的
        salary_record = MonthlySalary.objects.get(
            id=salary_id,
            employee=user.employee,
            status__in=['APPROVED', 'PAID']
        )
        
        # 获取考勤薪资明细
        attendance_detail = None
        try:
            attendance_detail = salary_record.attendance_detail
        except:
            pass
        
        data = {
            'id': salary_record.id,
            'employee_name': salary_record.employee.name,
            'salary_month': salary_record.salary_month.strftime('%Y年%m月'),
            'basic_salary': float(salary_record.basic_salary),
            'performance_salary': float(salary_record.performance_salary),
            'allowance': float(salary_record.allowance),
            'bonus': float(salary_record.bonus),
            'overtime_pay': float(salary_record.overtime_pay),
            'gross_salary': float(salary_record.gross_salary),
            'social_insurance': float(salary_record.social_insurance),
            'housing_fund': float(salary_record.housing_fund),
            'income_tax': float(salary_record.income_tax),
            'other_deduction': float(salary_record.other_deduction),
            'total_deduction': float(salary_record.total_deduction),
            'net_salary': float(salary_record.net_salary),
            'status': salary_record.get_status_display(),
            'pay_date': salary_record.pay_date.strftime('%Y-%m-%d') if salary_record.pay_date else None,
            'bank_account': salary_record.bank_account or '',
            'remarks': salary_record.remarks or '',
            # 考勤薪资明细
            'attendance_detail': {
                'actual_work_days': attendance_detail.actual_work_days if attendance_detail else 0,
                'actual_work_hours': float(attendance_detail.actual_work_hours) if attendance_detail else 0,
                'personal_leave_hours': float(attendance_detail.personal_leave_hours) if attendance_detail else 0,
                'sick_leave_hours': float(attendance_detail.sick_leave_hours) if attendance_detail else 0,
                'annual_leave_hours': float(attendance_detail.annual_leave_hours) if attendance_detail else 0,
                'other_leave_hours': float(attendance_detail.other_leave_hours) if attendance_detail else 0,
                'weekday_overtime_hours': float(attendance_detail.weekday_overtime_hours) if attendance_detail else 0,
                'weekend_overtime_hours': float(attendance_detail.weekend_overtime_hours) if attendance_detail else 0,
                'holiday_overtime_hours': float(attendance_detail.holiday_overtime_hours) if attendance_detail else 0,
                'late_minutes': attendance_detail.late_minutes if attendance_detail else 0,
                'early_leave_minutes': attendance_detail.early_leave_minutes if attendance_detail else 0,
                'missing_clock_days': attendance_detail.missing_clock_days if attendance_detail else 0,
                'normal_work_pay': float(attendance_detail.normal_work_pay) if attendance_detail else 0,
                'leave_deduction': float(attendance_detail.leave_deduction) if attendance_detail else 0,
                'overtime_pay_detail': float(attendance_detail.overtime_pay) if attendance_detail else 0,
                'late_early_deduction': float(attendance_detail.late_early_deduction) if attendance_detail else 0,
                # 计算具体的加班费和扣款明细
                'weekday_overtime_pay': float(attendance_detail.weekday_overtime_hours * (salary_record.basic_salary / 22 / 8) * attendance_detail.calculation_rule.weekday_overtime_rate) if attendance_detail and attendance_detail.weekday_overtime_hours > 0 else 0,
                'weekend_overtime_pay': float(attendance_detail.weekend_overtime_hours * (salary_record.basic_salary / 22 / 8) * attendance_detail.calculation_rule.weekend_overtime_rate) if attendance_detail and attendance_detail.weekend_overtime_hours > 0 else 0,
                'holiday_overtime_pay': float(attendance_detail.holiday_overtime_hours * (salary_record.basic_salary / 22 / 8) * attendance_detail.calculation_rule.holiday_overtime_rate) if attendance_detail and attendance_detail.holiday_overtime_hours > 0 else 0,
                'late_deduction': float(attendance_detail.late_minutes * attendance_detail.calculation_rule.late_deduction_per_minute) if attendance_detail and attendance_detail.late_minutes > 0 else 0,
                'early_leave_deduction': float(attendance_detail.early_leave_minutes * attendance_detail.calculation_rule.early_leave_deduction_per_minute) if attendance_detail and attendance_detail.early_leave_minutes > 0 else 0,
                'missing_clock_deduction': float(attendance_detail.missing_clock_days * (salary_record.basic_salary / 22)) if attendance_detail and attendance_detail.missing_clock_days > 0 else 0,
                'attendance_bonus': 0,  # 全勤奖暂时设为0，可根据业务需求计算
            } if attendance_detail else None,
        }
        
        return JsonResponse({'success': True, 'data': data})
        
    except MonthlySalary.DoesNotExist:
        return JsonResponse({'success': False, 'message': '工资记录不存在或无权限查看'})
    except User.DoesNotExist:
        return JsonResponse({'success': False, 'message': '用户不存在'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'查询失败: {str(e)}'})


@employee_required
def employee_salary_download(request, salary_id):
    """员工工资单PDF下载"""
    username = request.session['username']
    try:
        user = User.objects.get(username=username)
        
        # 查询工资记录，确保只能下载自己的工资单
        salary_record = MonthlySalary.objects.get(
            id=salary_id,
            employee=user.employee,
            status__in=['APPROVED', 'PAID']
        )
        
        # 生成PDF内容（简化版本，实际项目中可以使用reportlab等库）
        from django.template.loader import render_to_string
        
        # 构造工资单数据
        context = {
            'employee': user.employee,
            'salary': salary_record,
            'generated_date': timezone.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # 渲染HTML模板
        html_content = render_to_string('employee/salary_pdf.html', context)
        
        # 返回HTML响应（在实际项目中应该转换为PDF）
        response = HttpResponse(html_content, content_type='text/html')
        response['Content-Disposition'] = f'attachment; filename="{user.employee.name}_{salary_record.salary_month.strftime("%Y%m")}_salary.html"'
        
        return response
        
    except MonthlySalary.DoesNotExist:
        return JsonResponse({'success': False, 'message': '工资记录不存在或无权限下载'})
    except User.DoesNotExist:
        return JsonResponse({'success': False, 'message': '用户不存在'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'下载失败: {str(e)}'})