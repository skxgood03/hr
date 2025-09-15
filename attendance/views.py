from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone
from datetime import datetime, timedelta
import json
import logging

from .models import ClockInRecord, LeaveRecord, OvertimeRecord
from personal.models import Personal
from hr.decorators import login_required, employee_required, admin_required

logger = logging.getLogger(__name__)

# 员工考勤查询视图
@login_required
@employee_required
def employee_attendance_view(request):
    """员工个人考勤数据查询界面"""
    return render(request, 'attendance/employee_attendance.html')

# 管理员考勤管理视图
@login_required
@admin_required
def admin_attendance_view(request):
    """管理员考勤数据管理界面"""
    return render(request, 'attendance/admin_attendance.html')

# API接口
@csrf_exempt
@require_http_methods(["GET"])
@login_required
def get_attendance_records(request):
    """获取考勤记录API"""
    try:
        # 获取查询参数
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 10))
        record_type = request.GET.get('type', 'clock')  # clock, leave, overtime
        employee_id = request.GET.get('employee_id')
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        status = request.GET.get('status')
        
        # 权限检查
        user_role = request.session.get('user_role')
        if user_role == 'EMPLOYEE':
            # 员工只能查看自己的记录
            employee_id = request.session.get('employee_id')
            if not employee_id:
                return JsonResponse({'code': 4003, 'message': '员工信息不存在'})
        
        # 根据记录类型查询
        if record_type == 'clock':
            queryset = ClockInRecord.objects.all()
        elif record_type == 'leave':
            queryset = LeaveRecord.objects.all()
        elif record_type == 'overtime':
            queryset = OvertimeRecord.objects.all()
        else:
            return JsonResponse({'code': 4000, 'message': '无效的记录类型'})
        
        # 筛选条件
        if employee_id:
            queryset = queryset.filter(employee_id=employee_id)
        
        if start_date:
            start_datetime = datetime.strptime(start_date, '%Y-%m-%d')
            if record_type == 'clock':
                queryset = queryset.filter(clock_time__gte=start_datetime)
            else:
                queryset = queryset.filter(start_time__gte=start_datetime)
        
        if end_date:
            end_datetime = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
            if record_type == 'clock':
                queryset = queryset.filter(clock_time__lt=end_datetime)
            else:
                queryset = queryset.filter(start_time__lt=end_datetime)
        
        if status:
            queryset = queryset.filter(status=status)
        
        # 排序
        if record_type == 'clock':
            queryset = queryset.order_by('-clock_time')
        else:
            queryset = queryset.order_by('-created_at')
        
        # 分页
        paginator = Paginator(queryset, page_size)
        page_obj = paginator.get_page(page)
        
        # 序列化数据
        records = []
        for record in page_obj:
            if record_type == 'clock':
                records.append({
                    'id': record.id,
                    'employee_name': record.employee.name,
                    'employee_id': record.employee.id,
                    'clock_type': record.clock_type,
                    'clock_type_display': record.get_clock_type_display(),
                    'clock_time': record.clock_time.strftime('%Y-%m-%d %H:%M:%S'),
                    'location': record.location,
                    'device': record.device,
                    'status': record.status,
                    'status_display': record.get_status_display(),
                    'created_at': record.created_at.strftime('%Y-%m-%d %H:%M:%S')
                })
            elif record_type == 'leave':
                records.append({
                    'id': record.id,
                    'employee_name': record.employee.name,
                    'employee_id': record.employee.id,
                    'leave_type': record.leave_type,
                    'leave_type_display': record.get_leave_type_display(),
                    'start_time': record.start_time.strftime('%Y-%m-%d %H:%M:%S'),
                    'end_time': record.end_time.strftime('%Y-%m-%d %H:%M:%S'),
                    'duration_hours': str(record.duration_hours),
                    'reason': record.reason,
                    'status': record.status,
                    'status_display': record.get_status_display(),
                    'approver_name': record.approver.name if record.approver else '',
                    'approved_at': record.approved_at.strftime('%Y-%m-%d %H:%M:%S') if record.approved_at else '',
                    'created_at': record.created_at.strftime('%Y-%m-%d %H:%M:%S')
                })
            elif record_type == 'overtime':
                records.append({
                    'id': record.id,
                    'employee_name': record.employee.name,
                    'employee_id': record.employee.id,
                    'start_time': record.start_time.strftime('%Y-%m-%d %H:%M:%S'),
                    'end_time': record.end_time.strftime('%Y-%m-%d %H:%M:%S'),
                    'duration_hours': str(record.duration_hours),
                    'reason': record.reason,
                    'overtime_type': record.overtime_type,
                    'overtime_type_display': record.get_overtime_type_display(),
                    'status': record.status,
                    'status_display': record.get_status_display(),
                    'approver_name': record.approver.name if record.approver else '',
                    'approved_at': record.approved_at.strftime('%Y-%m-%d %H:%M:%S') if record.approved_at else '',
                    'created_at': record.created_at.strftime('%Y-%m-%d %H:%M:%S')
                })
        
        return JsonResponse({
            'code': 2000,
            'message': '查询成功',
            'data': {
                'records': records,
                'pagination': {
                    'current_page': page,
                    'total_pages': paginator.num_pages,
                    'total_count': paginator.count,
                    'page_size': page_size,
                    'has_next': page_obj.has_next(),
                    'has_previous': page_obj.has_previous()
                }
            }
        })
    
    except Exception as e:
        logger.error(f"获取考勤记录失败: {str(e)}")
        return JsonResponse({'code': 5000, 'message': f'服务器错误: {str(e)}'})

