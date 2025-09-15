# 人事公司工资管理系统 - 代码生成规范

## Python Web开发规范

### 1. Django项目结构规范

#### 1.1 应用目录结构
```
salary_management/
├── __init__.py
├── admin.py              # Django管理后台配置
├── apps.py               # 应用配置
├── models.py             # 数据模型定义
├── views.py              # 视图函数/类
├── urls.py               # URL路由配置
├── serializers.py        # DRF序列化器（如需要API）
├── forms.py              # Django表单定义
├── services.py           # 业务逻辑服务层
├── utils.py              # 工具函数
├── constants.py          # 常量定义
├── validators.py         # 自定义验证器
├── managers.py           # 自定义模型管理器
├── signals.py            # Django信号处理
├── tests/                # 测试文件目录
│   ├── __init__.py
│   ├── test_models.py
│   ├── test_views.py
│   └── test_services.py
├── migrations/           # 数据库迁移文件
├── templates/            # 模板文件
│   └── salary_management/
│       ├── base.html
│       ├── list.html
│       ├── detail.html
│       └── form.html
└── static/               # 静态文件
    └── salary_management/
        ├── css/
        ├── js/
        └── images/
```

### 2. 代码编写规范

#### 2.1 命名规范

```python
# 类名：使用PascalCase（大驼峰）
class SalaryCalculationService:
    pass

class MonthlySalaryRecord:
    pass

# 函数名和变量名：使用snake_case（下划线）
def calculate_monthly_salary(employee_id, salary_month):
    basic_salary = 0
    performance_bonus = 0
    return basic_salary + performance_bonus

# 常量：使用UPPER_CASE（全大写）
SALARY_STATUS_DRAFT = 'DRAFT'
SALARY_STATUS_APPROVED = 'APPROVED'
SALARY_STATUS_PAID = 'PAID'

# 私有方法：使用单下划线前缀
def _calculate_tax(gross_salary):
    pass

# 特殊方法：使用双下划线
def __calculate_internal_rate():
    pass
```

#### 2.2 模型定义规范

```python
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from decimal import Decimal

class SalaryGrade(models.Model):
    """薪资等级模型
    
    用于定义公司的薪资等级体系，包括等级名称、薪资范围等信息。
    每个等级对应一个薪资区间，用于员工薪资配置的参考标准。
    """
    
    # 字段定义：按照逻辑顺序排列
    grade_name = models.CharField(
        max_length=50, 
        unique=True,
        verbose_name='等级名称',
        help_text='薪资等级的名称，如：初级、中级、高级等'
    )
    min_salary = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name='最低薪资',
        help_text='该等级的最低薪资标准'
    )
    max_salary = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name='最高薪资',
        help_text='该等级的最高薪资标准'
    )
    description = models.TextField(
        blank=True, 
        null=True,
        verbose_name='描述',
        help_text='等级的详细描述信息'
    )
    
    # 状态字段
    is_active = models.BooleanField(
        default=True,
        verbose_name='是否启用',
        help_text='是否启用该薪资等级'
    )
    
    # 时间戳字段：放在最后
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='创建时间'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='更新时间'
    )
    
    class Meta:
        db_table = 't_salary_grade'
        verbose_name = '薪资等级'
        verbose_name_plural = '薪资等级'
        ordering = ['min_salary']  # 默认按最低薪资排序
        indexes = [
            models.Index(fields=['is_active']),
            models.Index(fields=['min_salary', 'max_salary']),
        ]
    
    def __str__(self):
        return f'{self.grade_name}({self.min_salary}-{self.max_salary})'
    
    def clean(self):
        """模型验证"""
        from django.core.exceptions import ValidationError
        if self.min_salary and self.max_salary and self.min_salary >= self.max_salary:
            raise ValidationError('最低薪资必须小于最高薪资')
    
    def save(self, *args, **kwargs):
        """保存前验证"""
        self.full_clean()
        super().save(*args, **kwargs)
    
    @property
    def salary_range(self):
        """薪资区间字符串"""
        return f'{self.min_salary}-{self.max_salary}'
    
    @classmethod
    def get_active_grades(cls):
        """获取所有启用的薪资等级"""
        return cls.objects.filter(is_active=True)
```

#### 2.3 视图函数规范

```python
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator
from django.db import transaction
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views.generic import ListView, DetailView, CreateView, UpdateView
import json
import logging

logger = logging.getLogger(__name__)

@login_required
@require_http_methods(["GET", "POST"])
def salary_grade_list(request):
    """薪资等级列表视图
    
    GET: 显示薪资等级列表页面
    POST: 处理新增薪资等级请求
    
    Args:
        request: HTTP请求对象
        
    Returns:
        HttpResponse: 渲染后的页面或重定向响应
    """
    try:
        if request.method == 'GET':
            # 获取查询参数
            search_query = request.GET.get('search', '').strip()
            is_active = request.GET.get('is_active', '')
            
            # 构建查询条件
            queryset = SalaryGrade.objects.all()
            
            if search_query:
                queryset = queryset.filter(
                    models.Q(grade_name__icontains=search_query) |
                    models.Q(description__icontains=search_query)
                )
            
            if is_active:
                queryset = queryset.filter(is_active=is_active == 'true')
            
            # 分页处理
            paginator = Paginator(queryset, 20)  # 每页20条记录
            page_number = request.GET.get('page')
            page_obj = paginator.get_page(page_number)
            
            context = {
                'page_obj': page_obj,
                'search_query': search_query,
                'is_active': is_active,
                'total_count': queryset.count(),
            }
            
            return render(request, 'salary_management/grade_list.html', context)
            
        elif request.method == 'POST':
            # 处理新增请求
            form = SalaryGradeForm(request.POST)
            if form.is_valid():
                try:
                    with transaction.atomic():
                        salary_grade = form.save()
                        messages.success(request, f'薪资等级 "{salary_grade.grade_name}" 创建成功')
                        logger.info(f'用户 {request.user.username} 创建了薪资等级: {salary_grade.grade_name}')
                        return redirect('salary_management:grade_list')
                except Exception as e:
                    logger.error(f'创建薪资等级失败: {str(e)}')
                    messages.error(request, '创建失败，请重试')
            else:
                messages.error(request, '表单验证失败，请检查输入')
            
            return redirect('salary_management:grade_list')
            
    except Exception as e:
        logger.error(f'薪资等级列表视图异常: {str(e)}')
        messages.error(request, '系统异常，请联系管理员')
        return redirect('home')


class SalaryGradeListView(ListView):
    """薪资等级列表类视图
    
    使用Django通用视图实现薪资等级的列表展示功能
    """
    model = SalaryGrade
    template_name = 'salary_management/grade_list.html'
    context_object_name = 'salary_grades'
    paginate_by = 20
    
    def get_queryset(self):
        """自定义查询集"""
        queryset = super().get_queryset()
        
        # 搜索功能
        search_query = self.request.GET.get('search')
        if search_query:
            queryset = queryset.filter(
                models.Q(grade_name__icontains=search_query) |
                models.Q(description__icontains=search_query)
            )
        
        # 状态筛选
        is_active = self.request.GET.get('is_active')
        if is_active:
            queryset = queryset.filter(is_active=is_active == 'true')
            
        return queryset.order_by('min_salary')
    
    def get_context_data(self, **kwargs):
        """添加额外的上下文数据"""
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('search', '')
        context['is_active'] = self.request.GET.get('is_active', '')
        context['total_count'] = self.get_queryset().count()
        return context


@login_required
@require_http_methods(["POST"])
@csrf_exempt
def ajax_calculate_salary(request):
    """AJAX工资计算接口
    
    接收前端传递的员工ID和月份，计算并返回工资详情
    
    Args:
        request: HTTP请求对象
        
    Returns:
        JsonResponse: JSON格式的响应数据
    """
    try:
        # 解析请求数据
        data = json.loads(request.body)
        employee_id = data.get('employee_id')
        salary_month = data.get('salary_month')
        
        # 参数验证
        if not employee_id or not salary_month:
            return JsonResponse({
                'success': False,
                'message': '参数不完整'
            }, status=400)
        
        # 调用业务服务
        from .services import SalaryCalculationService
        service = SalaryCalculationService()
        result = service.calculate_monthly_salary(employee_id, salary_month)
        
        return JsonResponse({
            'success': True,
            'data': result,
            'message': '计算成功'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': '请求数据格式错误'
        }, status=400)
    except Exception as e:
        logger.error(f'AJAX工资计算异常: {str(e)}')
        return JsonResponse({
            'success': False,
            'message': '计算失败，请重试'
        }, status=500)
```

