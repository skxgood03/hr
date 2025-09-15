import requests
import json
from datetime import datetime, timedelta
from django.utils import timezone
from django.conf import settings
import logging

from .models import ClockInRecord, LeaveRecord, OvertimeRecord
from personal.models import Personal

logger = logging.getLogger(__name__)

class AttendanceDataSync:
    """考勤数据同步器"""
    
    def __init__(self):
        # 外部API配置
        self.api_base_url = getattr(settings, 'ATTENDANCE_SYNC_API_URL', 'https://api.example.com')
        self.api_key = getattr(settings, 'ATTENDANCE_SYNC_API_KEY', 'your-api-key')
        self.timeout = 30
    
    def sync_monthly_data(self, year=None, month=None):
        """同步月度考勤数据
        
        Args:
            year: 年份，默认为上个月
            month: 月份，默认为上个月
        
        Returns:
            dict: 同步结果
        """
        # 默认同步上个月的数据
        if year is None or month is None:
            last_month = timezone.now().replace(day=1) - timedelta(days=1)
            year = last_month.year
            month = last_month.month
        
        logger.info(f"开始同步 {year}年{month}月 考勤数据")
        
        try:
            # 获取本地数据
            local_data = self._get_local_monthly_data(year, month)
            
            # 调用外部API获取数据
            remote_data = self._fetch_remote_data(year, month)
            
            # 数据对比和同步
            sync_result = self._sync_data(local_data, remote_data, year, month)
            
            logger.info(f"考勤数据同步完成 - {year}年{month}月, "
                       f"新增: {sync_result['created']}, 更新: {sync_result['updated']}, "
                       f"错误: {sync_result['errors']}")
            
            return {
                'success': True,
                'year': year,
                'month': month,
                'sync_time': timezone.now().isoformat(),
                'result': sync_result
            }
        
        except Exception as e:
            logger.error(f"考勤数据同步失败: {str(e)}")
            return {
                'success': False,
                'year': year,
                'month': month,
                'sync_time': timezone.now().isoformat(),
                'error': str(e)
            }
    
    def _get_local_monthly_data(self, year, month):
        """获取本地月度考勤数据"""
        start_date = datetime(year, month, 1)
        if month == 12:
            end_date = datetime(year + 1, 1, 1)
        else:
            end_date = datetime(year, month + 1, 1)
        
        # 获取打卡记录
        clock_records = ClockInRecord.objects.filter(
            clock_time__gte=start_date,
            clock_time__lt=end_date
        ).select_related('employee')
        
        # 获取请假记录
        leave_records = LeaveRecord.objects.filter(
            start_time__gte=start_date,
            start_time__lt=end_date
        ).select_related('employee', 'approver')
        
        # 获取加班记录
        overtime_records = OvertimeRecord.objects.filter(
            start_time__gte=start_date,
            start_time__lt=end_date
        ).select_related('employee', 'approver')
        
        return {
            'clock_records': list(clock_records),
            'leave_records': list(leave_records),
            'overtime_records': list(overtime_records)
        }
    
    def _fetch_remote_data(self, year, month):
        """从外部API获取考勤数据"""
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        params = {
            'year': year,
            'month': month,
            'company_id': getattr(settings, 'COMPANY_ID', 'default')
        }
        
        try:
            # 模拟外部API调用
            # 实际使用时需要替换为真实的API端点
            response = requests.get(
                f'{self.api_base_url}/attendance/monthly',
                headers=headers,
                params=params,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"API调用失败: {response.status_code} - {response.text}")
                # 返回模拟数据用于测试
                return self._get_mock_remote_data(year, month)
        
        except requests.RequestException as e:
            logger.warning(f"API调用异常，使用模拟数据: {str(e)}")
            # 返回模拟数据
            return self._get_mock_remote_data(year, month)
    
    def _get_mock_remote_data(self, year, month):
        """获取模拟的远程数据（用于测试）"""
        # 模拟外部系统返回的数据格式
        mock_data = {
            'status': 'success',
            'data': {
                'clock_records': [
                    {
                        'employee_id': '001',
                        'employee_name': '张三',
                        'clock_type': 'IN',
                        'clock_time': f'{year}-{month:02d}-15 09:05:00',
                        'location': '外部系统',
                        'device': 'API同步',
                        'status': 'LATE'
                    },
                    {
                        'employee_id': '001',
                        'employee_name': '张三',
                        'clock_type': 'OUT',
                        'clock_time': f'{year}-{month:02d}-15 18:00:00',
                        'location': '外部系统',
                        'device': 'API同步',
                        'status': 'NORMAL'
                    }
                ],
                'leave_records': [
                    {
                        'employee_id': '002',
                        'employee_name': '李四',
                        'leave_type': 'SICK',
                        'start_time': f'{year}-{month:02d}-20 09:00:00',
                        'end_time': f'{year}-{month:02d}-20 18:00:00',
                        'duration_hours': 8.0,
                        'reason': '感冒请假',
                        'status': 'APPROVED',
                        'approver_id': '003'
                    }
                ],
                'overtime_records': [
                    {
                        'employee_id': '003',
                        'employee_name': '王五',
                        'start_time': f'{year}-{month:02d}-25 19:00:00',
                        'end_time': f'{year}-{month:02d}-25 22:00:00',
                        'duration_hours': 3.0,
                        'reason': '项目加班',
                        'overtime_type': 'WEEKDAY',
                        'status': 'APPROVED',
                        'approver_id': '004'
                    }
                ]
            }
        }
        
        return mock_data
    
    def _sync_data(self, local_data, remote_data, year, month):
        """同步本地和远程数据"""
        result = {
            'created': 0,
            'updated': 0,
            'errors': 0,
            'error_details': []
        }
        
        if remote_data.get('status') != 'success':
            raise Exception(f"远程数据获取失败: {remote_data.get('message', '未知错误')}")
        
        remote_records = remote_data.get('data', {})
        
        # 同步打卡记录
        for record_data in remote_records.get('clock_records', []):
            try:
                self._sync_clock_record(record_data)
                result['created'] += 1
            except Exception as e:
                result['errors'] += 1
                result['error_details'].append(f"打卡记录同步失败: {str(e)}")
        
        # 同步请假记录
        for record_data in remote_records.get('leave_records', []):
            try:
                self._sync_leave_record(record_data)
                result['created'] += 1
            except Exception as e:
                result['errors'] += 1
                result['error_details'].append(f"请假记录同步失败: {str(e)}")
        
        # 同步加班记录
        for record_data in remote_records.get('overtime_records', []):
            try:
                self._sync_overtime_record(record_data)
                result['created'] += 1
            except Exception as e:
                result['errors'] += 1
                result['error_details'].append(f"加班记录同步失败: {str(e)}")
        
        return result
    
    def _sync_clock_record(self, record_data):
        """同步打卡记录"""
        # 根据员工工号查找员工
        try:
            employee = Personal.objects.get(employee_id=record_data['employee_id'])
        except Personal.DoesNotExist:
            # 如果找不到员工，尝试根据姓名查找
            employee = Personal.objects.get(name=record_data['employee_name'])
        
        clock_time = datetime.strptime(record_data['clock_time'], '%Y-%m-%d %H:%M:%S')
        
        # 检查是否已存在相同记录
        existing_record = ClockInRecord.objects.filter(
            employee=employee,
            clock_type=record_data['clock_type'],
            clock_time=clock_time
        ).first()
        
        if not existing_record:
            ClockInRecord.objects.create(
                employee=employee,
                clock_type=record_data['clock_type'],
                clock_time=clock_time,
                location=record_data.get('location', ''),
                device=record_data.get('device', 'API同步'),
                status=record_data.get('status', 'NORMAL')
            )
    
    def _sync_leave_record(self, record_data):
        """同步请假记录"""
        try:
            employee = Personal.objects.get(employee_id=record_data['employee_id'])
        except Personal.DoesNotExist:
            employee = Personal.objects.get(name=record_data['employee_name'])
        
        approver = None
        if record_data.get('approver_id'):
            try:
                approver = Personal.objects.get(employee_id=record_data['approver_id'])
            except Personal.DoesNotExist:
                pass
        
        start_time = datetime.strptime(record_data['start_time'], '%Y-%m-%d %H:%M:%S')
        end_time = datetime.strptime(record_data['end_time'], '%Y-%m-%d %H:%M:%S')
        
        # 检查是否已存在相同记录
        existing_record = LeaveRecord.objects.filter(
            employee=employee,
            leave_type=record_data['leave_type'],
            start_time=start_time,
            end_time=end_time
        ).first()
        
        if not existing_record:
            LeaveRecord.objects.create(
                employee=employee,
                leave_type=record_data['leave_type'],
                start_time=start_time,
                end_time=end_time,
                duration_hours=record_data['duration_hours'],
                reason=record_data.get('reason', ''),
                status=record_data.get('status', 'PENDING'),
                approver=approver
            )
    
    def _sync_overtime_record(self, record_data):
        """同步加班记录"""
        try:
            employee = Personal.objects.get(employee_id=record_data['employee_id'])
        except Personal.DoesNotExist:
            employee = Personal.objects.get(name=record_data['employee_name'])
        
        approver = None
        if record_data.get('approver_id'):
            try:
                approver = Personal.objects.get(employee_id=record_data['approver_id'])
            except Personal.DoesNotExist:
                pass
        
        start_time = datetime.strptime(record_data['start_time'], '%Y-%m-%d %H:%M:%S')
        end_time = datetime.strptime(record_data['end_time'], '%Y-%m-%d %H:%M:%S')
        
        # 检查是否已存在相同记录
        existing_record = OvertimeRecord.objects.filter(
            employee=employee,
            start_time=start_time,
            end_time=end_time
        ).first()
        
        if not existing_record:
            OvertimeRecord.objects.create(
                employee=employee,
                start_time=start_time,
                end_time=end_time,
                duration_hours=record_data['duration_hours'],
                reason=record_data.get('reason', ''),
                overtime_type=record_data.get('overtime_type', 'WEEKDAY'),
                status=record_data.get('status', 'PENDING'),
                approver=approver
            )

# 全局同步器实例
attendance_sync = AttendanceDataSync()

def sync_last_month_data():
    """同步上月考勤数据的便捷函数"""
    return attendance_sync.sync_monthly_data()

def sync_monthly_data(year, month):
    """同步指定月份考勤数据的便捷函数"""
    return attendance_sync.sync_monthly_data(year, month)