@csrf_exempt
@require_http_methods(["POST"])
@login_required
@admin_required
def import_attendance_records(request):
    """批量导入考勤记录API"""
    try:
        data = json.loads(request.body)
        records = data.get('records', [])
        record_type = data.get('type', 'clock')
        
        if not records:
            return JsonResponse({'code': 4000, 'message': '导入数据不能为空'})
        
        success_count = 0
        error_list = []
        
        for i, record_data in enumerate(records):
            try:
                if record_type == 'clock':
                    # 导入打卡记录
                    employee = Personal.objects.get(id=record_data['employee_id'])
                    ClockInRecord.objects.create(
                        employee=employee,
                        clock_type=record_data['clock_type'],
                        clock_time=datetime.strptime(record_data['clock_time'], '%Y-%m-%d %H:%M:%S'),
                        location=record_data.get('location', ''),
                        device=record_data.get('device', '导入数据'),
                        status=record_data.get('status', 'NORMAL')
                    )
                elif record_type == 'leave':
                    # 导入请假记录
                    employee = Personal.objects.get(id=record_data['employee_id'])
                    approver = None
                    if record_data.get('approver_id'):
                        approver = Personal.objects.get(id=record_data['approver_id'])
                    
                    LeaveRecord.objects.create(
                        employee=employee,
                        leave_type=record_data['leave_type'],
                        start_time=datetime.strptime(record_data['start_time'], '%Y-%m-%d %H:%M:%S'),
                        end_time=datetime.strptime(record_data['end_time'], '%Y-%m-%d %H:%M:%S'),
                        duration_hours=record_data['duration_hours'],
                        reason=record_data.get('reason', ''),
                        status=record_data.get('status', 'PENDING'),
                        approver=approver,
                        approved_at=datetime.strptime(record_data['approved_at'], '%Y-%m-%d %H:%M:%S') if record_data.get('approved_at') else None
                    )
                elif record_type == 'overtime':
                    # 导入加班记录
                    employee = Personal.objects.get(id=record_data['employee_id'])
                    approver = None
                    if record_data.get('approver_id'):
                        approver = Personal.objects.get(id=record_data['approver_id'])
                    
                    OvertimeRecord.objects.create(
                        employee=employee,
                        start_time=datetime.strptime(record_data['start_time'], '%Y-%m-%d %H:%M:%S'),
                        end_time=datetime.strptime(record_data['end_time'], '%Y-%m-%d %H:%M:%S'),
                        duration_hours=record_data['duration_hours'],
                        reason=record_data.get('reason', ''),
                        overtime_type=record_data.get('overtime_type', 'WEEKDAY'),
                        status=record_data.get('status', 'PENDING'),
                        approver=approver,
                        approved_at=datetime.strptime(record_data['approved_at'], '%Y-%m-%d %H:%M:%S') if record_data.get('approved_at') else None
                    )
                
                success_count += 1
            
            except Exception as e:
                error_list.append(f"第{i+1}条记录导入失败: {str(e)}")
        
        return JsonResponse({
            'code': 2000,
            'message': f'导入完成，成功{success_count}条',
            'data': {
                'success_count': success_count,
                'error_count': len(error_list),
                'errors': error_list
            }
        })
    
    except Exception as e:
        logger.error(f"批量导入考勤记录失败: {str(e)}")
        return JsonResponse({'code': 5000, 'message': f'服务器错误: {str(e)}'})