#### 2.4 服务层规范

```python
from decimal import Decimal, ROUND_HALF_UP
from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

class SalaryCalculationService:
    """工资计算服务类
    
    负责处理所有与工资计算相关的业务逻辑，包括：
    - 基本工资计算
    - 绩效工资计算
    - 各项扣除计算
    - 实发工资计算
    """
    
    # 个税起征点（2024年标准）
    TAX_THRESHOLD = Decimal('5000.00')
    
    # 社保费率配置
    SOCIAL_INSURANCE_RATES = {
        'pension': Decimal('0.08'),      # 养老保险 8%
        'medical': Decimal('0.02'),      # 医疗保险 2%
        'unemployment': Decimal('0.005'), # 失业保险 0.5%
    }
    
    # 公积金费率
    HOUSING_FUND_RATE = Decimal('0.12')  # 12%
    
    def __init__(self):
        """初始化服务"""
        self.logger = logging.getLogger(self.__class__.__name__)
    
    @transaction.atomic
    def calculate_monthly_salary(self, employee_id: int, salary_month: str) -> Dict:
        """计算员工月度工资
        
        Args:
            employee_id: 员工ID
            salary_month: 工资月份，格式：YYYY-MM
            
        Returns:
            Dict: 工资计算结果
            
        Raises:
            ValidationError: 参数验证失败
            ValueError: 数据异常
        """
        try:
            # 参数验证
            self._validate_calculation_params(employee_id, salary_month)
            
            # 获取员工信息
            employee = self._get_employee_info(employee_id)
            
            # 获取薪资配置
            salary_config = self._get_salary_config(employee_id, salary_month)
            
            # 计算各项工资组成
            basic_salary = salary_config.basic_salary
            performance_salary = self._calculate_performance_salary(employee_id, salary_month)
            allowance = salary_config.allowance
            bonus = self._calculate_bonus(employee_id, salary_month)
            overtime_pay = self._calculate_overtime_pay(employee_id, salary_month)
            
            # 计算应发工资
            gross_salary = basic_salary + performance_salary + allowance + bonus + overtime_pay
            
            # 计算各项扣除
            social_insurance = self._calculate_social_insurance(basic_salary)
            housing_fund = self._calculate_housing_fund(basic_salary)
            income_tax = self._calculate_income_tax(gross_salary - social_insurance - housing_fund)
            
            # 计算实发工资
            total_deduction = social_insurance + housing_fund + income_tax
            net_salary = gross_salary - total_deduction
            
            # 构建结果
            result = {
                'employee_id': employee_id,
                'employee_name': employee.name,
                'salary_month': salary_month,
                'basic_salary': float(basic_salary),
                'performance_salary': float(performance_salary),
                'allowance': float(allowance),
                'bonus': float(bonus),
                'overtime_pay': float(overtime_pay),
                'gross_salary': float(gross_salary),
                'social_insurance': float(social_insurance),
                'housing_fund': float(housing_fund),
                'income_tax': float(income_tax),
                'total_deduction': float(total_deduction),
                'net_salary': float(net_salary),
                'calculated_at': timezone.now().isoformat()
            }
            
            self.logger.info(f'员工 {employee.name} {salary_month} 工资计算完成')
            return result
            
        except Exception as e:
            self.logger.error(f'工资计算失败: employee_id={employee_id}, month={salary_month}, error={str(e)}')
            raise
    
    def _validate_calculation_params(self, employee_id: int, salary_month: str) -> None:
        """验证计算参数
        
        Args:
            employee_id: 员工ID
            salary_month: 工资月份
            
        Raises:
            ValidationError: 参数验证失败
        """
        if not employee_id or employee_id <= 0:
            raise ValidationError('员工ID无效')
        
        if not salary_month:
            raise ValidationError('工资月份不能为空')
        
        # 验证月份格式
        try:
            from datetime import datetime
            datetime.strptime(salary_month, '%Y-%m')
        except ValueError:
            raise ValidationError('工资月份格式错误，应为YYYY-MM')
    
    def _calculate_income_tax(self, taxable_income: Decimal) -> Decimal:
        """计算个人所得税
        
        使用2024年个税税率表计算
        
        Args:
            taxable_income: 应税收入
            
        Returns:
            Decimal: 个人所得税金额
        """
        if taxable_income <= self.TAX_THRESHOLD:
            return Decimal('0.00')
        
        # 应税所得额
        taxable_amount = taxable_income - self.TAX_THRESHOLD
        
        # 个税税率表（月度）
        tax_brackets = [
            (Decimal('3000'), Decimal('0.03'), Decimal('0')),      # 3%
            (Decimal('12000'), Decimal('0.10'), Decimal('210')),   # 10%
            (Decimal('25000'), Decimal('0.20'), Decimal('1410')),  # 20%
            (Decimal('35000'), Decimal('0.25'), Decimal('2660')),  # 25%
            (Decimal('55000'), Decimal('0.30'), Decimal('4410')),  # 30%
            (Decimal('80000'), Decimal('0.35'), Decimal('7160')),  # 35%
            (None, Decimal('0.45'), Decimal('15160')),             # 45%
        ]
        
        for threshold, rate, quick_deduction in tax_brackets:
            if threshold is None or taxable_amount <= threshold:
                tax = taxable_amount * rate - quick_deduction
                return max(Decimal('0.00'), tax.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))
        
        return Decimal('0.00')
    
    def _calculate_social_insurance(self, basic_salary: Decimal) -> Decimal:
        """计算社会保险费用
        
        Args:
            basic_salary: 基本工资
            
        Returns:
            Decimal: 社会保险费用总额
        """
        total_insurance = Decimal('0.00')
        
        for insurance_type, rate in self.SOCIAL_INSURANCE_RATES.items():
            insurance_amount = basic_salary * rate
            total_insurance += insurance_amount
        
        return total_insurance.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    
    def batch_calculate_salary(self, employee_ids: List[int], salary_month: str) -> List[Dict]:
        """批量计算工资
        
        Args:
            employee_ids: 员工ID列表
            salary_month: 工资月份
            
        Returns:
            List[Dict]: 计算结果列表
        """
        results = []
        failed_employees = []
        
        for employee_id in employee_ids:
            try:
                result = self.calculate_monthly_salary(employee_id, salary_month)
                results.append(result)
            except Exception as e:
                self.logger.error(f'员工 {employee_id} 工资计算失败: {str(e)}')
                failed_employees.append({
                    'employee_id': employee_id,
                    'error': str(e)
                })
        
        if failed_employees:
            self.logger.warning(f'批量计算中 {len(failed_employees)} 个员工计算失败')
        
        return {
            'success_count': len(results),
            'failed_count': len(failed_employees),
            'results': results,
            'failed_employees': failed_employees
        }
```

