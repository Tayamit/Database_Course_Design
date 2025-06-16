-- 删除旧表格（如果存在）
IF OBJECT_ID('overtime', 'U') IS NOT NULL DROP TABLE overtime;
IF OBJECT_ID('leaves', 'U') IS NOT NULL DROP TABLE leaves;
IF OBJECT_ID('attendance', 'U') IS NOT NULL DROP TABLE attendance;
IF OBJECT_ID('employees', 'U') IS NOT NULL DROP TABLE employees;
IF OBJECT_ID('departments', 'U') IS NOT NULL DROP TABLE departments;
IF OBJECT_ID('users', 'U') IS NOT NULL DROP TABLE users;

-- 创建部门表
CREATE TABLE departments (
    id INT PRIMARY KEY IDENTITY(1,1),
    name NVARCHAR(100) NOT NULL,
    description NVARCHAR(500),
    created_at DATETIME DEFAULT GETDATE()
);

-- 创建员工表
CREATE TABLE employees (
    id INT PRIMARY KEY IDENTITY(1,1),
    name NVARCHAR(100) NOT NULL,
    gender NVARCHAR(10),
    birth_date DATE,
    email NVARCHAR(100),
    phone NVARCHAR(20),
    address NVARCHAR(255),
    department_id INT,
    position NVARCHAR(100),
    hire_date DATE,
    salary DECIMAL(10, 2),
    status NVARCHAR(20) DEFAULT 'active',
    created_at DATETIME DEFAULT GETDATE(),
    FOREIGN KEY (department_id) REFERENCES departments(id)
);

-- 创建考勤表
CREATE TABLE attendance (
    id INT PRIMARY KEY IDENTITY(1,1),
    employee_id INT,
    date DATE,
    check_in TIME,
    check_out TIME,
    status NVARCHAR(20), -- present, absent, leave, half-day
    overtime_hours DECIMAL(5, 2) DEFAULT 0,
    note NVARCHAR(255),
    FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE
);

-- 创建请假表
CREATE TABLE leaves (
    id INT PRIMARY KEY IDENTITY(1,1),
    employee_id INT,
    start_date DATE,
    end_date DATE,
    days INT,
    leave_type NVARCHAR(20), -- sick, casual, annual, maternity, others
    reason NVARCHAR(500),
    applied_on DATETIME DEFAULT GETDATE(),
    FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE
);

-- 创建加班表
CREATE TABLE overtime (
    id INT PRIMARY KEY IDENTITY(1,1),
    employee_id INT,
    date DATE,
    start_time TIME,
    end_time TIME,
    hours DECIMAL(5, 2),
    reason NVARCHAR(255),
    FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE
);

-- 创建用户表
CREATE TABLE users (
    id INT PRIMARY KEY IDENTITY(1,1),
    username NVARCHAR(50) NOT NULL,
    password_hash NVARCHAR(255) NOT NULL,
    role NVARCHAR(20) DEFAULT 'user', -- admin, manager, user
    remember_token NVARCHAR(255),
    token_expiry DATETIME,
    created_at DATETIME DEFAULT GETDATE()
);

-- 插入示例数据
-- 部门数据
INSERT INTO departments (name, description) VALUES
('人力资源部', '负责公司人员招聘、培训和绩效评估'),
('财务部', '负责公司财务管理和会计工作'),
('研发部', '负责产品研发和技术创新'),
('市场部', '负责产品推广和市场营销'),
('销售部', '负责产品销售和客户关系管理');

-- 员工数据
INSERT INTO employees (name, gender, birth_date, email, phone, address, department_id, position, hire_date, salary, status) VALUES
('张三', '男', '1988-05-15', 'zhangsan@example.com', '13800138001', '北京市海淀区', 1, '人力资源经理', '2018-01-15', 12000.00, 'active'),
('李四', '男', '1990-09-20', 'lisi@example.com', '13800138002', '北京市朝阳区', 2, '财务主管', '2019-03-01', 10000.00, 'active'),
('王五', '男', '1992-07-10', 'wangwu@example.com', '13800138003', '上海市浦东新区', 3, '高级工程师', '2017-11-20', 15000.00, 'active'),
('赵六', '女', '1994-03-25', 'zhaoliu@example.com', '13800138004', '深圳市南山区', 4, '市场专员', '2020-05-10', 8000.00, 'active'),
('钱七', '女', '1991-12-18', 'qianqi@example.com', '13800138005', '广州市天河区', 5, '销售代表', '2019-08-15', 9000.00, 'active'),
('孙八', '男', '1987-02-22', 'sunba@example.com', '13800138006', '北京市西城区', 3, '技术总监', '2016-04-01', 18000.00, 'active'),
('周九', '女', '1993-08-30', 'zhoujiu@example.com', '13800138007', '上海市静安区', 1, '招聘专员', '2020-01-10', 7500.00, 'active'),
('吴十', '男', '1990-11-05', 'wushi@example.com', '13800138008', '深圳市福田区', 5, '销售经理', '2018-07-01', 12000.00, 'active'),
('郑十一', '女', '1995-06-14', 'zhengshiyi@example.com', '13800138009', '广州市越秀区', 4, '市场经理', '2019-09-20', 11000.00, 'active'),
('王十二', '男', '1989-01-08', 'wangshier@example.com', '13800138010', '北京市东城区', 2, '会计', '2020-03-15', 8500.00, 'active');

