from flask import Flask, render_template, request, redirect, url_for, jsonify, session, flash
import pyodbc
import os
from datetime import datetime, timedelta
from functools import wraps
import calendar

app = Flask(__name__)
app.secret_key = os.urandom(24)
# 设置永久会话的过期时间为15天
app.permanent_session_lifetime = timedelta(days=15)

# 数据库连接
def get_db_connection():
    conn = pyodbc.connect('DRIVER={ODBC Driver 17 for SQL Server};'
                          'SERVER=LAPTOP-DH58L4N7\SQLSERVER;'
                          'DATABASE=EmployeeManagement;'
                          'UID=sa;'
                          'PWD=12345678;'
                          'Trusted_Connection=yes;')
    return conn

# 添加上下文处理器，为所有模板提供now变量
@app.context_processor
def inject_now():
    return {'now': datetime.now()}

# 登录验证装饰器
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('请先登录', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# 首页
@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('login.html')

# 登录
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        remember = 'remember' in request.form
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, role FROM users WHERE username = ? AND password = ?", 
                      (username, password))
        user = cursor.fetchone()
        conn.close()
        
        if user:
            session['user_id'] = user[0]
            session['username'] = user[1]
            session['role'] = user[2]
            
            # 如果用户勾选了"记住我"，设置会话的永久性
            if remember:
                session.permanent = True
                
            flash('登录成功！欢迎回来，' + user[1], 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('用户名或密码错误', 'danger')
    
    return render_template('login.html')

# 退出登录
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# 仪表盘
@app.route('/dashboard')
@login_required
def dashboard():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 获取员工数量
    cursor.execute("SELECT COUNT(*) FROM employees")
    employee_count = cursor.fetchone()[0]
    
    # 获取部门数量
    cursor.execute("SELECT COUNT(*) FROM departments")
    department_count = cursor.fetchone()[0]
    
    # 获取当天日期
    today = datetime.now().strftime('%Y-%m-%d')
    
    # 获取当天出勤数据
    cursor.execute("""
        SELECT 
            COUNT(CASE WHEN status = 'present' THEN 1 END) AS present_count,
            COUNT(CASE WHEN status = 'absent' THEN 1 END) AS absent_count,
            COUNT(CASE WHEN status = 'leave' THEN 1 END) AS leave_count,
            COUNT(CASE WHEN status = 'half-day' THEN 1 END) AS half_day_count,
            SUM(overtime_hours) AS total_overtime_hours
        FROM attendance 
        WHERE date = ?
    """, today)
    
    attendance_stats = cursor.fetchone()
    present_count = attendance_stats[0] if attendance_stats[0] else 0
    absent_count = attendance_stats[1] if attendance_stats[1] else 0
    leave_count = attendance_stats[2] if attendance_stats[2] else 0
    half_day_count = attendance_stats[3] if attendance_stats[3] else 0
    overtime_hours = attendance_stats[4] if attendance_stats[4] else 0
    
    # 使用员工总数作为分母计算出勤率
    attendance_rate = (present_count * 100.0 / employee_count) if employee_count > 0 else 0
    
    # 获取最近添加的员工
    cursor.execute("""
        SELECT TOP 10 e.id, e.name, d.name as department, e.position, e.hire_date
        FROM employees e
        JOIN departments d ON e.department_id = d.id
        ORDER BY e.hire_date DESC
    """)
    recent_employees = cursor.fetchall()
    
    # 获取部门人员分布数据
    cursor.execute("""
        SELECT d.name, COUNT(e.id) as employee_count
        FROM departments d
        LEFT JOIN employees e ON d.id = e.department_id
        GROUP BY d.name
        ORDER BY employee_count DESC
    """)
    department_distribution = cursor.fetchall()
    
    # 获取本周出勤情况数据
    # 计算本周的开始日期和结束日期
    today_date = datetime.now()
    start_of_week = (today_date - timedelta(days=today_date.weekday())).strftime('%Y-%m-%d')
    end_of_week = (today_date + timedelta(days=6-today_date.weekday())).strftime('%Y-%m-%d')
    
    # 获取本周每天的出勤数据
    week_days = []
    week_attendance = []
    current_date = today_date - timedelta(days=today_date.weekday())  # 本周一
    
    # 星期几的中文映射
    weekday_map = {
        0: "周一",
        1: "周二",
        2: "周三",
        3: "周四",
        4: "周五",
        5: "周六",
        6: "周日"
    }
    
    for i in range(5):  # 本周一到周五
        if current_date <= today_date:  # 只计算到今天
            day_str = current_date.strftime('%Y-%m-%d')
            week_days.append(weekday_map[current_date.weekday()])  # 中文星期几
            
            # 查询当天出勤人数
            cursor.execute("""
                SELECT COUNT(*) FROM attendance 
                WHERE date = ? AND status = 'present'
            """, (day_str,))
            day_present = cursor.fetchone()[0]
            week_attendance.append(day_present)
        
        current_date += timedelta(days=1)
    
    conn.close()
    
    return render_template('dashboard.html', 
                          employee_count=employee_count,
                          department_count=department_count,
                          attendance_rate=attendance_rate,
                          present_count=present_count,
                          absent_count=absent_count,
                          leave_count=leave_count,
                          half_day_count=half_day_count,
                          overtime_hours=overtime_hours,
                          recent_employees=recent_employees,
                          department_distribution=department_distribution,
                          week_days=week_days,
                          week_attendance=week_attendance)

# 员工管理
@app.route('/employees')
@login_required
def employees():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT e.id, e.name, e.email, e.phone, e.hire_date, 
               d.name as department, e.position, e.salary
        FROM employees e
        JOIN departments d ON e.department_id = d.id
        ORDER BY e.id
    """)
    employees = cursor.fetchall()
    
    cursor.execute("SELECT id, name FROM departments")
    departments = cursor.fetchall()
    
    conn.close()
    
    return render_template('employees.html', 
                          employees=employees,
                          departments=departments)

# 添加员工
@app.route('/employees/add', methods=['POST'])
@login_required
def add_employee():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        department_id = request.form['department_id']
        position = request.form['position']
        salary = request.form['salary']
        hire_date = datetime.now()
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO employees (name, email, phone, department_id, position, salary, hire_date)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (name, email, phone, department_id, position, salary, hire_date))
        conn.commit()
        conn.close()
        
        flash('员工添加成功', 'success')
    
    return redirect(url_for('employees'))

# 编辑员工
@app.route('/employees/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_employee(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        department_id = request.form['department_id']
        position = request.form['position']
        salary = request.form['salary']
        
        cursor.execute("""
            UPDATE employees
            SET name = ?, email = ?, phone = ?, department_id = ?, position = ?, salary = ?
            WHERE id = ?
        """, (name, email, phone, department_id, position, salary, id))
        conn.commit()
        
        flash('员工信息更新成功', 'success')
        return redirect(url_for('employees'))
    
    cursor.execute("SELECT * FROM employees WHERE id = ?", (id,))
    employee = cursor.fetchone()
    
    cursor.execute("SELECT id, name FROM departments")
    departments = cursor.fetchall()
    
    # 获取员工考勤信息
    # 本月出勤天数
    cursor.execute("""
        SELECT COUNT(*) FROM attendance 
        WHERE employee_id = ? AND status = 'present' 
        AND MONTH(date) = MONTH(GETDATE()) AND YEAR(date) = YEAR(GETDATE())
    """, (id,))
    present_days = cursor.fetchone()[0]
    
    # 本月请假天数
    cursor.execute("""
        SELECT COUNT(*) FROM attendance 
        WHERE employee_id = ? AND status = 'leave' 
        AND MONTH(date) = MONTH(GETDATE()) AND YEAR(date) = YEAR(GETDATE())
    """, (id,))
    leave_days = cursor.fetchone()[0]
    
    # 本月缺勤天数
    cursor.execute("""
        SELECT COUNT(*) FROM attendance 
        WHERE employee_id = ? AND status = 'absent' 
        AND MONTH(date) = MONTH(GETDATE()) AND YEAR(date) = YEAR(GETDATE())
    """, (id,))
    absent_days = cursor.fetchone()[0]
    
    # 计算考勤率
    # 获取当前月的工作日总数（简化处理，以本月当前天数为准）
    today = datetime.today()
    _, days_in_month = calendar.monthrange(today.year, today.month)
    current_day = min(today.day, days_in_month)
    
    # 考勤率 = 出勤天数 / 当前月已过天数
    attendance_rate = round((present_days * 100.0 / current_day) if current_day > 0 else 0, 1)
    
    conn.close()
    
    return render_template('edit_employee.html', 
                          employee=employee,
                          departments=departments,
                          present_days=present_days,
                          leave_days=leave_days,
                          absent_days=absent_days,
                          attendance_rate=attendance_rate)

# 删除员工
@app.route('/employees/delete/<int:id>')
@login_required
def delete_employee(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # 开始事务
        conn.autocommit = False
        
        # 先删除该员工的考勤记录
        cursor.execute("DELETE FROM attendance WHERE employee_id = ?", (id,))
        
        # 删除该员工的加班记录
        cursor.execute("DELETE FROM overtime WHERE employee_id = ?", (id,))
        
        # 删除该员工的请假记录
        cursor.execute("DELETE FROM leaves WHERE employee_id = ?", (id,))
        
        # 最后删除员工
        cursor.execute("DELETE FROM employees WHERE id = ?", (id,))
        
        # 提交事务
        conn.commit()
        flash('员工删除成功', 'success')
        
    except Exception as e:
        # 发生错误时回滚事务
        conn.rollback()
        flash(f'删除失败: {str(e)}', 'danger')
        
    finally:
        # 恢复自动提交并关闭连接
        conn.autocommit = True
        conn.close()
    
    return redirect(url_for('employees'))

# 部门管理
@app.route('/departments')
@login_required
def departments():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM departments")
    departments = cursor.fetchall()
    
    # 获取每个部门的员工数量
    dept_employee_counts = {}
    for dept in departments:
        cursor.execute("SELECT COUNT(*) FROM employees WHERE department_id = ?", (dept[0],))
        count = cursor.fetchone()[0]
        dept_employee_counts[dept[0]] = count
    
    conn.close()
    
    return render_template('departments.html', departments=departments, 
                          dept_employee_counts=dept_employee_counts)

# 查看部门员工
@app.route('/departments/<int:id>/employees')
@login_required
def department_employees(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 获取部门信息
    cursor.execute("SELECT * FROM departments WHERE id = ?", (id,))
    department = cursor.fetchone()
    
    if not department:
        flash('部门不存在', 'danger')
        return redirect(url_for('departments'))
    
    # 获取该部门的所有员工
    cursor.execute("""
        SELECT e.id, e.name, e.email, e.phone, e.hire_date, e.position, e.salary
        FROM employees e
        WHERE e.department_id = ?
        ORDER BY e.id
    """, (id,))
    employees = cursor.fetchall()
    
    # 获取所有员工总数，用于计算部门占比
    cursor.execute("SELECT COUNT(*) FROM employees")
    department_total_employees = cursor.fetchone()[0]
    
    conn.close()
    
    return render_template('department_employees.html', 
                          department=department, 
                          employees=employees,
                          department_total_employees=department_total_employees)

# 添加部门
@app.route('/departments/add', methods=['POST'])
@login_required
def add_department():
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO departments (name, description)
            VALUES (?, ?)
        """, (name, description))
        conn.commit()
        conn.close()
        
        flash('部门添加成功', 'success')
    
    return redirect(url_for('departments'))