#### 2.5 表单定义规范

```python
from django import forms
from django.core.exceptions import ValidationError
from decimal import Decimal
from .models import SalaryGrade, EmployeeSalaryConfig

class SalaryGradeForm(forms.ModelForm):
    """薪资等级表单
    
    用于薪资等级的创建和编辑
    """
    
    class Meta:
        model = SalaryGrade
        fields = ['grade_name', 'min_salary', 'max_salary', 'description', 'is_active']
        widgets = {
            'grade_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '请输入等级名称',
                'maxlength': 50
            }),
            'min_salary': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '请输入最低薪资',
                'step': '0.01',
                'min': '0.01'
            }),
            'max_salary': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '请输入最高薪资',
                'step': '0.01',
                'min': '0.01'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': '请输入等级描述',
                'rows': 3
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
        labels = {
            'grade_name': '等级名称',
            'min_salary': '最低薪资',
            'max_salary': '最高薪资',
            'description': '描述',
            'is_active': '是否启用'
        }
        help_texts = {
            'grade_name': '薪资等级的名称，如：初级、中级、高级等',
            'min_salary': '该等级的最低薪资标准',
            'max_salary': '该等级的最高薪资标准',
            'description': '等级的详细描述信息',
            'is_active': '是否启用该薪资等级'
        }
    
    def clean(self):
        """表单整体验证"""
        cleaned_data = super().clean()
        min_salary = cleaned_data.get('min_salary')
        max_salary = cleaned_data.get('max_salary')
        
        if min_salary and max_salary:
            if min_salary >= max_salary:
                raise ValidationError('最低薪资必须小于最高薪资')
        
        return cleaned_data
    
    def clean_grade_name(self):
        """等级名称验证"""
        grade_name = self.cleaned_data.get('grade_name')
        if grade_name:
            grade_name = grade_name.strip()
            if len(grade_name) < 2:
                raise ValidationError('等级名称至少需要2个字符')
        return grade_name
```

### 3. 错误处理和日志规范

```python
import logging
from django.http import JsonResponse
from django.shortcuts import render
from django.contrib import messages

# 配置日志
logger = logging.getLogger(__name__)

def handle_view_exception(view_func):
    """视图异常处理装饰器"""
    def wrapper(request, *args, **kwargs):
        try:
            return view_func(request, *args, **kwargs)
        except ValidationError as e:
            logger.warning(f'验证错误: {str(e)}')
            messages.error(request, str(e))
            return redirect('home')
        except Exception as e:
            logger.error(f'视图异常: {view_func.__name__}, 错误: {str(e)}')
            messages.error(request, '系统异常，请联系管理员')
            return render(request, 'error.html', {'error_message': '系统异常'})
    return wrapper

def handle_ajax_exception(ajax_func):
    """AJAX异常处理装饰器"""
    def wrapper(request, *args, **kwargs):
        try:
            return ajax_func(request, *args, **kwargs)
        except ValidationError as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            }, status=400)
        except Exception as e:
            logger.error(f'AJAX异常: {ajax_func.__name__}, 错误: {str(e)}')
            return JsonResponse({
                'success': False,
                'message': '系统异常，请重试'
            }, status=500)
    return wrapper
```

## 前端代码生成规范

### 1. HTML模板规范

#### 1.1 基础模板结构

