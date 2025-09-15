from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count, Sum
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from datetime import datetime, date
import json
from decimal import Decimal

from .models import SalaryGrade, EmployeeSalaryConfig, MonthlySalary, SalaryAdjustment
from hr.decorators import admin_required
from .services import SalaryCalculationService, SalaryReportService, SalaryAdjustmentService
from personal.models import Personal
from department.models import Department


def salary_dashboard(request):
    """工资管理首页"""
    current_month = date.today().replace(day=1)
    
    # 统计数据
    total_employees = Personal.objects.count()
    active_configs = EmployeeSalaryConfig.objects.filter(is_active=True).count()
    current_month_records = MonthlySalary.objects.filter(salary_month=current_month).count()
    
    # 最近的工资记录
    recent_salaries = MonthlySalary.objects.select_related(
        'employee', 'employee__station', 'employee__station__department'
    ).order_by('-created_at')[:10]
    
    context = {
        'total_employees': total_employees,
        'active_configs': active_configs,
        'current_month_records': current_month_records,
        'recent_salaries': recent_salaries,
        'current_month': current_month,
    }
    
    return render(request, 'salary_management/dashboard.html', context)


@admin_required
def salary_grade_list(request):
    """薪资等级列表"""
    grades = SalaryGrade.objects.filter(is_active=True).order_by('min_salary')
    
    context = {
        'grades': grades,
    }
    
    return render(request, 'salary_management/grade_list.html', context)


@admin_required
def employee_salary_config_list(request):
    """员工薪资配置列表"""
    search = request.GET.get('search', '')
    department_id = request.GET.get('department', '')
    
    configs = EmployeeSalaryConfig.objects.select_related(
        'employee', 'employee__station', 'employee__station__department', 'salary_grade'
    ).filter(is_active=True)
    
    if search:
        configs = configs.filter(
            Q(employee__name__icontains=search) |
            Q(employee__employeeId__icontains=search)
        )
    
    if department_id:
        configs = configs.filter(employee__station__department_id=department_id)
    
    # 分页
    paginator = Paginator(configs, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # 部门列表用于筛选
    departments = Department.objects.all()
    
    context = {
        'page_obj': page_obj,
        'departments': departments,
        'search': search,
        'selected_department': department_id,
    }
    
    return render(request, 'salary_management/config_list.html', context)


def monthly_salary_list(request):
    """月度工资记录列表"""
    salary_month = request.GET.get('month', date.today().strftime('%Y-%m'))
    search = request.GET.get('search', '')
    department_id = request.GET.get('department', '')
    status = request.GET.get('status', '')
    
    try:
        month_date = datetime.strptime(salary_month, '%Y-%m').date().replace(day=1)
    except ValueError:
        month_date = date.today().replace(day=1)
    
    salaries = MonthlySalary.objects.select_related(
        'employee', 'employee__station', 'employee__station__department'
    ).filter(salary_month=month_date)
    
    if search:
        salaries = salaries.filter(
            Q(employee__name__icontains=search) |
            Q(employee__employeeId__icontains=search)
        )
    
    if department_id:
        salaries = salaries.filter(employee__station__department_id=department_id)
    
    if status:
        salaries = salaries.filter(status=status)
    
    # 分页
    paginator = Paginator(salaries, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # 统计数据
    stats = salaries.aggregate(
        total_count=Count('id'),
        total_gross=Sum('gross_salary'),
        total_net=Sum('net_salary'),
        total_social_insurance=Sum('social_insurance'),
        total_housing_fund=Sum('housing_fund'),
        total_income_tax=Sum('income_tax'),
        total_deduction=Sum('total_deduction')
    )
    
    departments = Department.objects.all()
    
    context = {
        'page_obj': page_obj,
        'departments': departments,
        'salary_month': salary_month,
        'search': search,
        'selected_department': department_id,
        'selected_status': status,
        'statistics': stats,
        'status_choices': MonthlySalary.STATUS_CHOICES,
    }
    
    return render(request, 'salary_management/monthly_list.html', context)


def salary_calculate(request):
    """工资计算页面"""
    if request.method == 'POST':
        salary_month = request.POST.get('salary_month')
        employee_ids = request.POST.getlist('employee_ids')
        
        try:
            month_date = datetime.strptime(salary_month, '%Y-%m').date().replace(day=1)
            
            if employee_ids:
                # 计算指定员工
                results, errors = SalaryCalculationService.batch_calculate_monthly_salary(
                    month_date, [int(id) for id in employee_ids]
                )
            else:
                # 计算所有员工
                results, errors = SalaryCalculationService.batch_calculate_monthly_salary(month_date)
            
            # 检查是否为AJAX请求
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'results_count': len(results),
                    'errors_count': len(errors),
                    'errors': errors
                })
            else:
                # 非AJAX请求，使用原来的重定向逻辑
                if results:
                    messages.success(request, f'成功计算 {len(results)} 名员工的工资')
                
                if errors:
                    for error in errors:
                        messages.error(request, error)
                
                return redirect('salary_management:monthly_list')
            
        except ValueError as e:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'error': str(e)
                }, status=400)
            else:
                messages.error(request, f'日期格式错误：{str(e)}')
                return redirect('salary_management:monthly_list')
        except Exception as e:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'error': str(e)
                }, status=500)
            else:
                messages.error(request, f'计算失败：{str(e)}')
                return redirect('salary_management:monthly_list')
    
    # GET请求，显示计算页面
    employees = Personal.objects.filter(workStatus=1).select_related('station__department')
    departments = Department.objects.all()
    
    context = {
        'employees': employees,
        'departments': departments,
        'current_month': '2025-10'
    }
    return render(request, 'salary_management/calculate.html', context)


