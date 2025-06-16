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
        overtime_hours DECIMAL(4, 2) DEFAULT 0, -- 加班小时数
        status NVARCHAR(20) CHECK (status IN ('present', 'absent', 'half-day', 'leave')),
        note NVARCHAR(200)
    );
END
ELSE
BEGIN
    -- 检查是否已有overtime_hours列，如果没有则添加
    IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('attendance') AND name = 'overtime_hours')
    BEGIN
        ALTER TABLE attendance ADD overtime_hours DECIMAL(4, 2) DEFAULT 0;
    END
END
GO

-- 创建加班信息表
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'overtime')
BEGIN
    CREATE TABLE overtime (
        id INT IDENTITY(1,1) PRIMARY KEY,
        employee_id INT FOREIGN KEY REFERENCES employees(id),
        date DATE,
        start_time TIME,
        end_time TIME,
        hours DECIMAL(4, 2), -- 加班小时数
        reason NVARCHAR(500),
        status NVARCHAR(20) CHECK (status IN ('pending', 'approved', 'rejected')),
        approved_by INT, -- 批准人ID
        approved_at DATETIME, -- 批准时间
        created_at DATETIME DEFAULT GETDATE()
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
        days DECIMAL(5, 2), -- 请假天数
        leave_type NVARCHAR(50) CHECK (leave_type IN ('sick', 'casual', 'annual', 'maternity', 'others')),
        reason NVARCHAR(500),
        status NVARCHAR(20) CHECK (status IN ('pending', 'approved', 'rejected')),
        approved_by INT, -- 批准人ID
        approved_at DATETIME, -- 批准时间
        applied_on DATETIME DEFAULT GETDATE()
    );
END
ELSE 
BEGIN
    -- 检查是否已有approved_by和approved_at列，如果没有则添加
    IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('leaves') AND name = 'approved_by')
    BEGIN
        ALTER TABLE leaves ADD approved_by INT;
    END
    
    IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('leaves') AND name = 'approved_at')
    BEGIN
        ALTER TABLE leaves ADD approved_at DATETIME;
    END
    
    IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('leaves') AND name = 'days')
    BEGIN
        ALTER TABLE leaves ADD days DECIMAL(5, 2);
    END
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
    (N'行政部', N'负责公司的日常行政事务管理'),
    (N'市场部', N'负责公司的市场推广和品牌建设'),
    (N'客服部', N'负责客户服务和售后支持');
END
GO

-- 2. 添加管理员用户
IF NOT EXISTS (SELECT * FROM users)
BEGIN
    INSERT INTO users (username, password, full_name, email, role) VALUES 
    ('admin', 'admin123', N'系统管理员', 'admin@company.com', 'admin'),
    ('manager', 'manager123', N'部门经理', 'manager@company.com', 'manager'),
    ('user1', 'user123', N'普通用户', 'user1@company.com', 'user'),
    ('hr', 'hr123', N'人力资源', 'hr@company.com', 'manager');
END
GO

-- 3. 添加示例员工
IF NOT EXISTS (SELECT * FROM employees WHERE id <= 5)
BEGIN
    INSERT INTO employees (name, email, phone, department_id, position, salary, hire_date) VALUES 
    (N'张三', 'zhangsan@company.com', '13800138001', 1, N'高级开发工程师', 15000.00, '2021-01-15'),
    (N'李四', 'lisi@company.com', '13800138002', 1, N'前端开发工程师', 12000.00, '2021-03-20'),
    (N'王五', 'wangwu@company.com', '13800138003', 2, N'销售经理', 13000.00, '2020-11-05'),
    (N'赵六', 'zhaoliu@company.com', '13800138004', 3, N'人力资源专员', 9000.00, '2022-02-18'),
    (N'孙七', 'sunqi@company.com', '13800138005', 4, N'财务主管', 11000.00, '2021-07-10');
END
GO