```html
<!-- templates/base.html -->
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="人事公司工资管理系统">
    <title>{% block title %}人事公司工资管理系统{% endblock %}</title>
    
    <!-- CSS文件引入 -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.7.2/font/bootstrap-icons.css" rel="stylesheet">
    <link href="{% static 'css/custom.css' %}" rel="stylesheet">
    
    <!-- 页面特定CSS -->
    {% block extra_css %}{% endblock %}
</head>
<body>
    <!-- 导航栏 -->
    <nav class="navbar navbar-expand-lg navbar-dark bg-primary fixed-top">
        <div class="container-fluid">
            <a class="navbar-brand" href="{% url 'home' %}">
                <i class="bi bi-building"></i>
                人事工资管理系统
            </a>
            
            <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
                <span class="navbar-toggler-icon"></span>
            </button>
            
            <div class="collapse navbar-collapse" id="navbarNav">
                <ul class="navbar-nav me-auto">
                    <li class="nav-item">
                        <a class="nav-link" href="{% url 'home' %}">首页</a>
                    </li>
                    <li class="nav-item dropdown">
                        <a class="nav-link dropdown-toggle" href="#" id="salaryDropdown" role="button" data-bs-toggle="dropdown">
                            工资管理
                        </a>
                        <ul class="dropdown-menu">
                            <li><a class="dropdown-item" href="{% url 'salary_management:grade_list' %}">薪资等级</a></li>
                            <li><a class="dropdown-item" href="{% url 'salary_management:config_list' %}">员工薪资配置</a></li>
                            <li><a class="dropdown-item" href="{% url 'salary_management:calculate' %}">工资计算</a></li>
                            <li><a class="dropdown-item" href="{% url 'salary_management:record_list' %}">工资记录</a></li>
                        </ul>
                    </li>
                </ul>
                
                <ul class="navbar-nav">
                    {% if user.is_authenticated %}
                        <li class="nav-item dropdown">
                            <a class="nav-link dropdown-toggle" href="#" id="userDropdown" role="button" data-bs-toggle="dropdown">
                                <i class="bi bi-person-circle"></i>
                                {{ user.username }}
                            </a>
                            <ul class="dropdown-menu">
                                <li><a class="dropdown-item" href="#">个人设置</a></li>
                                <li><hr class="dropdown-divider"></li>
                                <li><a class="dropdown-item" href="{% url 'logout' %}">退出登录</a></li>
                            </ul>
                        </li>
                    {% else %}
                        <li class="nav-item">
                            <a class="nav-link" href="{% url 'login' %}">登录</a>
                        </li>
                    {% endif %}
                </ul>
            </div>
        </div>
    </nav>
    
    <!-- 主要内容区域 -->
    <div class="container-fluid" style="margin-top: 76px;">
        <div class="row">
            <!-- 侧边栏 -->
            <nav class="col-md-2 d-none d-md-block bg-light sidebar">
                <div class="position-sticky pt-3">
                    {% block sidebar %}
                        {% include 'includes/sidebar.html' %}
                    {% endblock %}
                </div>
            </nav>
            
            <!-- 主内容区 -->
            <main class="col-md-10 ms-sm-auto px-md-4">
                <!-- 面包屑导航 -->
                {% block breadcrumb %}
                    <nav aria-label="breadcrumb" class="mt-3">
                        <ol class="breadcrumb">
                            <li class="breadcrumb-item"><a href="{% url 'home' %}">首页</a></li>
                            {% block breadcrumb_items %}{% endblock %}
                        </ol>
                    </nav>
                {% endblock %}
                
                <!-- 消息提示 -->
                {% if messages %}
                    <div class="alert-container mt-3">
                        {% for message in messages %}
                            <div class="alert alert-{{ message.tags }} alert-dismissible fade show" role="alert">
                                {{ message }}
                                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                            </div>
                        {% endfor %}
                    </div>
                {% endif %}
                
                <!-- 页面标题 -->
                {% block page_header %}
                    <div class="d-flex justify-content-between flex-wrap flex-md-nowrap align-items-center pt-3 pb-2 mb-3 border-bottom">
                        <h1 class="h2">{% block page_title %}页面标题{% endblock %}</h1>
                        <div class="btn-toolbar mb-2 mb-md-0">
                            {% block page_actions %}{% endblock %}
                        </div>
                    </div>
                {% endblock %}
                
                <!-- 主要内容 -->
                <div class="main-content">
                    {% block content %}
                    {% endblock %}
                </div>
            </main>
        </div>
    </div>
    
    <!-- 页脚 -->
    <footer class="bg-light text-center text-muted py-3 mt-5">
        <div class="container">
            <p>&copy; 2024 人事公司工资管理系统. All rights reserved.</p>
        </div>
    </footer>
    
    <!-- JavaScript文件引入 -->
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="{% static 'js/common.js' %}"></script>
    
    <!-- 页面特定JavaScript -->
    {% block extra_js %}{% endblock %}
</body>
</html>
```

#### 1.2 列表页面模板

