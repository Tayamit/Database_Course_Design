from flask import Flask, render_template, request, redirect, url_for, jsonify, session, flash
import pyodbc
import os
from datetime import datetime
from functools import wraps

app = Flask(__name__)
app.secret_key = os.urandom(24)

# 数据库连接
def get_db_connection():
    conn = pyodbc.connect('DRIVER={ODBC Driver 17 for SQL Server};'
                          'SERVER=DESKTOP-H7RDUFQ;'
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
    
    cursor.execute("DELETE FROM employees WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    
    flash('员工删除成功', 'success')
    return redirect(url_for('employees'))

# 部门管理
@app.route('/departments')
@login_required
def departments():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM departments")
    departments = cursor.fetchall()
    
    conn.close()
    
    return render_template('departments.html', departments=departments)

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
    
    conn.close()
    
    return render_template('edit_department.html', department=department)

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

# 运行应用
if __name__ == '__main__':
    app.run(debug=True) 