# 异常检测API
@csrf_exempt
@require_http_methods(["GET"])
@login_required
@admin_required
def daily_anomaly_detection_api(request):
    """每日考勤异常检测API"""
    try:
        from .detection import attendance_detector
        
        date_str = request.GET.get('date')
        if date_str:
            date = datetime.strptime(date_str, '%Y-%m-%d').date()
        else:
            date = timezone.now().date()
        
        report = attendance_detector.generate_daily_report(date)
        
        return JsonResponse({
            'code': 2000,
            'message': '异常检测完成',
            'data': report
        })
    
    except Exception as e:
        logger.error(f"考勤异常检测失败: {str(e)}")
        return JsonResponse({'code': 5000, 'message': f'服务器错误: {str(e)}'})

@csrf_exempt
@require_http_methods(["POST"])
@login_required
@admin_required
def manual_anomaly_detection_api(request):
    """手动考勤异常检测API"""
    try:
        from .tasks import task_manager
        
        data = json.loads(request.body)
        date_str = data.get('date')
        
        if date_str:
            date = datetime.strptime(date_str, '%Y-%m-%d').date()
        else:
            date = None
        
        report = task_manager.run_manual_detection(date)
        
        return JsonResponse({
            'code': 2000,
            'message': '手动异常检测完成',
            'data': report
        })
    
    except Exception as e:
        logger.error(f"手动考勤异常检测失败: {str(e)}")
        return JsonResponse({'code': 5000, 'message': f'服务器错误: {str(e)}'})

# 数据同步API
@csrf_exempt
@require_http_methods(["GET"])
@login_required
@admin_required
def monthly_sync_api(request):
    """月度数据同步API"""
    try:
        from .sync import attendance_sync
        
        year = request.GET.get('year')
        month = request.GET.get('month')
        
        if year and month:
            result = attendance_sync.sync_monthly_data(int(year), int(month))
        else:
            result = attendance_sync.sync_monthly_data()
        
        return JsonResponse({
            'code': 2000,
            'message': '数据同步完成',
            'data': result
        })
    
    except Exception as e:
        logger.error(f"月度数据同步失败: {str(e)}")
        return JsonResponse({'code': 5000, 'message': f'服务器错误: {str(e)}'})

@csrf_exempt
@require_http_methods(["POST"])
@login_required
@admin_required
def manual_sync_api(request):
    """手动数据同步API"""
    try:
        from .tasks import task_manager
        
        data = json.loads(request.body)
        year = data.get('year')
        month = data.get('month')
        
        result = task_manager.run_manual_sync(year, month)
        
        return JsonResponse({
            'code': 2000,
            'message': '手动数据同步完成',
            'data': result
        })
    
    except Exception as e:
        logger.error(f"手动数据同步失败: {str(e)}")
        return JsonResponse({'code': 5000, 'message': f'服务器错误: {str(e)}'})

# 统计报告API
@csrf_exempt
@require_http_methods(["GET"])
@login_required
@admin_required
def daily_report_api(request):
    """每日考勤报告API"""
    try:
        date_str = request.GET.get('date')
        if date_str:
            date = datetime.strptime(date_str, '%Y-%m-%d').date()
        else:
            date = timezone.now().date() - timedelta(days=1)  # 默认昨天
        
        # 获取当天的打卡记录统计
        clock_records = ClockInRecord.objects.filter(clock_time__date=date)
        
        summary = {
            'date': date.strftime('%Y-%m-%d'),
            'total_records': clock_records.count(),
            'normal_count': clock_records.filter(status='NORMAL').count(),
            'late_count': clock_records.filter(status='LATE').count(),
            'early_count': clock_records.filter(status='EARLY').count(),
            'absent_count': clock_records.filter(status='ABSENT').count()
        }
        
        return JsonResponse({
            'code': 2000,
            'message': '每日报告生成成功',
            'data': summary
        })
    
    except Exception as e:
        logger.error(f"每日报告生成失败: {str(e)}")
        return JsonResponse({'code': 5000, 'message': f'服务器错误: {str(e)}'})

@csrf_exempt
@require_http_methods(["GET"])
@login_required
@admin_required
def weekly_report_api(request):
    """周度考勤报告API"""
    try:
        # 计算指定周或上周的日期范围
        week_start_str = request.GET.get('week_start')
        if week_start_str:
            week_start = datetime.strptime(week_start_str, '%Y-%m-%d').date()
        else:
            # 默认上周
            today = timezone.now().date()
            week_start = today - timedelta(days=today.weekday() + 7)
        
        week_end = week_start + timedelta(days=6)
        
        # 获取周内的打卡记录
        weekly_records = ClockInRecord.objects.filter(
            clock_time__date__gte=week_start,
            clock_time__date__lte=week_end
        )
        
        summary = {
            'week_start': week_start.strftime('%Y-%m-%d'),
            'week_end': week_end.strftime('%Y-%m-%d'),
            'total_records': weekly_records.count(),
            'normal_count': weekly_records.filter(status='NORMAL').count(),
            'late_count': weekly_records.filter(status='LATE').count(),
            'early_count': weekly_records.filter(status='EARLY').count(),
            'absent_count': weekly_records.filter(status='ABSENT').count()
        }
        
        return JsonResponse({
            'code': 2000,
            'message': '周度报告生成成功',
            'data': summary
        })
    
    except Exception as e:
        logger.error(f"周度报告生成失败: {str(e)}")
        return JsonResponse({'code': 5000, 'message': f'服务器错误: {str(e)}'})