```html
<!-- templates/salary_management/grade_list.html -->
{% extends 'base.html' %}
{% load static %}

{% block title %}薪资等级管理 - {{ block.super }}{% endblock %}

{% block breadcrumb_items %}
    <li class="breadcrumb-item">工资管理</li>
    <li class="breadcrumb-item active">薪资等级</li>
{% endblock %}

{% block page_title %}薪资等级管理{% endblock %}

{% block page_actions %}
    <button type="button" class="btn btn-primary" data-bs-toggle="modal" data-bs-target="#addGradeModal">
        <i class="bi bi-plus-circle"></i> 新增等级
    </button>
    <button type="button" class="btn btn-outline-secondary" onclick="exportData()">
        <i class="bi bi-download"></i> 导出
    </button>
{% endblock %}

{% block content %}
    <!-- 搜索和筛选区域 -->
    <div class="card mb-4">
        <div class="card-body">
            <form method="get" class="row g-3">
                <div class="col-md-4">
                    <label for="search" class="form-label">搜索</label>
                    <input type="text" class="form-control" id="search" name="search" 
                           value="{{ search_query }}" placeholder="等级名称或描述">
                </div>
                <div class="col-md-3">
                    <label for="is_active" class="form-label">状态</label>
                    <select class="form-select" id="is_active" name="is_active">
                        <option value="">全部</option>
                        <option value="true" {% if is_active == 'true' %}selected{% endif %}>启用</option>
                        <option value="false" {% if is_active == 'false' %}selected{% endif %}>禁用</option>
                    </select>
                </div>
                <div class="col-md-3 d-flex align-items-end">
                    <button type="submit" class="btn btn-outline-primary me-2">
                        <i class="bi bi-search"></i> 搜索
                    </button>
                    <a href="{% url 'salary_management:grade_list' %}" class="btn btn-outline-secondary">
                        <i class="bi bi-arrow-clockwise"></i> 重置
                    </a>
                </div>
            </form>
        </div>
    </div>
    
    <!-- 数据统计 -->
    <div class="row mb-4">
        <div class="col-md-3">
            <div class="card text-center">
                <div class="card-body">
                    <h5 class="card-title text-primary">{{ total_count }}</h5>
                    <p class="card-text">总等级数</p>
                </div>
            </div>
        </div>
        <div class="col-md-3">
            <div class="card text-center">
                <div class="card-body">
                    <h5 class="card-title text-success">{{ page_obj.paginator.count }}</h5>
                    <p class="card-text">当前筛选</p>
                </div>
            </div>
        </div>
    </div>
    
    <!-- 数据表格 -->
    <div class="card">
        <div class="card-header">
            <h5 class="card-title mb-0">薪资等级列表</h5>
        </div>
        <div class="card-body">
            {% if page_obj %}
                <div class="table-responsive">
                    <table class="table table-striped table-hover">
                        <thead class="table-dark">
                            <tr>
                                <th>
                                    <input type="checkbox" id="selectAll" class="form-check-input">
                                </th>
                                <th>等级名称</th>
                                <th>薪资范围</th>
                                <th>状态</th>
                                <th>创建时间</th>
                                <th>操作</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for grade in page_obj %}
                                <tr>
                                    <td>
                                        <input type="checkbox" class="form-check-input row-checkbox" 
                                               value="{{ grade.id }}">
                                    </td>
                                    <td>
                                        <strong>{{ grade.grade_name }}</strong>
                                        {% if grade.description %}
                                            <br><small class="text-muted">{{ grade.description|truncatechars:50 }}</small>
                                        {% endif %}
                                    </td>
                                    <td>
                                        <span class="badge bg-info">
                                            ¥{{ grade.min_salary|floatformat:2 }} - ¥{{ grade.max_salary|floatformat:2 }}
                                        </span>
                                    </td>
                                    <td>
                                        {% if grade.is_active %}
                                            <span class="badge bg-success">启用</span>
                                        {% else %}
                                            <span class="badge bg-secondary">禁用</span>
                                        {% endif %}
                                    </td>
                                    <td>{{ grade.created_at|date:"Y-m-d H:i" }}</td>
                                    <td>
                                        <div class="btn-group btn-group-sm" role="group">
                                            <button type="button" class="btn btn-outline-primary" 
                                                    onclick="editGrade({{ grade.id }})" title="编辑">
                                                <i class="bi bi-pencil"></i>
                                            </button>
                                            <button type="button" class="btn btn-outline-info" 
                                                    onclick="viewGrade({{ grade.id }})" title="查看">
                                                <i class="bi bi-eye"></i>
                                            </button>
                                            {% if grade.is_active %}
                                                <button type="button" class="btn btn-outline-warning" 
                                                        onclick="toggleStatus({{ grade.id }}, false)" title="禁用">
                                                    <i class="bi bi-pause-circle"></i>
                                                </button>
                                            {% else %}
                                                <button type="button" class="btn btn-outline-success" 
                                                        onclick="toggleStatus({{ grade.id }}, true)" title="启用">
                                                    <i class="bi bi-play-circle"></i>
                                                </button>
                                            {% endif %}
                                            <button type="button" class="btn btn-outline-danger" 
                                                    onclick="deleteGrade({{ grade.id }})" title="删除">
                                                <i class="bi bi-trash"></i>
                                            </button>
                                        </div>
                                    </td>
                                </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
                
                <!-- 分页 -->
                {% if page_obj.has_other_pages %}
                    <nav aria-label="分页导航">
                        <ul class="pagination justify-content-center">
                            {% if page_obj.has_previous %}
                                <li class="page-item">
                                    <a class="page-link" href="?page=1{% if search_query %}&search={{ search_query }}{% endif %}{% if is_active %}&is_active={{ is_active }}{% endif %}">
                                        首页
                                    </a>
                                </li>
                                <li class="page-item">
                                    <a class="page-link" href="?page={{ page_obj.previous_page_number }}{% if search_query %}&search={{ search_query }}{% endif %}{% if is_active %}&is_active={{ is_active }}{% endif %}">
                                        上一页
                                    </a>
                                </li>
                            {% endif %}
                            
                            <li class="page-item active">
                                <span class="page-link">
                                    第 {{ page_obj.number }} 页，共 {{ page_obj.paginator.num_pages }} 页
                                </span>
                            </li>
                            
                            {% if page_obj.has_next %}
                                <li class="page-item">
                                    <a class="page-link" href="?page={{ page_obj.next_page_number }}{% if search_query %}&search={{ search_query }}{% endif %}{% if is_active %}&is_active={{ is_active }}{% endif %}">
                                        下一页
                                    </a>
                                </li>
                                <li class="page-item">
                                    <a class="page-link" href="?page={{ page_obj.paginator.num_pages }}{% if search_query %}&search={{ search_query }}{% endif %}{% if is_active %}&is_active={{ is_active }}{% endif %}">
                                        末页
                                    </a>
                                </li>
                            {% endif %}
                        </ul>
                    </nav>
                {% endif %}
            {% else %}
                <div class="text-center py-5">
                    <i class="bi bi-inbox display-1 text-muted"></i>
                    <h4 class="text-muted mt-3">暂无数据</h4>
                    <p class="text-muted">点击上方"新增等级"按钮添加第一个薪资等级</p>
                </div>
            {% endif %}
        </div>
    </div>
    
    <!-- 新增等级模态框 -->
    <div class="modal fade" id="addGradeModal" tabindex="-1">
        <div class="modal-dialog">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title">新增薪资等级</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                </div>
                <form id="addGradeForm" method="post">
                    {% csrf_token %}
                    <div class="modal-body">
                        <div class="mb-3">
                            <label for="grade_name" class="form-label">等级名称 <span class="text-danger">*</span></label>
                            <input type="text" class="form-control" id="grade_name" name="grade_name" required>
                        </div>
                        <div class="row">
                            <div class="col-md-6">
                                <div class="mb-3">
                                    <label for="min_salary" class="form-label">最低薪资 <span class="text-danger">*</span></label>
                                    <input type="number" class="form-control" id="min_salary" name="min_salary" 
                                           step="0.01" min="0.01" required>
                                </div>
                            </div>
                            <div class="col-md-6">
                                <div class="mb-3">
                                    <label for="max_salary" class="form-label">最高薪资 <span class="text-danger">*</span></label>
                                    <input type="number" class="form-control" id="max_salary" name="max_salary" 
                                           step="0.01" min="0.01" required>
                                </div>
                            </div>
                        </div>
                        <div class="mb-3">
                            <label for="description" class="form-label">描述</label>
                            <textarea class="form-control" id="description" name="description" rows="3"></textarea>
                        </div>
                        <div class="mb-3 form-check">
                            <input type="checkbox" class="form-check-input" id="is_active" name="is_active" checked>
                            <label class="form-check-label" for="is_active">启用该等级</label>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">取消</button>
                        <button type="submit" class="btn btn-primary">保存</button>
                    </div>
                </form>
            </div>
        </div>
    </div>
{% endblock %}

{% block extra_js %}
    <script src="{% static 'js/salary_grade.js' %}"></script>
{% endblock %}
```

### 2. CSS样式规范

