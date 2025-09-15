该项目是一个基于Django框架的人力资源管理系统（HRMS），包含了多个功能模块，如部门管理、员工信息管理、招聘管理、薪资管理、岗位管理、培训管理以及奖励管理等。该项目通过Django REST framework实现了基于API的增删查改操作，适用于构建前后端分离的人力资源管理系统。

## 功能模块

### 部门管理 (department)
- 部门信息的增删查改
- 部门列表展示
- 部门详情查看

### 员工管理 (personal)
- 员工信息的增删查改
- 员工列表展示
- 根据部门获取员工信息
- 计算员工年龄

### 招聘管理 (recruit)
- 招聘信息的增删查改
- 招聘列表展示
- 招聘详情查看

### 薪资管理 (salary)
- 薪资信息的增删查改
- 薪资列表展示
- 薪资详情查看
- 薪资计算（包含奖励金额）

### 岗位管理 (station)
- 岗位信息的增删查改
- 岗位列表展示
- 根据部门获取岗位信息

### 培训管理 (train)
- 培训信息的增删查改
- 培训列表展示
- 培训详情查看

### 奖励管理 (rewards)
- 奖励信息的增删查改
- 奖励列表展示
- 奖励详情查看

### 用户认证 (hr)
- 用户登录
- 用户登出

### 返回值封装
- `ResultVo`：用于封装操作结果（成功/失败）及数据。
- `ResultPageVo`：用于封装分页查询结果。

## 技术栈
- Python
- Django
- Django REST framework

## 安装与运行
1. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```
2. 数据库迁移：
   ```bash
   python manage.py migrate
   ```
3. 启动开发服务器：
   ```bash
   python manage.py runserver
   ```

## 使用说明
- 所有模块均提供基于API的接口，可通过POST、GET、PUT、DELETE方法进行操作。
- 接口地址定义在各模块的`urls.py`文件中。
- 数据模型定义在各模块的`models.py`文件中。
- 序列化器定义在各模块的`serializers.py`文件中。

## 贡献
欢迎提交Issue和Pull Request来改进本项目。

## 许可证
本项目采用MIT License，请查看具体的许可证文件。