-- 添加更多员工
IF NOT EXISTS (SELECT * FROM employees WHERE id > 5)
BEGIN
    INSERT INTO employees (name, email, phone, department_id, position, salary, hire_date) VALUES
    (N'周八', 'zhouba@company.com', '13800138006', 5, N'行政主管', 10000.00, '2021-09-12'),
    (N'吴九', 'wujiu@company.com', '13800138007', 1, N'测试工程师', 11000.00, '2022-01-10'),
    (N'郑十', 'zhengshi@company.com', '13800138008', 2, N'销售代表', 9000.00, '2022-03-15'),
    (N'刘一', 'liuyi@company.com', '13800138009', 6, N'市场专员', 8500.00, '2022-04-20'),
    (N'陈二', 'chener@company.com', '13800138010', 7, N'客服专员', 7500.00, '2022-05-05'),
    (N'杨十一', 'yangshiyi@company.com', '13800138011', 1, N'后端开发工程师', 13000.00, '2021-12-01'),
    (N'黄十二', 'huangshier@company.com', '13800138012', 3, N'培训专员', 9500.00, '2022-02-28'),
    (N'赵十三', 'zhaoshisan@company.com', '13800138013', 4, N'会计', 8500.00, '2022-06-10'),
    (N'徐十四', 'xushisi@company.com', '13800138014', 5, N'行政助理', 7000.00, '2022-06-15'),
    (N'朱十五', 'zhushiwu@company.com', '13800138015', 6, N'市场分析师', 12000.00, '2021-08-20');
END
GO

-- 4. 添加示例考勤记录(如果表为空)
DELETE FROM attendance;
INSERT INTO attendance (employee_id, date, check_in, check_out, overtime_hours, status, note) VALUES
-- 一周的考勤记录示例
-- 张三
(1, '2023-06-01', '08:30', '17:30', 0, 'present', N'正常出勤'),
(1, '2023-06-02', '08:20', '19:30', 2, 'present', N'项目加班'),
(1, '2023-06-03', NULL, NULL, 0, 'absent', N'未打卡'),
(1, '2023-06-04', '08:45', '17:45', 0, 'present', N'正常出勤'),
(1, '2023-06-05', '08:30', '18:00', 0.5, 'present', N'略有加班'),
-- 李四
(2, '2023-06-01', '08:15', '17:45', 0.5, 'present', N'正常出勤'),
(2, '2023-06-02', '08:30', '17:30', 0, 'present', N'正常出勤'),
(2, '2023-06-03', '09:00', '18:00', 0, 'half-day', N'下午请假'),
(2, '2023-06-04', NULL, NULL, 0, 'leave', N'全天请假'),
(2, '2023-06-05', '08:30', '17:30', 0, 'present', N'正常出勤'),
-- 王五
(3, '2023-06-01', '09:00', '18:00', 0, 'present', N'正常出勤'),
(3, '2023-06-02', '09:10', '18:10', 0, 'present', N'正常出勤'),
(3, '2023-06-03', '09:00', '18:30', 0.5, 'present', N'客户会议加班'),
(3, '2023-06-04', '09:00', '18:00', 0, 'present', N'正常出勤'),
(3, '2023-06-05', '09:15', '18:00', 0, 'present', N'正常出勤'),
-- 更多员工的当前日期考勤
(4, CONVERT(DATE, GETDATE()), '08:40', '17:40', 0, 'present', N'正常出勤'),
(5, CONVERT(DATE, GETDATE()), '08:30', '17:30', 0, 'present', N'正常出勤'),
(6, CONVERT(DATE, GETDATE()), '08:45', '18:30', 1, 'present', N'部门会议加班'),
(7, CONVERT(DATE, GETDATE()), '08:25', '17:30', 0, 'present', N'正常出勤'),
(8, CONVERT(DATE, GETDATE()), '09:00', NULL, 0, 'half-day', N'下午请假'),
(9, CONVERT(DATE, GETDATE()), NULL, NULL, 0, 'leave', N'病假'),
(10, CONVERT(DATE, GETDATE()), '08:50', '17:30', 0, 'present', N'正常出勤');
GO