```css
/* static/css/custom.css */

/* 全局样式 */
:root {
    --primary-color: #0d6efd;
    --secondary-color: #6c757d;
    --success-color: #198754;
    --danger-color: #dc3545;
    --warning-color: #ffc107;
    --info-color: #0dcaf0;
    --light-color: #f8f9fa;
    --dark-color: #212529;
    
    --border-radius: 0.375rem;
    --box-shadow: 0 0.125rem 0.25rem rgba(0, 0, 0, 0.075);
    --transition: all 0.15s ease-in-out;
}

/* 基础样式重置 */
* {
    box-sizing: border-box;
}

body {
    font-family: 'Microsoft YaHei', 'Helvetica Neue', Arial, sans-serif;
    line-height: 1.6;
    color: var(--dark-color);
    background-color: #f5f5f5;
}

/* 导航栏样式 */
.navbar-brand {
    font-weight: 600;
    font-size: 1.25rem;
}

.navbar-nav .nav-link {
    font-weight: 500;
    transition: var(--transition);
}

.navbar-nav .nav-link:hover {
    color: rgba(255, 255, 255, 0.8) !important;
}

/* 侧边栏样式 */
.sidebar {
    position: fixed;
    top: 76px;
    bottom: 0;
    left: 0;
    z-index: 100;
    padding: 0;
    box-shadow: inset -1px 0 0 rgba(0, 0, 0, 0.1);
    overflow-y: auto;
}

.sidebar .nav-link {
    color: var(--dark-color);
    padding: 0.75rem 1rem;
    border-bottom: 1px solid rgba(0, 0, 0, 0.05);
    transition: var(--transition);
}

.sidebar .nav-link:hover {
    background-color: rgba(0, 0, 0, 0.05);
    color: var(--primary-color);
}

.sidebar .nav-link.active {
    background-color: var(--primary-color);
    color: white;
}

.sidebar .nav-link i {
    margin-right: 0.5rem;
    width: 16px;
    text-align: center;
}

/* 主内容区样式 */
.main-content {
    min-height: calc(100vh - 200px);
}

/* 卡片样式 */
.card {
    border: none;
    box-shadow: var(--box-shadow);
    border-radius: var(--border-radius);
    margin-bottom: 1.5rem;
}

.card-header {
    background-color: white;
    border-bottom: 1px solid rgba(0, 0, 0, 0.125);
    font-weight: 600;
}

/* 表格样式 */
.table {
    margin-bottom: 0;
}

.table th {
    border-top: none;
    font-weight: 600;
    font-size: 0.875rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

.table-hover tbody tr:hover {
    background-color: rgba(0, 0, 0, 0.02);
}

/* 按钮样式 */
.btn {
    font-weight: 500;
    border-radius: var(--border-radius);
    transition: var(--transition);
}

.btn-group-sm > .btn {
    padding: 0.25rem 0.5rem;
    font-size: 0.75rem;
}

/* 表单样式 */
.form-control, .form-select {
    border-radius: var(--border-radius);
    border: 1px solid #ced4da;
    transition: var(--transition);
}

.form-control:focus, .form-select:focus {
    border-color: var(--primary-color);
    box-shadow: 0 0 0 0.2rem rgba(13, 110, 253, 0.25);
}

.form-label {
    font-weight: 500;
    margin-bottom: 0.5rem;
}

/* 徽章样式 */
.badge {
    font-weight: 500;
    font-size: 0.75em;
}

/* 分页样式 */
.pagination {
    margin-bottom: 0;
}

.page-link {
    color: var(--primary-color);
    border-radius: var(--border-radius);
    margin: 0 2px;
    border: 1px solid #dee2e6;
}

.page-link:hover {
    background-color: var(--light-color);
    border-color: #adb5bd;
}

.page-item.active .page-link {
    background-color: var(--primary-color);
    border-color: var(--primary-color);
}

/* 模态框样式 */
.modal-content {
    border: none;
    box-shadow: 0 0.5rem 1rem rgba(0, 0, 0, 0.15);
    border-radius: var(--border-radius);
}

.modal-header {
    border-bottom: 1px solid rgba(0, 0, 0, 0.125);
}

.modal-footer {
    border-top: 1px solid rgba(0, 0, 0, 0.125);
}

/* 面包屑样式 */
.breadcrumb {
    background-color: transparent;
    padding: 0;
    margin-bottom: 1rem;
}

.breadcrumb-item + .breadcrumb-item::before {
    content: ">";
    color: var(--secondary-color);
}

/* 警告框样式 */
.alert {
    border: none;
    border-radius: var(--border-radius);
    font-weight: 500;
}

/* 统计卡片样式 */
.stats-card {
    background: linear-gradient(135deg, var(--primary-color), #0056b3);
    color: white;
    border-radius: var(--border-radius);
    padding: 1.5rem;
    margin-bottom: 1rem;
}

.stats-card h3 {
    font-size: 2rem;
    font-weight: 700;
    margin-bottom: 0.5rem;
}

.stats-card p {
    margin-bottom: 0;
    opacity: 0.9;
}

/* 加载动画 */
.loading {
    display: inline-block;
    width: 20px;
    height: 20px;
    border: 3px solid rgba(255, 255, 255, 0.3);
    border-radius: 50%;
    border-top-color: #fff;
    animation: spin 1s ease-in-out infinite;
}

@keyframes spin {
    to { transform: rotate(360deg); }
}

/* 响应式设计 */
@media (max-width: 768px) {
    .sidebar {
        position: static;
        height: auto;
    }
    
    .main-content {
        margin-left: 0;
    }
    
    .table-responsive {
        font-size: 0.875rem;
    }
    
    .btn-group-sm > .btn {
        padding: 0.125rem 0.25rem;
        font-size: 0.6875rem;
    }
}

/* 打印样式 */
@media print {
    .navbar, .sidebar, .btn, .pagination {
        display: none !important;
    }
    
    .main-content {
        margin-left: 0;
    }
    
    .card {
        box-shadow: none;
        border: 1px solid #dee2e6;
    }
}

/* 工具类 */
.text-truncate-2 {
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
}

.cursor-pointer {
    cursor: pointer;
}

.border-dashed {
    border-style: dashed !important;
}

.bg-gradient-primary {
    background: linear-gradient(135deg, var(--primary-color), #0056b3);
}

.shadow-sm {
    box-shadow: var(--box-shadow) !important;
}
```

### 3. JavaScript规范

