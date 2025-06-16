-- 创建数据库
IF NOT EXISTS (SELECT * FROM sys.databases WHERE name = 'EmployeeManagement')
BEGIN
    CREATE DATABASE EmployeeManagement;
END
GO

USE EmployeeManagement;
GO

-- 创建部门表
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'departments')
BEGIN
    CREATE TABLE departments (
        id INT IDENTITY(1,1) PRIMARY KEY,
        name NVARCHAR(100) NOT NULL,
        description NVARCHAR(500),
        created_at DATETIME DEFAULT GETDATE()
    );
END
GO

-- 创建员工表
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'employees')
BEGIN
    CREATE TABLE employees (
        id INT IDENTITY(1,1) PRIMARY KEY,
        name NVARCHAR(100) NOT NULL,
        email NVARCHAR(100) UNIQUE,
        phone NVARCHAR(20),
        department_id INT FOREIGN KEY REFERENCES departments(id),
        position NVARCHAR(100),
        salary DECIMAL(10, 2),
        hire_date DATETIME,
        created_at DATETIME DEFAULT GETDATE(),
        updated_at DATETIME DEFAULT GETDATE()
    );
END
GO

-- 创建用户表
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'users')
BEGIN
    CREATE TABLE users (
        id INT IDENTITY(1,1) PRIMARY KEY,
        username NVARCHAR(50) UNIQUE NOT NULL,
        password NVARCHAR(100) NOT NULL,
        full_name NVARCHAR(100),
        email NVARCHAR(100),
        role NVARCHAR(20) CHECK (role IN ('admin', 'manager', 'user')),
        created_at DATETIME DEFAULT GETDATE()
    );
END
GO

-- 创建考勤表
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'attendance')
BEGIN
    CREATE TABLE attendance (
        id INT IDENTITY(1,1) PRIMARY KEY,
        employee_id INT FOREIGN KEY REFERENCES employees(id),
        date DATE,
        check_in TIME,
        check_out TIME,
        status NVARCHAR(20) CHECK (status IN ('present', 'absent', 'half-day', 'leave')),
        note NVARCHAR(200)
    );
END
GO

-- 创建请假表
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'leaves')
BEGIN
    CREATE TABLE leaves (
        id INT IDENTITY(1,1) PRIMARY KEY,
        employee_id INT FOREIGN KEY REFERENCES employees(id),
        start_date DATE,
        end_date DATE,
        leave_type NVARCHAR(50) CHECK (leave_type IN ('sick', 'casual', 'annual', 'maternity', 'others')),
        reason NVARCHAR(500),
        status NVARCHAR(20) CHECK (status IN ('pending', 'approved', 'rejected')),
        applied_on DATETIME DEFAULT GETDATE()
    );
END
GO

-- 创建工资单表
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'payrolls')
BEGIN
    CREATE TABLE payrolls (
        id INT IDENTITY(1,1) PRIMARY KEY,
        employee_id INT FOREIGN KEY REFERENCES employees(id),
        salary_month DATE,
        basic_salary DECIMAL(10, 2),
        allowances DECIMAL(10, 2),
        deductions DECIMAL(10, 2),
        total_salary DECIMAL(10, 2),
        payment_date DATETIME,
        status NVARCHAR(20) CHECK (status IN ('pending', 'paid')),
        created_at DATETIME DEFAULT GETDATE()
    );
END
GO

-- 插入默认数据
-- 1. 添加部门
IF NOT EXISTS (SELECT * FROM departments)
BEGIN
    INSERT INTO departments (name, description) VALUES 
    (N'技术部', N'负责公司的技术研发和产品实现'),
    (N'销售部', N'负责公司产品的销售和客户管理'),
    (N'人力资源部', N'负责公司的人员招聘、培训和管理'),
    (N'财务部', N'负责公司的财务管理和预算控制'),
    (N'行政部', N'负责公司的日常行政事务管理');
END
GO

-- 2. 添加管理员用户
IF NOT EXISTS (SELECT * FROM users)
BEGIN
    INSERT INTO users (username, password, full_name, email, role) VALUES 
    ('admin', 'admin123', N'系统管理员', 'admin@company.com', 'admin'),
    ('manager', 'manager123', N'部门经理', 'manager@company.com', 'manager');
END
GO

-- 3. 添加示例员工
IF NOT EXISTS (SELECT * FROM employees)
BEGIN
    INSERT INTO employees (name, email, phone, department_id, position, salary, hire_date) VALUES 
    (N'张三', 'zhangsan@company.com', '13800138001', 1, N'高级开发工程师', 15000.00, '2021-01-15'),
    (N'李四', 'lisi@company.com', '13800138002', 1, N'前端开发工程师', 12000.00, '2021-03-20'),
    (N'王五', 'wangwu@company.com', '13800138003', 2, N'销售经理', 13000.00, '2020-11-05'),
    (N'赵六', 'zhaoliu@company.com', '13800138004', 3, N'人力资源专员', 9000.00, '2022-02-18'),
    (N'孙七', 'sunqi@company.com', '13800138005', 4, N'财务主管', 11000.00, '2021-07-10');
END
GO 