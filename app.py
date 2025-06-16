from flask import Flask, render_template, request, redirect, url_for, jsonify, session, flash
import pyodbc
import os
from datetime import datetime, timedelta
from functools import wraps

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
    
    # 获取当天出勤率
    cursor.execute("""
        SELECT 
            COUNT(CASE WHEN status = 'present' THEN 1 END) * 100.0 / COUNT(*) AS attendance_rate,
            COUNT(CASE WHEN status = 'present' THEN 1 END) AS present_count,
            COUNT(CASE WHEN status = 'absent' THEN 1 END) AS absent_count,
            COUNT(CASE WHEN status = 'leave' THEN 1 END) AS leave_count,
            COUNT(CASE WHEN status = 'half-day' THEN 1 END) AS half_day_count,
            SUM(overtime_hours) AS total_overtime_hours
        FROM attendance 
        WHERE date = ?
    """, today)
    
    attendance_stats = cursor.fetchone()
    attendance_rate = attendance_stats[0] if attendance_stats[0] else 0
    present_count = attendance_stats[1] if attendance_stats[1] else 0
    absent_count = attendance_stats[2] if attendance_stats[2] else 0
    leave_count = attendance_stats[3] if attendance_stats[3] else 0
    half_day_count = attendance_stats[4] if attendance_stats[4] else 0
    overtime_hours = attendance_stats[5] if attendance_stats[5] else 0
    
    # 获取最近添加的员工
    cursor.execute("""
        SELECT TOP 5 e.id, e.name, d.name as department
        FROM employees e
        JOIN departments d ON e.department_id = d.id
        ORDER BY e.hire_date DESC
    """)
    recent_employees = cursor.fetchall()
    
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
                          recent_employees=recent_employees)

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
    
    conn.close()
    
    return render_template('edit_employee.html', 
                          employee=employee,
                          departments=departments)

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
    
    conn.close()
    
    return render_template('attendance.html', 
                          attendances=attendances,
                          employees=employees)

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