```javascript
// static/js/common.js

/**
 * 通用JavaScript工具库
 * 包含常用的工具函数和全局配置
 */

// 全局配置
window.APP_CONFIG = {
    // API基础URL
    API_BASE_URL: '/api/',
    
    // CSRF Token
    CSRF_TOKEN: document.querySelector('[name=csrfmiddlewaretoken]')?.value || '',
    
    // 分页配置
    PAGE_SIZE: 20,
    
    // 消息显示时间
    MESSAGE_TIMEOUT: 5000,
    
    // 日期格式
    DATE_FORMAT: 'YYYY-MM-DD',
    DATETIME_FORMAT: 'YYYY-MM-DD HH:mm:ss'
};

/**
 * 工具函数库
 */
window.Utils = {
    
    /**
     * 显示成功消息
     * @param {string} message - 消息内容
     * @param {number} timeout - 显示时间（毫秒）
     */
    showSuccess: function(message, timeout = APP_CONFIG.MESSAGE_TIMEOUT) {
        this.showMessage(message, 'success', timeout);
    },
    
    /**
     * 显示错误消息
     * @param {string} message - 消息内容
     * @param {number} timeout - 显示时间（毫秒）
     */
    showError: function(message, timeout = APP_CONFIG.MESSAGE_TIMEOUT) {
        this.showMessage(message, 'danger', timeout);
    },
    
    /**
     * 显示警告消息
     * @param {string} message - 消息内容
     * @param {number} timeout - 显示时间（毫秒）
     */
    showWarning: function(message, timeout = APP_CONFIG.MESSAGE_TIMEOUT) {
        this.showMessage(message, 'warning', timeout);
    },
    
    /**
     * 显示消息
     * @param {string} message - 消息内容
     * @param {string} type - 消息类型（success, danger, warning, info）
     * @param {number} timeout - 显示时间（毫秒）
     */
    showMessage: function(message, type = 'info', timeout = APP_CONFIG.MESSAGE_TIMEOUT) {
        const alertContainer = document.querySelector('.alert-container') || 
                              document.querySelector('.main-content');
        
        if (!alertContainer) return;
        
        const alertId = 'alert-' + Date.now();
        const alertHtml = `
            <div id="${alertId}" class="alert alert-${type} alert-dismissible fade show" role="alert">
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `;
        
        alertContainer.insertAdjacentHTML('afterbegin', alertHtml);
        
        // 自动隐藏
        if (timeout > 0) {
            setTimeout(() => {
                const alert = document.getElementById(alertId);
                if (alert) {
                    const bsAlert = new bootstrap.Alert(alert);
                    bsAlert.close();
                }
            }, timeout);
        }
    },
    
    /**
     * 发送AJAX请求
     * @param {Object} options - 请求配置
     * @returns {Promise} - 请求Promise
     */
    ajax: function(options) {
        const defaults = {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': APP_CONFIG.CSRF_TOKEN
            },
            credentials: 'same-origin'
        };
        
        const config = Object.assign({}, defaults, options);
        
        // 如果是POST请求且数据是对象，转换为JSON
        if (config.method === 'POST' && config.data && typeof config.data === 'object') {
            config.body = JSON.stringify(config.data);
        }
        
        return fetch(config.url, config)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                return response.json();
            })
            .catch(error => {
                console.error('AJAX请求失败:', error);
                throw error;
            });
    },
    
    /**
     * 格式化日期
     * @param {Date|string} date - 日期对象或字符串
     * @param {string} format - 格式字符串
     * @returns {string} - 格式化后的日期字符串
     */
    formatDate: function(date, format = APP_CONFIG.DATE_FORMAT) {
        if (!date) return '';
        
        const d = new Date(date);
        if (isNaN(d.getTime())) return '';
        
        const year = d.getFullYear();
        const month = String(d.getMonth() + 1).padStart(2, '0');
        const day = String(d.getDate()).padStart(2, '0');
        const hours = String(d.getHours()).padStart(2, '0');
        const minutes = String(d.getMinutes()).padStart(2, '0');
        const seconds = String(d.getSeconds()).padStart(2, '0');
        
        return format
            .replace('YYYY', year)
            .replace('MM', month)
            .replace('DD', day)
            .replace('HH', hours)
            .replace('mm', minutes)
            .replace('ss', seconds);
    },
    
    /**
     * 格式化金额
     * @param {number} amount - 金额
     * @param {number} decimals - 小数位数
     * @returns {string} - 格式化后的金额字符串
     */
    formatMoney: function(amount, decimals = 2) {
        if (isNaN(amount)) return '0.00';
        
        return Number(amount).toLocaleString('zh-CN', {
            minimumFractionDigits: decimals,
            maximumFractionDigits: decimals
        });
    },
    
    /**
     * 防抖函数
     * @param {Function} func - 要防抖的函数
     * @param {number} wait - 等待时间（毫秒）
     * @returns {Function} - 防抖后的函数
     */
    debounce: function(func, wait = 300) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func.apply(this, args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },
    
    /**
     * 节流函数
     * @param {Function} func - 要节流的函数
     * @param {number} limit - 限制时间（毫秒）
     * @returns {Function} - 节流后的函数
     */
    throttle: function(func, limit = 300) {
        let inThrottle;
        return function executedFunction(...args) {
            if (!inThrottle) {
                func.apply(this, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    },
    
    /**
     * 确认对话框
     * @param {string} message - 确认消息
     * @param {Function} callback - 确认后的回调函数
     */
    confirm: function(message, callback) {
        if (window.confirm(message)) {
            if (typeof callback === 'function') {
                callback();
            }
        }
    },
    
    /**
     * 显示加载状态
     * @param {HTMLElement} element - 目标元素
     * @param {boolean} show - 是否显示加载状态
     */
    showLoading: function(element, show = true) {
        if (!element) return;
        
        if (show) {
            element.disabled = true;
            const originalText = element.textContent;
            element.dataset.originalText = originalText;
            element.innerHTML = '<span class="loading"></span> 加载中...';
        } else {
            element.disabled = false;
            element.textContent = element.dataset.originalText || '确定';
        }
    }
};

/**
 * 表单验证工具
 */
window.FormValidator = {
    
    /**
     * 验证必填字段
     * @param {HTMLFormElement} form - 表单元素
     * @returns {boolean} - 验证结果
     */
    validateRequired: function(form) {
        const requiredFields = form.querySelectorAll('[required]');
        let isValid = true;
        
        requiredFields.forEach(field => {
            if (!field.value.trim()) {
                this.showFieldError(field, '此字段为必填项');
                isValid = false;
            } else {
                this.clearFieldError(field);
            }
        });
        
        return isValid;
    },
    
    /**
     * 显示字段错误
     * @param {HTMLElement} field - 字段元素
     * @param {string} message - 错误消息
     */
    showFieldError: function(field, message) {
        field.classList.add('is-invalid');
        
        let feedback = field.parentNode.querySelector('.invalid-feedback');
        if (!feedback) {
            feedback = document.createElement('div');
            feedback.className = 'invalid-feedback';
            field.parentNode.appendChild(feedback);
        }
        feedback.textContent = message;
    },
    
    /**
     * 清除字段错误
     * @param {HTMLElement} field - 字段元素
     */
    clearFieldError: function(field) {
        field.classList.remove('is-invalid');
        const feedback = field.parentNode.querySelector('.invalid-feedback');
        if (feedback) {
            feedback.remove();
        }
    }
};

// 页面加载完成后的初始化
document.addEventListener('DOMContentLoaded', function() {
    
    // 初始化所有工具提示
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // 全选功能
    const selectAllCheckbox = document.getElementById('selectAll');
    if (selectAllCheckbox) {
        selectAllCheckbox.addEventListener('change', function() {
            const checkboxes = document.querySelectorAll('.row-checkbox');
            checkboxes.forEach(checkbox => {
                checkbox.checked = this.checked;
            });
        });
    }
    
    // 自动隐藏消息提示
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, APP_CONFIG.MESSAGE_TIMEOUT);
    });
});
```

## 4. 开发最佳实践

### 4.1 代码质量标准