@csrf_exempt
@require_http_methods(["POST"])
def api_update_housing_fund_rate(request):
    """更新员工住房公积金缴费比例"""
    try:
        if request.content_type == 'application/json':
            data = json.loads(request.body)
        else:
            data = request.POST.dict()
        employee_id = data.get('employee_id')
        housing_fund_rate = data.get('housing_fund_rate')
        
        if not employee_id or housing_fund_rate is None:
            return JsonResponse({
                'success': False,
                'message': '员工ID和住房公积金比例不能为空'
            }, status=400)
        
        # 验证比例范围
        housing_fund_rate = Decimal(str(housing_fund_rate))
        if housing_fund_rate < 0 or housing_fund_rate > 1:
            return JsonResponse({
                'success': False,
                'message': '住房公积金比例必须在0-1之间'
            }, status=400)
        
        # 获取员工当前的薪资配置
        try:
            employee = Personal.objects.get(id=employee_id)
            current_config = EmployeeSalaryConfig.objects.filter(
                employee=employee,
                is_active=True
            ).order_by('-effective_date').first()
            
            if not current_config:
                return JsonResponse({
                    'success': False,
                    'message': '该员工没有有效的薪资配置'
                }, status=400)
            
            # 更新住房公积金比例
            current_config.housing_fund_rate = housing_fund_rate
            current_config.save()
            
            return JsonResponse({
                'success': True,
                'message': f'员工 {employee.name} 的住房公积金缴费比例已更新为 {housing_fund_rate:.2%}',
                'data': {
                    'employee_id': employee_id,
                    'employee_name': employee.name,
                    'housing_fund_rate': float(housing_fund_rate)
                }
            })
            
        except Personal.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': '员工不存在'
            }, status=404)
            
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': '无效的JSON数据'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'更新失败: {str(e)}'
        }, status=500)


@require_http_methods(["GET"])
def api_get_housing_fund_rate(request, employee_id):
    """获取员工住房公积金缴费比例"""
    try:
        employee = Personal.objects.get(id=employee_id)
        current_config = EmployeeSalaryConfig.objects.filter(
            employee=employee,
            is_active=True
        ).order_by('-effective_date').first()
        
        if not current_config:
            return JsonResponse({
                'success': False,
                'message': '该员工没有有效的薪资配置'
            }, status=400)
        
        return JsonResponse({
            'success': True,
            'data': {
                'employee_id': employee_id,
                'employee_name': employee.name,
                'housing_fund_rate': float(current_config.housing_fund_rate)
            }
        })
        
    except Personal.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': '员工不存在'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'获取失败: {str(e)}'
        }, status=500)


