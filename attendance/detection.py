from datetime import datetime, time, timedelta
from django.utils import timezone
from django.db.models import Q
import logging

from .models import ClockInRecord, AttendanceRule
from personal.models import Personal

logger = logging.getLogger(__name__)

class AttendanceDetector:
    """考勤异常检测器"""
    
    def __init__(self):
        # 默认工作时间规则
        self.default_work_start = time(9, 0)  # 上班时间 9:00
        self.default_work_end = time(18, 0)   # 下班时间 18:00
        self.late_threshold = 15  # 迟到阈值（分钟）
        self.early_leave_threshold = 30  # 早退阈值（分钟）
    
    def detect_attendance_anomalies(self, date=None):
        """检测考勤异常
        
        Args:
            date: 检测日期，默认为今天
        
        Returns:
            dict: 检测结果
        """
        if date is None:
            date = timezone.now().date()
        
        # 获取当天的打卡记录
        clock_records = ClockInRecord.objects.filter(
            clock_time__date=date
        ).order_by('employee', 'clock_time')
        
        anomalies = {
            'late': [],      # 迟到记录
            'early_leave': [], # 早退记录
            'missing_clock': [], # 缺卡记录
            'duplicate_clock': [] # 重复打卡
        }
        
        # 按员工分组处理
        employee_records = {}
        for record in clock_records:
            emp_id = record.employee.id
            if emp_id not in employee_records:
                employee_records[emp_id] = {
                    'employee': record.employee,
                    'clock_in': [],
                    'clock_out': []
                }
            
            if record.clock_type == 'IN':
                employee_records[emp_id]['clock_in'].append(record)
            else:
                employee_records[emp_id]['clock_out'].append(record)
        
        # 检测每个员工的异常
        for emp_id, records in employee_records.items():
            employee = records['employee']
            clock_in_records = records['clock_in']
            clock_out_records = records['clock_out']
            
            # 获取员工的工作时间规则
            work_start, work_end = self._get_employee_work_time(employee)
            
            # 检测迟到
            if clock_in_records:
                first_clock_in = min(clock_in_records, key=lambda x: x.clock_time)
                if self._is_late(first_clock_in.clock_time.time(), work_start):
                    late_minutes = self._calculate_late_minutes(first_clock_in.clock_time.time(), work_start)
                    anomalies['late'].append({
                        'employee': employee,
                        'record': first_clock_in,
                        'late_minutes': late_minutes,
                        'work_start_time': work_start.strftime('%H:%M')
                    })
                    # 更新记录状态
                    first_clock_in.status = 'LATE'
                    first_clock_in.save()
            else:
                # 缺少上班打卡
                anomalies['missing_clock'].append({
                    'employee': employee,
                    'type': 'clock_in',
                    'date': date
                })
            
            # 检测早退
            if clock_out_records:
                last_clock_out = max(clock_out_records, key=lambda x: x.clock_time)
                if self._is_early_leave(last_clock_out.clock_time.time(), work_end):
                    early_minutes = self._calculate_early_minutes(last_clock_out.clock_time.time(), work_end)
                    anomalies['early_leave'].append({
                        'employee': employee,
                        'record': last_clock_out,
                        'early_minutes': early_minutes,
                        'work_end_time': work_end.strftime('%H:%M')
                    })
                    # 更新记录状态
                    last_clock_out.status = 'EARLY'
                    last_clock_out.save()
            else:
                # 缺少下班打卡
                anomalies['missing_clock'].append({
                    'employee': employee,
                    'type': 'clock_out',
                    'date': date
                })
            
            # 检测重复打卡
            if len(clock_in_records) > 1:
                for record in clock_in_records[1:]:
                    anomalies['duplicate_clock'].append({
                        'employee': employee,
                        'record': record,
                        'type': 'clock_in'
                    })
            
            if len(clock_out_records) > 1:
                for record in clock_out_records[1:]:
                    anomalies['duplicate_clock'].append({
                        'employee': employee,
                        'record': record,
                        'type': 'clock_out'
                    })
        
        return anomalies
    
    def _get_employee_work_time(self, employee):
        """获取员工的工作时间规则"""
        try:
            # 尝试从数据库获取员工的工作时间规则
            # 这里可以扩展为从员工部门或个人设置中获取
            return self.default_work_start, self.default_work_end
        except:
            return self.default_work_start, self.default_work_end
    
    def _is_late(self, clock_time, work_start):
        """判断是否迟到"""
        if clock_time <= work_start:
            return False
        
        # 计算迟到分钟数
        late_minutes = self._calculate_late_minutes(clock_time, work_start)
        return late_minutes > self.late_threshold
    
    def _is_early_leave(self, clock_time, work_end):
        """判断是否早退"""
        if clock_time >= work_end:
            return False
        
        # 计算早退分钟数
        early_minutes = self._calculate_early_minutes(clock_time, work_end)
        return early_minutes > self.early_leave_threshold
    
    def _calculate_late_minutes(self, clock_time, work_start):
        """计算迟到分钟数"""
        clock_datetime = datetime.combine(datetime.today(), clock_time)
        work_start_datetime = datetime.combine(datetime.today(), work_start)
        
        if clock_datetime > work_start_datetime:
            delta = clock_datetime - work_start_datetime
            return int(delta.total_seconds() / 60)
        return 0
    
    def _calculate_early_minutes(self, clock_time, work_end):
        """计算早退分钟数"""
        clock_datetime = datetime.combine(datetime.today(), clock_time)
        work_end_datetime = datetime.combine(datetime.today(), work_end)
        
        if clock_datetime < work_end_datetime:
            delta = work_end_datetime - clock_datetime
            return int(delta.total_seconds() / 60)
        return 0
    
    def generate_daily_report(self, date=None):
        """生成每日考勤异常报告"""
        if date is None:
            date = timezone.now().date()
        
        anomalies = self.detect_attendance_anomalies(date)
        
        report = {
            'date': date.strftime('%Y-%m-%d'),
            'summary': {
                'late_count': len(anomalies['late']),
                'early_leave_count': len(anomalies['early_leave']),
                'missing_clock_count': len(anomalies['missing_clock']),
                'duplicate_clock_count': len(anomalies['duplicate_clock'])
            },
            'details': anomalies
        }
        
        logger.info(f"考勤异常检测完成 - 日期: {date}, 迟到: {report['summary']['late_count']}人, "
                   f"早退: {report['summary']['early_leave_count']}人, "
                   f"缺卡: {report['summary']['missing_clock_count']}人")
        
        return report

# 全局检测器实例
attendance_detector = AttendanceDetector()

def detect_daily_anomalies(date=None):
    """检测每日考勤异常的便捷函数"""
    return attendance_detector.detect_attendance_anomalies(date)

def generate_anomaly_report(date=None):
    """生成考勤异常报告的便捷函数"""
    return attendance_detector.generate_daily_report(date)