1. **代码注释**：
   - 所有公共方法必须有详细的文档注释
   - 复杂业务逻辑必须有行内注释说明
   - 使用中文注释，便于团队理解

2. **错误处理**：
   - 所有用户输入必须进行验证
   - 数据库操作必须使用事务
   - 异常信息要记录到日志
   - 用户界面要显示友好的错误提示

3. **性能优化**：
   - 数据库查询使用索引
   - 大数据量操作使用分页
   - 静态资源使用CDN
   - 合理使用缓存机制

4. **安全规范**：
   - 所有表单使用CSRF保护
   - 用户输入进行XSS过滤
   - 敏感操作需要权限验证
   - 密码等敏感信息加密存储

### 4.2 测试规范

```python
# 单元测试示例
from django.test import TestCase
from django.contrib.auth.models import User
from decimal import Decimal
from .models import SalaryGrade
from .services import SalaryCalculationService

class SalaryGradeModelTest(TestCase):
    """薪资等级模型测试"""
    
    def setUp(self):
        """测试数据准备"""
        self.grade_data = {
            'grade_name': '中级工程师',
            'min_salary': Decimal('8000.00'),
            'max_salary': Decimal('12000.00'),
            'description': '中级开发工程师薪资等级'
        }
    
    def test_create_salary_grade(self):
        """测试创建薪资等级"""
        grade = SalaryGrade.objects.create(**self.grade_data)
        self.assertEqual(grade.grade_name, '中级工程师')
        self.assertEqual(grade.min_salary, Decimal('8000.00'))
        self.assertTrue(grade.is_active)
    
    def test_salary_range_property(self):
        """测试薪资区间属性"""
        grade = SalaryGrade.objects.create(**self.grade_data)
        expected_range = '8000.00-12000.00'
        self.assertEqual(grade.salary_range, expected_range)
    
    def test_validation_min_greater_than_max(self):
        """测试最低薪资大于最高薪资的验证"""
        invalid_data = self.grade_data.copy()
        invalid_data['min_salary'] = Decimal('15000.00')
        
        with self.assertRaises(ValidationError):
            grade = SalaryGrade(**invalid_data)
            grade.full_clean()

class SalaryCalculationServiceTest(TestCase):
    """工资计算服务测试"""
    
    def setUp(self):
        """测试数据准备"""
        self.service = SalaryCalculationService()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
    
    def test_calculate_income_tax(self):
        """测试个人所得税计算"""
        # 测试免税额以下
        tax = self.service._calculate_income_tax(Decimal('4000.00'))
        self.assertEqual(tax, Decimal('0.00'))
        
        # 测试3%税率
        tax = self.service._calculate_income_tax(Decimal('6000.00'))
        expected = (Decimal('6000.00') - Decimal('5000.00')) * Decimal('0.03')
        self.assertEqual(tax, expected)
    
    def test_calculate_social_insurance(self):
        """测试社保计算"""
        basic_salary = Decimal('10000.00')
        insurance = self.service._calculate_social_insurance(basic_salary)
        
        expected = basic_salary * (Decimal('0.08') + Decimal('0.02') + Decimal('0.005'))
        self.assertEqual(insurance, expected.quantize(Decimal('0.01')))
```

### 4.3 部署和运维规范

1. **环境配置**：
   - 开发、测试、生产环境分离
   - 使用环境变量管理配置
   - 数据库连接池配置
   - 日志级别和输出配置

2. **静态文件管理**：
   - 使用Django的collectstatic命令
   - 配置静态文件服务器
   - 启用Gzip压缩
   - 设置合适的缓存头

3. **数据库优化**：
   - 定期备份数据库
   - 监控慢查询
   - 合理设置索引
   - 定期清理无用数据

4. **监控和日志**：
   - 应用性能监控
   - 错误日志收集
   - 用户行为分析
   - 系统资源监控

## 5. 项目结构和文件组织

```
hr_salary_management/
├── manage.py
├── requirements.txt
├── README.md
├── .env.example
├── .gitignore
├── hrms/                     # 项目配置目录
│   ├── __init__.py
│   ├── settings/
│   │   ├── __init__.py
│   │   ├── base.py          # 基础配置
│   │   ├── development.py   # 开发环境配置
│   │   ├── production.py    # 生产环境配置
│   │   └── testing.py       # 测试环境配置
│   ├── urls.py
│   └── wsgi.py
├── apps/                     # 应用目录
│   ├── __init__.py
│   ├── common/              # 公共模块
│   │   ├── __init__.py
│   │   ├── models.py        # 基础模型
│   │   ├── utils.py         # 工具函数
│   │   ├── validators.py    # 验证器
│   │   └── mixins.py        # 混入类
│   ├── department/          # 部门管理
│   ├── personal/            # 个人信息管理
│   ├── station/             # 岗位管理
│   └── salary_management/   # 工资管理
├── static/                  # 静态文件
│   ├── css/
│   ├── js/
│   ├── images/
│   └── fonts/
├── templates/               # 模板文件
│   ├── base.html
│   ├── includes/
│   └── [app_name]/
├── media/                   # 媒体文件
├── logs/                    # 日志文件
├── docs/                    # 文档
└── tests/                   # 测试文件
```

## 6. Git提交规范

### 6.1 提交消息格式

```
<type>(<scope>): <subject>

<body>

<footer>
```

### 6.2 类型说明

- **feat**: 新功能
- **fix**: 修复bug
- **docs**: 文档更新
- **style**: 代码格式调整
- **refactor**: 代码重构
- **test**: 测试相关
- **chore**: 构建过程或辅助工具的变动

### 6.3 示例

```
feat(salary): 添加薪资等级管理功能

- 新增薪资等级模型
- 实现等级的增删改查
- 添加等级验证逻辑
- 完善前端交互界面

Closes #123
```

## 7. 代码审查清单

### 7.1 功能性检查
- [ ] 功能是否按需求实现
- [ ] 边界条件是否处理
- [ ] 错误处理是否完善
- [ ] 用户体验是否友好

### 7.2 代码质量检查
- [ ] 代码是否符合规范
- [ ] 命名是否清晰易懂
- [ ] 注释是否充分
- [ ] 是否有重复代码

### 7.3 安全性检查
- [ ] 输入验证是否充分
- [ ] SQL注入防护
- [ ] XSS攻击防护
- [ ] 权限控制是否正确

### 7.4 性能检查
- [ ] 数据库查询是否优化
- [ ] 是否存在N+1查询问题
- [ ] 静态资源是否压缩
- [ ] 缓存策略是否合理

---

**注意事项**：
1. 本规范适用于人事公司工资管理系统的开发
2. 所有开发人员必须严格遵守本规范
3. 代码提交前必须通过代码审查
4. 定期更新和完善开发规范