-- 5. 添加示例加班记录
DELETE FROM overtime;
INSERT INTO overtime (employee_id, date, start_time, end_time, hours, reason, status, approved_by, approved_at) VALUES
-- 已审批的加班记录
(1, '2023-06-02', '18:00', '20:00', 2, N'项目紧急需求开发', 'approved', 1, '2023-06-01 14:30'),
(2, '2023-06-01', '18:00', '19:30', 1.5, N'修复系统Bug', 'approved', 1, '2023-06-01 14:35'),
(3, '2023-06-03', '18:00', '20:00', 2, N'客户会议准备', 'approved', 1, '2023-06-02 16:00'),
-- 待审批的加班记录
(4, '2023-06-05', '18:00', '19:30', 1.5, N'月底报表统计', 'pending', NULL, NULL),
(5, '2023-06-05', '18:00', '20:30', 2.5, N'财务系统维护', 'pending', NULL, NULL),
-- 已拒绝的加班记录
(6, '2023-06-04', '18:00', '19:00', 1, N'整理办公室文件', 'rejected', 1, '2023-06-03 15:30'),
-- 更多加班记录
(7, CONVERT(DATE, GETDATE()), '18:00', '20:00', 2, N'紧急系统维护', 'pending', NULL, NULL),
(8, CONVERT(DATE, GETDATE()), '18:00', '21:00', 3, N'销售月底总结', 'pending', NULL, NULL),
(1, CONVERT(DATE, GETDATE()), '18:00', '19:30', 1.5, N'版本发布准备', 'pending', NULL, NULL),
(3, DATEADD(DAY, -1, CONVERT(DATE, GETDATE())), '18:00', '20:30', 2.5, N'客户紧急需求', 'approved', 1, DATEADD(DAY, -1, GETDATE()));
GO

-- 6. 添加示例请假记录
DELETE FROM leaves;
INSERT INTO leaves (employee_id, start_date, end_date, days, leave_type, reason, status, approved_by, approved_at, applied_on) VALUES
-- 已批准的请假
(2, '2023-06-04', '2023-06-04', 1, 'sick', N'感冒发烧', 'approved', 1, '2023-06-03 10:30', '2023-06-03 09:00'),
(8, '2023-06-03', '2023-06-03', 0.5, 'casual', N'个人事务', 'approved', 1, '2023-06-02 16:45', '2023-06-02 14:30'),
-- 待批准的请假
(9, '2023-06-05', '2023-06-07', 3, 'sick', N'需要住院治疗', 'pending', NULL, NULL, '2023-06-05 08:30'),
(4, DATEADD(DAY, 1, CONVERT(DATE, GETDATE())), DATEADD(DAY, 2, CONVERT(DATE, GETDATE())), 2, 'annual', N'家庭旅行', 'pending', NULL, NULL, GETDATE()),
-- 已拒绝的请假
(5, '2023-06-10', '2023-06-12', 3, 'casual', N'个人事务', 'rejected', 1, '2023-06-08 11:20', '2023-06-08 09:15'),
-- 更多请假记录
(10, DATEADD(DAY, 5, CONVERT(DATE, GETDATE())), DATEADD(DAY, 7, CONVERT(DATE, GETDATE())), 3, 'annual', N'计划休假', 'pending', NULL, NULL, GETDATE()),
(3, DATEADD(DAY, 3, CONVERT(DATE, GETDATE())), DATEADD(DAY, 3, CONVERT(DATE, GETDATE())), 1, 'sick', N'牙医预约', 'pending', NULL, NULL, DATEADD(DAY, -1, GETDATE())),
(7, DATEADD(DAY, -10, CONVERT(DATE, GETDATE())), DATEADD(DAY, -8, CONVERT(DATE, GETDATE())), 3, 'others', N'参加培训', 'approved', 1, DATEADD(DAY, -12, GETDATE()), DATEADD(DAY, -12, GETDATE()));
GO 