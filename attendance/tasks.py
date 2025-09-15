from datetime import datetime, timedelta
from django.utils import timezone
from django.core.management.base import BaseCommand
import logging
import schedule
import time
import threading

from .detection import attendance_detector
from .sync import attendance_sync
from .models import ClockInRecord

logger = logging.getLogger(__name__)

class AttendanceTaskManager:
    """考勤任务管理器"""
    
    def __init__(self):
        self.running = False
        self.scheduler_thread = None
    
    def start_scheduler(self):
        """启动定时任务调度器"""
        if self.running:
            logger.warning("任务调度器已在运行中")
            return
        
        # 配置定时任务
        self._setup_scheduled_tasks()
        
        # 启动调度器线程
        self.running = True
        self.scheduler_thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.scheduler_thread.start()
        
        logger.info("考勤任务调度器已启动")
    
    def stop_scheduler(self):
        """停止定时任务调度器"""
        self.running = False
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
        
        schedule.clear()
        logger.info("考勤任务调度器已停止")
    
    def _setup_scheduled_tasks(self):
        """设置定时任务"""
        # 每天18:30执行考勤异常检测
        schedule.every().day.at("18:30").do(self.daily_anomaly_detection)
        
        # 每月10号02:00执行数据同步
        schedule.every().month.do(self.monthly_data_sync)
        
        # 每天00:01执行前一天的考勤统计
        schedule.every().day.at("00:01").do(self.daily_attendance_summary)
        
        # 每周一08:00生成周报
        schedule.every().monday.at("08:00").do(self.weekly_attendance_report)
        
        logger.info("定时任务配置完成")
    
    def _run_scheduler(self):
        """运行调度器"""
        while self.running:
            try:
                schedule.run_pending()
                time.sleep(60)  # 每分钟检查一次
            except Exception as e:
                logger.error(f"调度器运行异常: {str(e)}")
                time.sleep(60)
    
    def daily_anomaly_detection(self):
        """每日考勤异常检测任务"""
        try:
            logger.info("开始执行每日考勤异常检测")
            
            # 检测今天的考勤异常
            today = timezone.now().date()
            report = attendance_detector.generate_daily_report(today)
            
            # 记录检测结果
            self._log_anomaly_report(report)
            
            # 可以在这里添加邮件通知或其他处理逻辑
            if report['summary']['late_count'] > 0 or report['summary']['early_leave_count'] > 0:
                self._send_anomaly_notification(report)
            
            logger.info(f"每日考勤异常检测完成 - 迟到: {report['summary']['late_count']}人, "
                       f"早退: {report['summary']['early_leave_count']}人")
        
        except Exception as e:
            logger.error(f"每日考勤异常检测失败: {str(e)}")
    
    def monthly_data_sync(self):
        """月度数据同步任务"""
        try:
            # 检查是否为每月10号
            today = timezone.now().date()
            if today.day != 10:
                return
            
            logger.info("开始执行月度考勤数据同步")
            
            # 同步上个月的数据
            result = attendance_sync.sync_monthly_data()
            
            if result['success']:
                logger.info(f"月度数据同步成功 - {result['year']}年{result['month']}月, "
                           f"新增: {result['result']['created']}, 更新: {result['result']['updated']}")
            else:
                logger.error(f"月度数据同步失败: {result['error']}")
                # 发送失败通知
                self._send_sync_failure_notification(result)
        
        except Exception as e:
            logger.error(f"月度数据同步任务失败: {str(e)}")
    
    def daily_attendance_summary(self):
        """每日考勤统计任务"""
        try:
            logger.info("开始生成每日考勤统计")
            
            # 统计昨天的考勤数据
            yesterday = timezone.now().date() - timedelta(days=1)
            
            # 获取昨天的打卡记录
            clock_records = ClockInRecord.objects.filter(
                clock_time__date=yesterday
            )
            
            # 统计各种状态的记录数
            summary = {
                'date': yesterday.strftime('%Y-%m-%d'),
                'total_records': clock_records.count(),
                'normal_count': clock_records.filter(status='NORMAL').count(),
                'late_count': clock_records.filter(status='LATE').count(),
                'early_count': clock_records.filter(status='EARLY').count(),
                'absent_count': clock_records.filter(status='ABSENT').count()
            }
            
            logger.info(f"每日考勤统计完成 - {summary['date']}: "
                       f"总计{summary['total_records']}条, 正常{summary['normal_count']}条, "
                       f"迟到{summary['late_count']}条, 早退{summary['early_count']}条")
            
            return summary
        
        except Exception as e:
            logger.error(f"每日考勤统计失败: {str(e)}")
    
    def weekly_attendance_report(self):
        """周度考勤报告任务"""
        try:
            logger.info("开始生成周度考勤报告")
            
            # 计算上周的日期范围
            today = timezone.now().date()
            last_monday = today - timedelta(days=today.weekday() + 7)
            last_sunday = last_monday + timedelta(days=6)
            
            # 获取上周的打卡记录
            weekly_records = ClockInRecord.objects.filter(
                clock_time__date__gte=last_monday,
                clock_time__date__lte=last_sunday
            )
            
            # 生成周报统计
            weekly_summary = {
                'week_start': last_monday.strftime('%Y-%m-%d'),
                'week_end': last_sunday.strftime('%Y-%m-%d'),
                'total_records': weekly_records.count(),
                'normal_count': weekly_records.filter(status='NORMAL').count(),
                'late_count': weekly_records.filter(status='LATE').count(),
                'early_count': weekly_records.filter(status='EARLY').count(),
                'absent_count': weekly_records.filter(status='ABSENT').count()
            }
            
            logger.info(f"周度考勤报告完成 - {weekly_summary['week_start']} 至 {weekly_summary['week_end']}: "
                       f"总计{weekly_summary['total_records']}条记录")
            
            return weekly_summary
        
        except Exception as e:
            logger.error(f"周度考勤报告生成失败: {str(e)}")
    
    def _log_anomaly_report(self, report):
        """记录异常检测报告"""
        # 这里可以将报告保存到数据库或文件
        logger.info(f"考勤异常报告 - {report['date']}: {report['summary']}")
    
    def _send_anomaly_notification(self, report):
        """发送异常通知"""
        # 这里可以实现邮件、短信或其他通知方式
        logger.info(f"发送考勤异常通知 - {report['date']}: "
                   f"迟到{report['summary']['late_count']}人, "
                   f"早退{report['summary']['early_leave_count']}人")
    
    def _send_sync_failure_notification(self, result):
        """发送同步失败通知"""
        logger.error(f"数据同步失败通知 - {result['year']}年{result['month']}月: {result['error']}")
    
    def run_manual_detection(self, date=None):
        """手动执行考勤异常检测"""
        if date is None:
            date = timezone.now().date()
        
        logger.info(f"手动执行考勤异常检测 - {date}")
        return attendance_detector.generate_daily_report(date)
    
    def run_manual_sync(self, year=None, month=None):
        """手动执行数据同步"""
        logger.info(f"手动执行数据同步 - {year}年{month}月")
        return attendance_sync.sync_monthly_data(year, month)

# 全局任务管理器实例
task_manager = AttendanceTaskManager()

# 便捷函数
def start_attendance_scheduler():
    """启动考勤任务调度器"""
    task_manager.start_scheduler()

def stop_attendance_scheduler():
    """停止考勤任务调度器"""
    task_manager.stop_scheduler()

def manual_anomaly_detection(date=None):
    """手动执行异常检测"""
    return task_manager.run_manual_detection(date)

def manual_data_sync(year=None, month=None):
    """手动执行数据同步"""
    return task_manager.run_manual_sync(year, month)