-- 考勤数据
DECLARE @today DATE = CONVERT(DATE, GETDATE());
DECLARE @yesterday DATE = DATEADD(DAY, -1, @today);
DECLARE @two_days_ago DATE = DATEADD(DAY, -2, @today);

INSERT INTO attendance (employee_id, date, check_in, check_out, status, note) VALUES
(1, @today, '08:30', '18:00', 'present', NULL),
(2, @today, '08:45', '18:15', 'present', NULL),
(3, @today, '08:20', '17:50', 'present', NULL),
(4, @today, '09:00', '17:30', 'present', NULL),
(5, @today, NULL, NULL, 'absent', '未打卡'),
(6, @today, '08:15', '18:30', 'present', NULL),
(7, @today, '08:50', '17:45', 'present', NULL),
(8, @today, '08:40', '18:10', 'present', NULL),
(9, @today, '08:55', '17:30', 'half-day', '下午请假'),
(10, @today, NULL, NULL, 'leave', '病假'),
(1, @yesterday, '08:25', '18:05', 'present', NULL),
(2, @yesterday, '08:50', '18:20', 'present', NULL),
(3, @yesterday, '08:15', '17:55', 'present', NULL),
(4, @yesterday, '09:05', '17:35', 'present', NULL),
(5, @yesterday, '08:45', '18:15', 'present', NULL),
(6, @yesterday, '08:20', '18:25', 'present', NULL),
(7, @yesterday, '08:55', '17:50', 'present', NULL),
(8, @yesterday, '08:35', '18:05', 'present', NULL),
(9, @yesterday, NULL, NULL, 'leave', '年假'),
(10, @yesterday, NULL, NULL, 'leave', '病假'),
(1, @two_days_ago, '08:30', '18:30', 'present', '加班1小时'),
(2, @two_days_ago, '08:40', '18:10', 'present', NULL),
(3, @two_days_ago, '08:25', '17:55', 'present', NULL),
(4, @two_days_ago, '09:10', '17:40', 'present', NULL),
(5, @two_days_ago, '08:50', '18:20', 'present', NULL),
(6, @two_days_ago, '08:15', '19:30', 'present', '加班1.5小时'),
(7, @two_days_ago, '08:45', '17:45', 'present', NULL),
(8, @two_days_ago, '08:30', '18:00', 'present', NULL),
(9, @two_days_ago, '08:55', '17:25', 'half-day', '下午有事'),
(10, @two_days_ago, NULL, NULL, 'leave', '病假');

-- 更新考勤表中的加班时间
UPDATE attendance SET overtime_hours = 1.0 WHERE employee_id = 1 AND date = @two_days_ago;
UPDATE attendance SET overtime_hours = 1.5 WHERE employee_id = 6 AND date = @two_days_ago;

-- 加班数据
INSERT INTO overtime (employee_id, date, start_time, end_time, hours, reason) VALUES
(1, @two_days_ago, '18:00', '19:00', 1.0, '完成月底报表'),
(6, @two_days_ago, '18:00', '19:30', 1.5, '处理紧急技术问题'),
(3, DATEADD(DAY, -5, @today), '18:00', '20:00', 2.0, '项目赶工'),
(8, DATEADD(DAY, -3, @today), '18:00', '19:00', 1.0, '客户会议准备');

-- 请假数据
INSERT INTO leaves (employee_id, start_date, end_date, days, leave_type, reason, applied_on) VALUES
(9, @yesterday, @yesterday, 1, 'annual', '个人事务', DATEADD(DAY, -3, @today)),
(10, @two_days_ago, @today, 3, 'sick', '感冒发烧', DATEADD(DAY, -3, @today)),
(5, DATEADD(DAY, 1, @today), DATEADD(DAY, 5, @today), 5, 'annual', '家庭旅行', @today),
(7, DATEADD(DAY, -10, @today), DATEADD(DAY, -6, @today), 5, 'maternity', '产假', DATEADD(DAY, -15, @today)),
(4, DATEADD(DAY, -8, @today), DATEADD(DAY, -8, @today), 1, 'casual', '办理个人证件', DATEADD(DAY, -10, @today));

-- 用户数据 (密码: 123456)
INSERT INTO users (username, password_hash, role) VALUES
('admin', '$2b$12$tCY.wTANvYEjauR4nUjY3OYp1WXEAVbTlEQrtoTh5m5JA7FmuQ/oO', 'admin'),
('manager', '$2b$12$tCY.wTANvYEjauR4nUjY3OYp1WXEAVbTlEQrtoTh5m5JA7FmuQ/oO', 'manager'),
('user', '$2b$12$tCY.wTANvYEjauR4nUjY3OYp1WXEAVbTlEQrtoTh5m5JA7FmuQ/oO', 'user'); 