# 编辑部门
@app.route('/departments/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_department(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        
        cursor.execute("""
            UPDATE departments
            SET name = ?, description = ?
            WHERE id = ?
        """, (name, description, id))
        conn.commit()
        
        flash('部门信息更新成功', 'success')
        return redirect(url_for('departments'))
    
    cursor.execute("SELECT * FROM departments WHERE id = ?", (id,))
    department = cursor.fetchone()
    
    # 获取该部门的所有员工
    cursor.execute("""
        SELECT e.id, e.name, e.position, e.hire_date
        FROM employees e
        WHERE e.department_id = ?
        ORDER BY e.hire_date DESC
    """, (id,))
    employees = cursor.fetchall()
    
    # 获取该部门的员工数量
    cursor.execute("SELECT COUNT(*) FROM employees WHERE department_id = ?", (id,))
    employee_count = cursor.fetchone()[0]
    
    # 获取该部门的平均薪资
    cursor.execute("SELECT AVG(salary) FROM employees WHERE department_id = ?", (id,))
    avg_salary = cursor.fetchone()[0]
    if avg_salary is None:
        avg_salary = 0
    
    conn.close()
    
    return render_template('edit_department.html', 
                          department=department,
                          department_employees=employees,
                          employee_count=employee_count,
                          avg_salary=avg_salary)

# 删除部门
@app.route('/departments/delete/<int:id>')
@login_required
def delete_department(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 检查部门是否有员工
    cursor.execute("SELECT COUNT(*) FROM employees WHERE department_id = ?", (id,))
    count = cursor.fetchone()[0]
    
    if count > 0:
        flash('无法删除部门，该部门下有员工', 'danger')
    else:
        cursor.execute("DELETE FROM departments WHERE id = ?", (id,))
        conn.commit()
        flash('部门删除成功', 'success')
    
    conn.close()
    return redirect(url_for('departments'))

# 考勤管理
@app.route('/attendance')
@login_required
def attendance():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 获取所有考勤记录
    cursor.execute("""
        SELECT a.id, e.name, a.date, a.check_in, a.check_out, a.overtime_hours, a.status, a.note
        FROM attendance a
        JOIN employees e ON a.employee_id = e.id
        ORDER BY a.date DESC, e.name
    """)
    attendances = cursor.fetchall()
    
    # 获取所有员工
    cursor.execute("SELECT id, name FROM employees")
    employees = cursor.fetchall()
    
    # 获取员工总数（用于计算出勤率）
    cursor.execute("SELECT COUNT(*) FROM employees")
    total_employees = cursor.fetchone()[0]
    
    # 获取今日日期
    today = datetime.now().strftime('%Y-%m-%d')
    
    # 获取当天考勤统计数据
    cursor.execute("""
        SELECT 
            COUNT(CASE WHEN status = 'present' THEN 1 END) AS present_count,
            COUNT(CASE WHEN status = 'absent' THEN 1 END) AS absent_count,
            COUNT(CASE WHEN status = 'leave' THEN 1 END) AS leave_count,
            COUNT(CASE WHEN status = 'half-day' THEN 1 END) AS half_day_count
        FROM attendance
        WHERE date = ?
    """, today)
    daily_stats = cursor.fetchone()
    daily_present = daily_stats[0] if daily_stats and daily_stats[0] else 0
    daily_absent = daily_stats[1] if daily_stats and daily_stats[1] else 0
    daily_leave = daily_stats[2] if daily_stats and daily_stats[2] else 0
    daily_half_day = daily_stats[3] if daily_stats and daily_stats[3] else 0
    
    # 获取本周考勤统计数据
    # 计算本周的开始日期和结束日期
    today_date = datetime.now()
    start_of_week = (today_date - timedelta(days=today_date.weekday())).strftime('%Y-%m-%d')
    end_of_week = (today_date + timedelta(days=6-today_date.weekday())).strftime('%Y-%m-%d')
    
    # 获取本周每天的出勤数据
    week_dates = []
    current_date = today_date - timedelta(days=today_date.weekday())  # 本周一
    for i in range(7):  # 本周一到周日
        if current_date <= today_date:  # 只计算到今天
            week_dates.append(current_date.strftime('%Y-%m-%d'))
        current_date += timedelta(days=1)
    
    # 初始化本周统计数据
    weekly_present = 0
    weekly_absent = 0
    weekly_leave = 0
    weekly_half_day = 0
    weekly_attendance_sum = 0
    days_counted = 0
    
    # 遍历本周每一天，获取出勤数据
    for date in week_dates:
        cursor.execute("""
            SELECT 
                COUNT(CASE WHEN status = 'present' THEN 1 END) AS present_count,
                COUNT(CASE WHEN status = 'absent' THEN 1 END) AS absent_count,
                COUNT(CASE WHEN status = 'leave' THEN 1 END) AS leave_count,
                COUNT(CASE WHEN status = 'half-day' THEN 1 END) AS half_day_count
            FROM attendance
            WHERE date = ?
        """, date)
        
        day_stats = cursor.fetchone()
        day_present = day_stats[0] if day_stats and day_stats[0] else 0
        day_absent = day_stats[1] if day_stats and day_stats[1] else 0
        day_leave = day_stats[2] if day_stats and day_stats[2] else 0
        day_half_day = day_stats[3] if day_stats and day_stats[3] else 0
        
        # 累加各项数据
        weekly_present += day_present
        weekly_absent += day_absent
        weekly_leave += day_leave
        weekly_half_day += day_half_day
        
        # 计算当天出勤率并累加
        if total_employees > 0:
            day_attendance_rate = day_present * 100.0 / total_employees
            weekly_attendance_sum += day_attendance_rate
        
        days_counted += 1
    
    # 获取本月考勤统计数据
    # 计算本月的开始日期和结束日期
    start_of_month = datetime(today_date.year, today_date.month, 1).strftime('%Y-%m-%d')
    if today_date.month == 12:
        end_of_month = datetime(today_date.year + 1, 1, 1) - timedelta(days=1)
    else:
        end_of_month = datetime(today_date.year, today_date.month + 1, 1) - timedelta(days=1)
    end_of_month = end_of_month.strftime('%Y-%m-%d')
    
    # 获取本月每天的出勤数据
    month_dates = []
    current_date = datetime(today_date.year, today_date.month, 1)  # 本月第一天
    while current_date <= today_date:  # 只计算到今天
        month_dates.append(current_date.strftime('%Y-%m-%d'))
        current_date += timedelta(days=1)
    
    # 初始化本月统计数据
    monthly_present = 0
    monthly_absent = 0
    monthly_leave = 0
    monthly_half_day = 0
    monthly_attendance_sum = 0
    monthly_days_counted = 0
    
    # 遍历本月每一天，获取出勤数据
    for date in month_dates:
        cursor.execute("""
            SELECT 
                COUNT(CASE WHEN status = 'present' THEN 1 END) AS present_count,
                COUNT(CASE WHEN status = 'absent' THEN 1 END) AS absent_count,
                COUNT(CASE WHEN status = 'leave' THEN 1 END) AS leave_count,
                COUNT(CASE WHEN status = 'half-day' THEN 1 END) AS half_day_count
            FROM attendance
            WHERE date = ?
        """, date)
        
        day_stats = cursor.fetchone()
        day_present = day_stats[0] if day_stats and day_stats[0] else 0
        day_absent = day_stats[1] if day_stats and day_stats[1] else 0
        day_leave = day_stats[2] if day_stats and day_stats[2] else 0
        day_half_day = day_stats[3] if day_stats and day_stats[3] else 0
        
        # 累加各项数据
        monthly_present += day_present
        monthly_absent += day_absent
        monthly_leave += day_leave
        monthly_half_day += day_half_day
        
        # 计算当天出勤率并累加
        if total_employees > 0:
            day_attendance_rate = day_present * 100.0 / total_employees
            monthly_attendance_sum += day_attendance_rate
        
        monthly_days_counted += 1
    
    # 计算日出勤率（使用出勤人数除以员工总数）
    if total_employees > 0:
        daily_attendance_rate = round(daily_present * 100.0 / total_employees, 1)
        daily_absent_rate = round(daily_absent * 100.0 / total_employees, 1)
        daily_leave_rate = round(daily_leave * 100.0 / total_employees, 1)
        daily_half_day_rate = round(daily_half_day * 100.0 / total_employees, 1)
    else:
        daily_attendance_rate = daily_absent_rate = daily_leave_rate = daily_half_day_rate = 0
    
    daily_rates = (daily_attendance_rate, daily_absent_rate, daily_leave_rate, daily_half_day_rate)
    
    # 计算周出勤率（使用每天出勤率的平均值）
    weekly_attendance_rate = round(weekly_attendance_sum / days_counted, 1) if days_counted > 0 else 0
    # 计算周其他率（使用累计数据除以员工总数和天数）
    weekly_absent_rate = round(weekly_absent * 100.0 / (total_employees * days_counted), 1) if total_employees > 0 and days_counted > 0 else 0
    weekly_leave_rate = round(weekly_leave * 100.0 / (total_employees * days_counted), 1) if total_employees > 0 and days_counted > 0 else 0
    weekly_half_day_rate = round(weekly_half_day * 100.0 / (total_employees * days_counted), 1) if total_employees > 0 and days_counted > 0 else 0
    weekly_rates = (weekly_attendance_rate, weekly_absent_rate, weekly_leave_rate, weekly_half_day_rate)
    
    # 计算月出勤率（使用每天出勤率的平均值）
    monthly_attendance_rate = round(monthly_attendance_sum / monthly_days_counted, 1) if monthly_days_counted > 0 else 0
    # 计算月其他率（使用累计数据除以员工总数和天数）
    monthly_absent_rate = round(monthly_absent * 100.0 / (total_employees * monthly_days_counted), 1) if total_employees > 0 and monthly_days_counted > 0 else 0
    monthly_leave_rate = round(monthly_leave * 100.0 / (total_employees * monthly_days_counted), 1) if total_employees > 0 and monthly_days_counted > 0 else 0
    monthly_half_day_rate = round(monthly_half_day * 100.0 / (total_employees * monthly_days_counted), 1) if total_employees > 0 and monthly_days_counted > 0 else 0
    monthly_rates = (monthly_attendance_rate, monthly_absent_rate, monthly_leave_rate, monthly_half_day_rate)
    
    # 获取最近四周加班统计数据
    cursor.execute("""
        SELECT 
            DATEPART(week, date) AS week_number,
            SUM(overtime_hours) AS total_hours
        FROM attendance
        WHERE overtime_hours > 0 
          AND date >= DATEADD(day, -28, GETDATE())
        GROUP BY DATEPART(week, date)
        ORDER BY week_number
    """)
    overtime_stats = cursor.fetchall()
    
    # 获取最近30天加班总时长
    cursor.execute("""
        SELECT SUM(overtime_hours)
        FROM attendance
        WHERE date >= DATEADD(day, -30, GETDATE())
    """)
    result = cursor.fetchone()
    total_overtime_hours = round(result[0], 1) if result[0] else 0
    
    # 准备加班数据
    weeks = []
    overtime_hours = []
    
    # 获取当前周数
    current_week = datetime.now().isocalendar()[1]
    
    # 准备最近四周的标签和数据
    for i in range(4):
        week_number = current_week - i
        if week_number <= 0:  # 处理年初的情况
            week_number = 52 + week_number  # 假设一年有52周
        
        weeks.append(f"第{week_number}周")
        
        # 查找该周的加班数据
        found = False
        for stat in overtime_stats:
            if stat[0] == week_number:
                overtime_hours.append(float(stat[1]) if stat[1] else 0)
                found = True
                break
        
        if not found:
            overtime_hours.append(0)
    
    # 反转列表，使最早的周在前面
    weeks.reverse()
    overtime_hours.reverse()
    
    conn.close()
    
    return render_template('attendance.html', 
                          attendances=attendances,
                          employees=employees,
                          attendance_stats={
                              'present_count': daily_present,
                              'absent_count': daily_absent,
                              'leave_count': daily_leave,
                              'half_day_count': daily_half_day,
                              'attendance_rate': daily_rates[0],
                              'absent_rate': daily_rates[1],
                              'leave_rate': daily_rates[2],
                              'half_day_rate': daily_rates[3]
                          },
                          weekly_stats={
                              'present_count': weekly_present,
                              'absent_count': weekly_absent,
                              'leave_count': weekly_leave,
                              'half_day_count': weekly_half_day,
                              'attendance_rate': weekly_rates[0],
                              'absent_rate': weekly_rates[1],
                              'leave_rate': weekly_rates[2],
                              'half_day_rate': weekly_rates[3]
                          },
                          monthly_stats={
                              'present_count': monthly_present,
                              'absent_count': monthly_absent,
                              'leave_count': monthly_leave,
                              'half_day_count': monthly_half_day,
                              'attendance_rate': monthly_rates[0],
                              'absent_rate': monthly_rates[1],
                              'leave_rate': monthly_rates[2],
                              'half_day_rate': monthly_rates[3]
                          },
                          overtime_stats={
                              'weeks': weeks,
                              'hours': overtime_hours,
                              'total_hours': total_overtime_hours
                          })

# 添加考勤记录
@app.route('/attendance/add', methods=['POST'])
@login_required
def add_attendance():
    if request.method == 'POST':
        employee_id = request.form['employee_id']
        date = request.form['date']
        check_in = request.form['check_in']
        check_out = request.form['check_out']
        overtime_hours = request.form['overtime_hours']
        status = request.form['status']
        note = request.form['note']
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 检查是否有ID参数（编辑模式）
        if 'id' in request.form and request.form['id']:
            # 更新指定ID的记录
            attendance_id = request.form['id']
            cursor.execute("""
                UPDATE attendance
                SET employee_id = ?, date = ?, check_in = ?, check_out = ?, overtime_hours = ?, status = ?, note = ?
                WHERE id = ?
            """, (employee_id, date, check_in, check_out, overtime_hours, status, note, attendance_id))
            flash('考勤记录已更新', 'success')
        else:
            # 检查该员工当天是否已有考勤记录
            cursor.execute("""
                SELECT id FROM attendance 
                WHERE employee_id = ? AND date = ?
            """, (employee_id, date))
            existing = cursor.fetchone()
            
            if existing:
                # 更新现有记录
                cursor.execute("""
                    UPDATE attendance
                    SET check_in = ?, check_out = ?, overtime_hours = ?, status = ?, note = ?
                    WHERE id = ?
                """, (check_in, check_out, overtime_hours, status, note, existing[0]))
                flash('考勤记录已更新', 'success')
            else:
                # 添加新记录
                cursor.execute("""
                    INSERT INTO attendance (employee_id, date, check_in, check_out, overtime_hours, status, note)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (employee_id, date, check_in, check_out, overtime_hours, status, note))
                flash('考勤记录添加成功', 'success')
        
        conn.commit()
        conn.close()
    
    return redirect(url_for('attendance'))

# 删除考勤记录
@app.route('/attendance/delete/<int:id>')
@login_required
def delete_attendance(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM attendance WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    
    flash('考勤记录已删除', 'success')
    return redirect(url_for('attendance'))

# 加班管理
@app.route('/overtime')
@login_required
def overtime():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 修改为只获取加班记录，不关注审批状态
    cursor.execute("""
        SELECT o.id, e.name, o.date, o.start_time, o.end_time, 
               o.hours, o.reason
        FROM overtime o
        JOIN employees e ON o.employee_id = e.id
        ORDER BY o.date DESC, e.name
    """)
    overtimes = cursor.fetchall()
    
    # 获取所有员工
    cursor.execute("SELECT id, name FROM employees")
    employees = cursor.fetchall()
    
    conn.close()
    
    return render_template('overtime.html', 
                          overtimes=overtimes,
                          employees=employees)

# 添加加班记录
@app.route('/overtime/add', methods=['POST'])
@login_required
def add_overtime():
    if request.method == 'POST':
        employee_id = request.form['employee_id']
        date = request.form['date']
        start_time = request.form['start_time']
        end_time = request.form['end_time']
        reason = request.form['reason']
        
        # 计算加班小时数
        start_hour, start_minute = map(int, start_time.split(':'))
        end_hour, end_minute = map(int, end_time.split(':'))
        
        hours = (end_hour - start_hour) + (end_minute - start_minute) / 60.0
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 移除状态字段，或设置固定值
        cursor.execute("""
            INSERT INTO overtime (employee_id, date, start_time, end_time, hours, reason)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (employee_id, date, start_time, end_time, hours, reason))
        
        # 同时更新考勤记录中的加班时间
        cursor.execute("""
            UPDATE attendance
            SET overtime_hours = ?
            WHERE employee_id = ? AND date = ?
        """, (hours, employee_id, date))
        
        # 如果没有该日期的考勤记录，则创建
        if cursor.rowcount == 0:
            cursor.execute("""
                INSERT INTO attendance (employee_id, date, overtime_hours, status, note)
                VALUES (?, ?, ?, 'present', '加班记录')
            """, (employee_id, date, hours))
        
        conn.commit()
        conn.close()
        
        flash('加班记录添加成功', 'success')
    
    return redirect(url_for('overtime'))

# 请假管理
@app.route('/leaves')
@login_required
def leaves():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 修改为只获取请假记录，不关注审批状态
    cursor.execute("""
        SELECT l.id, e.name, l.start_date, l.end_date, l.days, 
               l.leave_type, l.reason, l.applied_on
        FROM leaves l
        JOIN employees e ON l.employee_id = e.id
        ORDER BY l.start_date DESC, e.name
    """)
    leaves_data = cursor.fetchall()
    
    # 获取所有员工
    cursor.execute("SELECT id, name FROM employees")
    employees = cursor.fetchall()
    
    conn.close()
    
    return render_template('leaves.html', 
                          leaves=leaves_data,
                          employees=employees)

# 添加请假记录
@app.route('/leaves/add', methods=['POST'])
@login_required
def add_leave():
    if request.method == 'POST':
        employee_id = request.form['employee_id']
        start_date = request.form['start_date']
        end_date = request.form['end_date']
        leave_type = request.form['leave_type']
        reason = request.form['reason']
        
        # 计算请假天数
        from datetime import datetime
        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')
        days = (end - start).days + 1
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 直接添加请假记录，不需要审批状态
        cursor.execute("""
            INSERT INTO leaves (employee_id, start_date, end_date, days, leave_type, reason)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (employee_id, start_date, end_date, days, leave_type, reason))
        
        # 自动更新考勤记录为请假状态
        from datetime import datetime, timedelta
        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')
        current_date = start
        
        while current_date <= end:
            date_str = current_date.strftime('%Y-%m-%d')
            
            # 检查是否已存在考勤记录
            cursor.execute("""
                SELECT id FROM attendance 
                WHERE employee_id = ? AND date = ?
            """, (employee_id, date_str))
            
            existing = cursor.fetchone()
            
            if existing:
                # 更新为请假状态
                cursor.execute("""
                    UPDATE attendance
                    SET status = 'leave', note = '请假'
                    WHERE id = ?
                """, (existing[0],))
            else:
                # 添加请假考勤记录
                cursor.execute("""
                    INSERT INTO attendance (employee_id, date, status, note)
                    VALUES (?, ?, 'leave', '请假')
                """, (employee_id, date_str))
            
            current_date += timedelta(days=1)
        
        conn.commit()
        conn.close()
        
        flash('请假申请已提交', 'success')
    
    return redirect(url_for('leaves'))

# API接口 - 获取所有员工
@app.route('/api/employees')
@login_required
def api_employees():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT e.id, e.name, e.email, e.phone, e.hire_date, 
               d.name as department, e.position, e.salary
        FROM employees e
        JOIN departments d ON e.department_id = d.id
        ORDER BY e.id
    """)
    employees = []
    for row in cursor.fetchall():
        employees.append({
            'id': row[0],
            'name': row[1],
            'email': row[2],
            'phone': row[3],
            'hire_date': row[4].strftime('%Y-%m-%d') if row[4] else '',
            'department': row[5],
            'position': row[6],
            'salary': row[7]
        })
    
    conn.close()
    
    return jsonify(employees)

# API接口 - 获取考勤记录详情
@app.route('/api/attendance/<int:id>')
@login_required
def api_attendance_detail(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 获取考勤记录
    cursor.execute("""
        SELECT a.id, a.employee_id, e.name, a.date, a.check_in, a.check_out, 
               a.overtime_hours, a.status, a.note
        FROM attendance a
        JOIN employees e ON a.employee_id = e.id
        WHERE a.id = ?
    """, (id,))
    
    attendance = cursor.fetchone()
    conn.close()
    
    if not attendance:
        return jsonify({'error': '考勤记录不存在'}), 404
    
    # 格式化日期和时间
    date_str = attendance[3].strftime('%Y-%m-%d') if attendance[3] else ''
    check_in_str = attendance[4].strftime('%H:%M') if attendance[4] else ''
    check_out_str = attendance[5].strftime('%H:%M') if attendance[5] else ''
    
    return jsonify({
        'id': attendance[0],
        'employee_id': attendance[1],
        'employee_name': attendance[2],
        'date': date_str,
        'check_in': check_in_str,
        'check_out': check_out_str,
        'overtime_hours': attendance[6],
        'status': attendance[7],
        'note': attendance[8]
    })

# API接口 - 获取部门员工
@app.route('/api/departments/<int:id>/employees')
@login_required
def api_department_employees(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT e.id, e.name, e.email, e.phone, e.hire_date, e.position, e.salary
        FROM employees e
        WHERE e.department_id = ?
        ORDER BY e.id
    """, (id,))
    
    employees = []
    for row in cursor.fetchall():
        employees.append({
            'id': row[0],
            'name': row[1],
            'email': row[2],
            'phone': row[3],
            'hire_date': row[4].strftime('%Y-%m-%d') if row[4] else '',
            'position': row[5],
            'salary': row[6]
        })
    
    conn.close()
    
    return jsonify(employees)

# 运行应用
if __name__ == '__main__':
    app.run(debug=True) 