# 薪资计算页面
@admin_required
def salary_calculate_page(request):
    """薪资计算页面"""
    employees = Personal.objects.filter(workStatus=1).select_related('station__department')  # 假设workStatus=1表示在职
    
    context = {
        'employees': employees,
        'title': '薪资计算',
        'current_month': '2025-10'  # 设置为2025年10月，确保能找到有效的薪资配置
    }
    return render(request, 'salary_management/calculate.html', context)


@csrf_exempt
@require_http_methods(["POST"])
def api_delete_salary_record(request):
    """删除工资记录API"""
    try:
        if request.content_type == 'application/json':
            data = json.loads(request.body)
        else:
            data = request.POST.dict()
        record_id = data.get('record_id')
        
        if not record_id:
            return JsonResponse({
                'success': False,
                'message': '缺少记录ID参数'
            }, status=400)
        
        # 获取工资记录
        salary_record = get_object_or_404(MonthlySalary, id=record_id)
        
        # 检查记录状态，只允许删除草稿状态的记录
        if salary_record.status != 'DRAFT':
            return JsonResponse({
                'success': False,
                'message': '只能删除草稿状态的工资记录'
            }, status=400)
        
        # 记录删除信息用于日志
        employee_name = salary_record.employee.name
        salary_month = salary_record.salary_month.strftime('%Y年%m月')
        
        # 删除记录
        salary_record.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'成功删除{employee_name}的{salary_month}工资记录'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': '请求数据格式错误'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'删除失败：{str(e)}'
        }, status=500)





def salary_slip(request, employee_id, salary_month):
    """工资条详情"""
    try:
        month_date = datetime.strptime(salary_month, '%Y-%m').date().replace(day=1)
        slip_data = SalaryReportService.generate_salary_slip(employee_id, month_date)
        
        context = {
            'slip_data': slip_data,
        }
        
        return render(request, 'salary_management/salary_slip.html', context)
        
    except ValueError as e:
        messages.error(request, str(e))
        return redirect('salary_management:monthly_list')


def print_salary_slip(request, salary_id):
    """打印工资条API接口"""
    try:
        # 获取工资记录
        monthly_salary = get_object_or_404(MonthlySalary, id=salary_id)
        
        # 生成工资条数据
        slip_data = SalaryReportService.generate_salary_slip(
            monthly_salary.employee.id, 
            monthly_salary.salary_month
        )
        
        # 如果是AJAX请求，返回打印页面的URL
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            print_url = f"/salary/slip/{monthly_salary.employee.id}/{monthly_salary.salary_month.strftime('%Y-%m')}/"
            return JsonResponse({
                'success': True,
                'print_url': print_url,
                'employee_name': monthly_salary.employee.name,
                'salary_month': monthly_salary.salary_month.strftime('%Y年%m月')
            })
        
        # 直接渲染工资条页面
        context = {
            'slip_data': slip_data,
        }
        
        return render(request, 'salary_management/salary_slip.html', context)
        
    except Exception as e:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)
        else:
            messages.error(request, f'打印工资条失败：{str(e)}')
            return redirect('salary_management:monthly_list')


def department_report(request):
    """部门工资报表"""
    department_id = request.GET.get('department')
    salary_month = request.GET.get('month', date.today().strftime('%Y-%m'))
    
    departments = Department.objects.all()
    report_data = None
    
    if department_id:
        try:
            month_date = datetime.strptime(salary_month, '%Y-%m').date().replace(day=1)
            report_data = SalaryReportService.generate_department_report(
                int(department_id), month_date
            )
        except (ValueError, TypeError) as e:
            messages.error(request, str(e))
    
    context = {
        'departments': departments,
        'selected_department': department_id,
        'salary_month': salary_month,
        'report_data': report_data,
    }
    
    return render(request, 'salary_management/department_report.html', context)


def company_summary(request):
    """公司工资汇总"""
    salary_month = request.GET.get('month', date.today().strftime('%Y-%m'))
    
    try:
        month_date = datetime.strptime(salary_month, '%Y-%m').date().replace(day=1)
        summary_data = SalaryReportService.generate_company_summary(month_date)
        
        context = {
            'salary_month': salary_month,
            'summary_data': summary_data,
        }
        
        return render(request, 'salary_management/company_summary.html', context)
        
    except ValueError as e:
        messages.error(request, str(e))
        return render(request, 'salary_management/company_summary.html', {
            'salary_month': salary_month,
        })


