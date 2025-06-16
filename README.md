# 公司员工管理系统

基于Flask、Python和SQL Server的公司员工管理系统，用于管理公司员工信息、部门结构、考勤和薪资等数据。

## 功能特点

- 员工信息管理：添加、编辑、删除员工信息
- 部门管理：创建、编辑、删除部门
- 用户权限控制：管理员、经理和普通用户
- 仪表盘：显示公司人员统计数据
- 员工查询：通过名称、部门等条件搜索员工
- 响应式设计：适配PC和移动设备

## 技术栈

- 后端：Python + Flask
- 数据库：SQL Server
- 前端：HTML + CSS + JavaScript + Bootstrap 5
- 数据库连接：pyodbc
- 表格展示：DataTables

## 安装步骤

1. 确保已安装Python 3.7+和SQL Server 2019+
2. 安装项目依赖

```bash
pip install -r requirements.txt
```

3. 配置SQL Server

```bash
# 在SQL Server中执行以下脚本创建数据库和表
sqlcmd -S localhost -i create_database.sql
```

4. 修改数据库连接信息

在 `app.py` 文件中修改数据库连接信息：

```python
def get_db_connection():
    conn = pyodbc.connect('DRIVER={ODBC Driver 17 for SQL Server};'
                          'SERVER=你的服务器名称;'
                          'DATABASE=EmployeeManagement;'
                          'UID=你的用户名;'
                          'PWD=你的密码;')
    return conn
```

## 启动应用

```bash
python app.py
```

然后在浏览器中访问：http://localhost:5000

## 账号信息

系统默认创建了两个账号：

- 管理员账号：admin / admin123
- 经理账号：manager / manager123

## 系统截图

![登录界面](screenshots/login.png)
![仪表盘](screenshots/dashboard.png)
![员工管理](screenshots/employees.png)
![部门管理](screenshots/departments.png)

## 项目结构

```
employee_management/
│
├── app.py                 # Flask应用主文件
├── create_database.sql    # SQL Server数据库初始化脚本
├── requirements.txt       # 项目依赖
│
├── static/                # 静态文件
│   ├── css/               # CSS样式
│   │   └── style.css      # 自定义样式
│   │
│   └── js/                # JavaScript文件
│       └── script.js      # 自定义脚本
│
├── templates/             # HTML模板
│   ├── base.html          # 基础模板
│   ├── login.html         # 登录页面
│   ├── dashboard.html     # 仪表盘页面
│   ├── employees.html     # 员工管理页面
│   ├── edit_employee.html # 编辑员工页面
│   ├── departments.html   # 部门管理页面
│   └── edit_department.html # 编辑部门页面
│
└── screenshots/           # 系统截图
```

## 依赖包

创建`requirements.txt`文件，内容如下：

```
Flask==2.3.2
pyodbc==4.0.39
Werkzeug==2.3.6
Jinja2==3.1.2
itsdangerous==2.1.2
```

## 联系方式

如有问题，请联系开发者：你的邮箱地址

## 版权信息

© 2023 员工管理系统. 版权所有. 