@csrf_exempt
@require_http_methods(["GET"])
@login_required
@admin_required
def monthly_report_api(request):
    """月度考勤报告API"""
    try:
        year = request.GET.get('year')
        month = request.GET.get('month')
        
        if year and month:
            year = int(year)
            month = int(month)
        else:
            # 默认上个月
            last_month = timezone.now().replace(day=1) - timedelta(days=1)
            year = last_month.year
            month = last_month.month
        
        # 计算月份的日期范围
        start_date = datetime(year, month, 1)
        if month == 12:
            end_date = datetime(year + 1, 1, 1)
        else:
            end_date = datetime(year, month + 1, 1)
        
        # 获取月内的各类记录
        clock_records = ClockInRecord.objects.filter(
            clock_time__gte=start_date,
            clock_time__lt=end_date
        )
        
        leave_records = LeaveRecord.objects.filter(
            start_time__gte=start_date,
            start_time__lt=end_date
        )
        
        overtime_records = OvertimeRecord.objects.filter(
            start_time__gte=start_date,
            start_time__lt=end_date
        )
        
        summary = {
            'year': year,
            'month': month,
            'clock_summary': {
                'total_records': clock_records.count(),
                'normal_count': clock_records.filter(status='NORMAL').count(),
                'late_count': clock_records.filter(status='LATE').count(),
                'early_count': clock_records.filter(status='EARLY').count(),
                'absent_count': clock_records.filter(status='ABSENT').count()
            },
            'leave_summary': {
                'total_records': leave_records.count(),
                'approved_count': leave_records.filter(status='APPROVED').count(),
                'pending_count': leave_records.filter(status='PENDING').count(),
                'rejected_count': leave_records.filter(status='REJECTED').count()
            },
            'overtime_summary': {
                'total_records': overtime_records.count(),
                'approved_count': overtime_records.filter(status='APPROVED').count(),
                'pending_count': overtime_records.filter(status='PENDING').count(),
                'rejected_count': overtime_records.filter(status='REJECTED').count()
            }
        }
        
        return JsonResponse({
            'code': 2000,
            'message': '月度报告生成成功',
            'data': summary
        })
    
    except Exception as e:
        logger.error(f"月度报告生成失败: {str(e)}")
        return JsonResponse({'code': 5000, 'message': f'服务器错误: {str(e)}'})

@csrf_exempt
@require_http_methods(["GET"])
@login_required
def daily_statistics_api(request):
    """获取每日统计数据API"""
    try:
        # 获取日期参数
        date_str = request.GET.get('date')
        if not date_str:
            target_date = timezone.now().date()
        else:
            target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        
        # 获取当日打卡记录统计
        clock_in_count = ClockInRecord.objects.filter(
            clock_time__date=target_date
        ).count()
        
        # 获取当日请假记录统计
        leave_count = LeaveRecord.objects.filter(
            start_time__date__lte=target_date,
            end_time__date__gte=target_date,
            status='APPROVED'
        ).count()
        
        # 获取当日加班记录统计
        overtime_count = OvertimeRecord.objects.filter(
            start_time__date=target_date,
            status='APPROVED'
        ).count()
        
        # 计算迟到次数（假设9:00为标准上班时间）
        late_count = ClockInRecord.objects.filter(
            clock_time__date=target_date,
            clock_time__time__gt='09:00:00'
        ).count()
        
        return JsonResponse({
            'code': 2000,
            'message': '获取统计数据成功',
            'data': {
                'date': target_date.strftime('%Y-%m-%d'),
                'clock_in_count': clock_in_count,
                'leave_count': leave_count,
                'overtime_count': overtime_count,
                'late_count': late_count
            }
        })
    
    except Exception as e:
        logger.error(f"获取每日统计数据失败: {str(e)}")
        return JsonResponse({
            'code': 5000,
            'message': f'获取统计数据失败: {str(e)}'
        })