# API接口
@csrf_exempt
@require_http_methods(["POST"])
def api_preview_calculation(request):
    """API: 预览工资计算结果"""
    try:
        if request.content_type == 'application/json':
            data = json.loads(request.body)
        else:
            data = request.POST.dict()
        salary_month = data.get('salary_month')
        employee_ids = data.get('employee_ids', [])
        
        if not salary_month:
            return JsonResponse({
                'success': False,
                'error': '请选择工资月份'
            }, status=400)
        
        month_date = datetime.strptime(salary_month, '%Y-%m').date().replace(day=1)
        
        # 获取要计算的员工列表
        if employee_ids:
            employees = Personal.objects.filter(id__in=employee_ids, workStatus=1)
        else:
            # 获取所有有薪资配置的在职员工
            config_employee_ids = EmployeeSalaryConfig.objects.filter(
                effective_date__lte=month_date,
                is_active=True
            ).filter(
                Q(end_date__isnull=True) | Q(end_date__gte=month_date)
            ).values_list('employee_id', flat=True).distinct()
            employees = Personal.objects.filter(id__in=config_employee_ids, workStatus=1)
        
        preview_data = []
        total_gross = Decimal('0')
        total_net = Decimal('0')
        error_count = 0
        
        for employee in employees:
            try:
                # 检查是否已存在该月工资记录
                existing_record = MonthlySalary.objects.filter(
                    employee=employee,
                    salary_month=month_date
                ).first()
                
                if existing_record:
                    # 使用现有记录
                    gross_salary = existing_record.gross_salary
                    net_salary = existing_record.net_salary
                    status = '已计算'
                else:
                    # 模拟计算（不保存到数据库）
                    config = EmployeeSalaryConfig.objects.filter(
                        employee=employee,
                        effective_date__lte=month_date,
                        is_active=True
                    ).filter(
                        Q(end_date__isnull=True) | Q(end_date__gte=month_date)
                    ).first()
                    
                    if not config:
                        preview_data.append({
                            'employee_id': employee.id,
                            'employee_name': employee.name,
                            'department': employee.department.name if employee.department else '未分配',
                            'error': '未找到薪资配置'
                        })
                        error_count += 1
                        continue
                    
                    # 简化的工资计算逻辑
                    gross_salary = config.basic_salary + (config.performance_salary or Decimal('0'))
                    # 使用服务计算社保和公积金
                    social_insurance = SalaryCalculationService.calculate_social_insurance(config.basic_salary)
                    housing_fund = SalaryCalculationService.calculate_housing_fund(config.basic_salary, config.housing_fund_rate)
                    deductions = social_insurance + housing_fund
                    net_salary = gross_salary - deductions
                    status = '待计算'
                
                preview_data.append({
                    'employee_id': employee.id,
                    'employee_name': employee.name,
                    'department': employee.station.department.departmentName if employee.station and employee.station.department else '未分配',
                    'gross_salary': float(gross_salary),
                    'net_salary': float(net_salary),
                    'status': status
                })
                
                total_gross += gross_salary
                total_net += net_salary
                
            except Exception as e:
                preview_data.append({
                    'employee_id': employee.id,
                    'employee_name': employee.name,
                    'department': employee.station.department.departmentName if employee.station and employee.station.department else '未分配',
                    'error': str(e)
                })
                error_count += 1
        
        return JsonResponse({
            'success': True,
            'data': {
                'preview_list': preview_data,
                'summary': {
                    'total_employees': len(employees),
                    'success_count': len(employees) - error_count,
                    'error_count': error_count,
                    'total_gross': float(total_gross),
                    'total_net': float(total_net)
                }
            }
        })
        
    except ValueError as e:
        return JsonResponse({
            'success': False,
            'error': f'日期格式错误：{str(e)}'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def api_calculate_salary(request):
    """API: 计算单个员工工资"""
    try:
        if request.content_type == 'application/json':
            data = json.loads(request.body)
        else:
            data = request.POST.dict()
        employee_id = data.get('employee_id')
        salary_month = data.get('salary_month')
        
        month_date = datetime.strptime(salary_month, '%Y-%m').date().replace(day=1)
        monthly_salary = SalaryCalculationService.calculate_monthly_salary(
            employee_id, month_date
        )
        
        return JsonResponse({
            'success': True,
            'data': {
                'id': monthly_salary.id,
                'employee_name': monthly_salary.employee.name,
                'gross_salary': str(monthly_salary.gross_salary),
                'net_salary': str(monthly_salary.net_salary),
                'status': monthly_salary.status,
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


def api_get_employees(request):
    """API: 获取员工列表（用于下拉框）"""
    try:
        # 获取还没有薪资配置的员工
        configured_employee_ids = EmployeeSalaryConfig.objects.filter(
            is_active=True
        ).values_list('employee_id', flat=True)
        
        employees = Personal.objects.exclude(
            id__in=configured_employee_ids
        ).select_related('station', 'station__department').order_by('name')
        
        employee_list = []
        for emp in employees:
            employee_list.append({
                'id': emp.id,
                'name': emp.name,
                'employee_id': emp.id,  # 使用id作为员工ID
                'station': emp.station.stationName if emp.station else '未分配',
                'department': emp.station.department.departmentName if emp.station and emp.station.department else '未分配'
            })
        
        return JsonResponse({
            'success': True,
            'data': employee_list
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


def api_get_salary_grades(request):
    """API: 获取薪资等级列表（用于下拉框）"""
    try:
        grades = SalaryGrade.objects.filter(is_active=True).order_by('min_salary')
        
        grade_list = []
        for grade in grades:
            grade_list.append({
                'id': grade.id,
                'grade_name': grade.grade_name,
                'min_salary': float(grade.min_salary),
                'max_salary': float(grade.max_salary),
                'description': grade.description or ''
            })
        
        return JsonResponse({
            'success': True,
            'data': grade_list
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@csrf_exempt
@require_http_methods(["POST"])
def api_create_salary_config(request):
    """API: 创建员工薪资配置"""
    try:
        if request.content_type == 'application/json':
            data = json.loads(request.body)
        else:
            data = request.POST.dict()
        
        # 获取参数验证必填字段
        required_fields = ['employee', 'salary_grade', 'basic_salary', 'effective_date']
        for field in required_fields:
            if not data.get(field):
                return JsonResponse({
                    'success': False,
                    'error': f'缺少必填字段: {field}'
                }, status=400)
        
        # 获取员工和薪资等级对象
        try:
            employee = Personal.objects.get(id=data['employee'])
            salary_grade = SalaryGrade.objects.get(id=data['salary_grade'])
        except Personal.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': '员工不存在'
            }, status=400)
        except SalaryGrade.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': '薪资等级不存在'
            }, status=400)
        
        # 解析生效日期
        effective_date = datetime.strptime(data['effective_date'], '%Y-%m-%d').date()
        
        # 验证基本工资是否在薪资等级范围内
        basic_salary = Decimal(str(data['basic_salary']))
        if not (salary_grade.min_salary <= basic_salary <= salary_grade.max_salary):
            return JsonResponse({
                'success': False,
                'error': f'基本工资 {basic_salary} 不在薪资等级范围 {salary_grade.min_salary}-{salary_grade.max_salary} 内'
            }, status=400)
        
        # 检查员工在该生效日期是否已有薪资配置（包括非活跃的）
        existing_config = EmployeeSalaryConfig.objects.filter(
            employee=employee,
            effective_date=effective_date
        ).first()
        
        if existing_config:
            if existing_config.is_active:
                return JsonResponse({
                    'success': False,
                    'error': f'员工 {employee.name} 在 {effective_date} 已有活跃的薪资配置，请选择其他生效日期'
                }, status=400)
            else:
                # 如果存在非活跃配置，更新为活跃状态并更新相关信息
                existing_config.salary_grade = salary_grade
                existing_config.basic_salary = basic_salary
                existing_config.performance_salary = Decimal(str(data.get('performance_bonus', '0')))
                existing_config.allowance = Decimal(str(data.get('allowances', '0')))
                existing_config.is_active = True
                existing_config.end_date = None  # 清除结束日期
                existing_config.save()
                
                # 停用员工其他有效的薪资配置
                other_active_configs = EmployeeSalaryConfig.objects.filter(
                    employee=employee,
                    is_active=True
                ).exclude(id=existing_config.id)
                
                for other_config in other_active_configs:
                    if effective_date > other_config.effective_date:
                        other_config.end_date = effective_date
                        other_config.is_active = False
                        other_config.save()
                
                config = existing_config
        else:
            # 检查员工是否已有其他有效的薪资配置
            active_config = EmployeeSalaryConfig.objects.filter(
                employee=employee,
                is_active=True
            ).first()
            
            if active_config:
                # 如果新配置的生效日期更晚，则停用旧配置
                if effective_date > active_config.effective_date:
                    active_config.end_date = effective_date
                    active_config.is_active = False
                    active_config.save()
            
            # 创建新的薪资配置
            config = EmployeeSalaryConfig.objects.create(
                employee=employee,
                salary_grade=salary_grade,
                basic_salary=basic_salary,
                performance_salary=Decimal(str(data.get('performance_bonus', '0'))),
                allowance=Decimal(str(data.get('allowances', '0'))),
                effective_date=effective_date,
                is_active=True
            )
        
        return JsonResponse({
            'success': True,
            'message': f'员工 {employee.name} 的薪资配置创建成功',
            'data': {
                'config_id': config.id,
                'employee_name': employee.name,
                'salary_grade': salary_grade.grade_name,
                'basic_salary': float(config.basic_salary)
            }
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': '无效的JSON数据'
        }, status=400)
    except ValueError as e:
        return JsonResponse({
            'success': False,
            'error': f'数据格式错误: {str(e)}'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


def api_get_salary_config(request, config_id):
    """API: 获取薪资配置详情"""
    try:
        config = EmployeeSalaryConfig.objects.select_related(
            'employee', 'salary_grade'
        ).get(id=config_id)
        
        config_data = {
            'id': config.id,
            'employee_id': config.employee.id,
            'employee_name': config.employee.name,
            'salary_grade_id': config.salary_grade.id,
            'salary_grade_name': config.salary_grade.grade_name,
            'basic_salary': str(config.basic_salary),
            'performance_salary': str(config.performance_salary),
            'allowance': str(config.allowance),
            'effective_date': config.effective_date.strftime('%Y-%m-%d'),
            'is_active': config.is_active
        }
        
        return JsonResponse({
            'success': True,
            'data': config_data
        })
        
    except EmployeeSalaryConfig.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': '薪资配置不存在'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@csrf_exempt
@require_http_methods(["POST"])
def api_update_salary_config(request, config_id):
    """API: 更新薪资配置"""
    try:
        if request.content_type == 'application/json':
            data = json.loads(request.body)
        else:
            data = request.POST.dict()
        
        # 获取配置对象
        try:
            config = EmployeeSalaryConfig.objects.get(id=config_id)
        except EmployeeSalaryConfig.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': '薪资配置不存在'
            }, status=404)
        
        # 验证必填字段
        required_fields = ['salary_grade', 'basic_salary', 'effective_date']
        for field in required_fields:
            if not data.get(field):
                return JsonResponse({
                    'success': False,
                    'error': f'缺少必填字段: {field}'
                }, status=400)
        
        # 获取薪资等级对象
        try:
            salary_grade = SalaryGrade.objects.get(id=data['salary_grade'])
        except SalaryGrade.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': '薪资等级不存在'
            }, status=400)
        
        # 验证基本工资是否在薪资等级范围内
        basic_salary = Decimal(str(data['basic_salary']))
        if not (salary_grade.min_salary <= basic_salary <= salary_grade.max_salary):
            return JsonResponse({
                'success': False,
                'error': f'基本工资必须在{salary_grade.min_salary}-{salary_grade.max_salary}元范围内'
            }, status=400)
        
        # 更新配置
        config.salary_grade = salary_grade
        config.basic_salary = basic_salary
        config.performance_salary = Decimal(str(data.get('performance_bonus', '0')))
        config.allowance = Decimal(str(data.get('allowances', '0')))
        config.effective_date = datetime.strptime(data['effective_date'], '%Y-%m-%d').date()
        config.save()
        
        return JsonResponse({
            'success': True,
            'message': '薪资配置更新成功'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': '无效的JSON数据'
        }, status=400)
    except ValueError as e:
        return JsonResponse({
            'success': False,
            'error': f'数据格式错误: {str(e)}'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@csrf_exempt
@require_http_methods(["POST"])
def api_deactivate_salary_config(request, config_id):
    """API: 停用薪资配置"""
    try:
        config = EmployeeSalaryConfig.objects.get(id=config_id)
        
        if not config.is_active:
            return JsonResponse({
                'success': False,
                'error': '配置已经是停用状态'
            }, status=400)
        
        config.is_active = False
        config.save()
        
        return JsonResponse({
            'success': True,
            'message': '薪资配置已停用'
        })
        
    except EmployeeSalaryConfig.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': '薪资配置不存在'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


def api_get_salary_history(request, employee_id):
    """API: 获取员工薪资调整历史"""
    try:
        # 获取员工对象
        try:
            employee = Personal.objects.get(id=employee_id)
        except Personal.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': '员工不存在'
            }, status=404)
        
        # 获取薪资调整记录
        adjustments = SalaryAdjustment.objects.filter(
            employee=employee
        ).select_related('salary_grade').order_by('-adjustment_date')
        
        history_data = []
        for adjustment in adjustments:
            history_data.append({
                'id': adjustment.id,
                'adjustment_date': adjustment.adjustment_date.strftime('%Y-%m-%d'),
                'adjustment_type': adjustment.adjustment_type,
                'old_salary': str(adjustment.old_salary) if adjustment.old_salary else '无',
                'new_salary': str(adjustment.new_salary),
                'reason': adjustment.reason,
                'status': adjustment.status,
                'created_at': adjustment.created_at.strftime('%Y-%m-%d %H:%M')
            })
        
        return JsonResponse({
            'success': True,
            'data': {
                'employee_name': employee.name,
                'employee_id': employee.employeeId,
                'history': history_data
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


def workflow_diagram(request):
    """工资管理系统流程图"""
    context = {
        'title': '系统流程图'
    }
    return render(request, 'salary_management/workflow.html', context)


@csrf_exempt
@require_http_methods(["POST"])
def api_update_salary_status(request):
    """API: 更新工资状态"""
    try:
        if request.content_type == 'application/json':
            data = json.loads(request.body)
        else:
            data = request.POST.dict()
        salary_id = data.get('salary_id')
        status = data.get('status')
        
        monthly_salary = get_object_or_404(MonthlySalary, id=salary_id)
        monthly_salary.status = status
        
        if status == 'PAID':
            monthly_salary.pay_date = date.today()
        
        monthly_salary.save()
        
        return JsonResponse({
            'success': True,
            'message': '状态更新成功'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@csrf_exempt
@require_http_methods(["POST"])
def api_create_salary_adjustment(request):
    """API: 创建工资调整"""
    try:
        if request.content_type == 'application/json':
            data = json.loads(request.body)
        else:
            data = request.POST.dict()
        
        adjustment, config = SalaryAdjustmentService.create_salary_adjustment(
            employee_id=data.get('employee_id'),
            adjustment_type=data.get('adjustment_type'),
            new_salary=Decimal(str(data.get('new_salary'))),
            effective_date=datetime.strptime(data.get('effective_date'), '%Y-%m-%d').date(),
            reason=data.get('reason', ''),
            approver_id=data.get('approver_id')
        )
        
        return JsonResponse({
            'success': True,
            'data': {
                'adjustment_id': adjustment.id,
                'config_id': config.id,
                'message': '工资调整创建成功'
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


def api_salary_statistics(request):
    """API: 获取工资统计数据"""
    salary_month = request.GET.get('month', date.today().strftime('%Y-%m'))
    
    try:
        month_date = datetime.strptime(salary_month, '%Y-%m').date().replace(day=1)
        
        # 按部门统计
        department_stats = []
        for dept in Department.objects.all():
            records = MonthlySalary.objects.filter(
                employee__station__department=dept,
                salary_month=month_date
            )
            
            if records.exists():
                stats = records.aggregate(
                    count=models.Count('id'),
                    total_gross=models.Sum('gross_salary'),
                    avg_gross=models.Avg('gross_salary')
                )
                department_stats.append({
                    'department': dept.departmentName,
                    'count': stats['count'],
                    'total_gross': float(stats['total_gross'] or 0),
                    'avg_gross': float(stats['avg_gross'] or 0)
                })
        
        return JsonResponse({
            'success': True,
            'data': {
                'department_statistics': department_stats,
                'month': salary_month
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)