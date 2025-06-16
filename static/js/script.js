// 页面加载完成后执行
document.addEventListener('DOMContentLoaded', function() {
    console.log('员工管理系统初始化');
    
    // 初始化Bootstrap提示框
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // 绑定搜索框事件
    bindSearchEvent();
    
    // 初始化数据表格
    initDataTables();
});

// 初始化DataTables
function initDataTables() {
    // 检查是否存在员工表格
    if (document.getElementById('employeesTable')) {
        $('#employeesTable').DataTable({
            language: {
                url: '//cdn.datatables.net/plug-ins/1.10.25/i18n/Chinese.json'
            },
            responsive: true,
            order: [[0, 'asc']]
        });
    }
    
    // 检查是否存在部门员工表格
    if (document.getElementById('deptEmployeesTable')) {
        $('#deptEmployeesTable').DataTable({
            language: {
                url: '//cdn.datatables.net/plug-ins/1.10.25/i18n/Chinese.json'
            },
            responsive: true,
            paging: false,
            info: false
        });
    }
}

// 绑定搜索框事件
function bindSearchEvent() {
    var searchInput = document.getElementById('searchEmployee');
    if (searchInput) {
        searchInput.addEventListener('keyup', function() {
            var table = $('#employeesTable').DataTable();
            table.search(this.value).draw();
        });
    }
}

// 确认删除员工
function confirmDelete(url) {
    $('#confirmDeleteBtn').attr('href', url);
    $('#deleteConfirmModal').modal('show');
    return false;
}

// 确认删除部门
function confirmDeleteDept(url) {
    $('#confirmDeleteDeptBtn').attr('href', url);
    $('#deleteDeptConfirmModal').modal('show');
    return false;
}

// 准备编辑部门
function prepareDeptEdit(id, name, description) {
    $('#editDeptForm').attr('action', '/departments/edit/' + id);
    $('#edit_name').val(name);
    $('#edit_description').val(description);
}

// 显示表单验证错误
function showFormErrors(formId, errors) {
    const form = document.getElementById(formId);
    if (!form) return;
    
    // 清除之前的错误提示
    clearFormErrors(formId);
    
    // 显示新的错误提示
    for (const field in errors) {
        const input = form.querySelector(`[name="${field}"]`);
        if (input) {
            input.classList.add('is-invalid');
            const feedback = document.createElement('div');
            feedback.className = 'invalid-feedback';
            feedback.innerText = errors[field];
            input.parentNode.appendChild(feedback);
        }
    }
}

// 清除表单验证错误
function clearFormErrors(formId) {
    const form = document.getElementById(formId);
    if (!form) return;
    
    const invalidInputs = form.querySelectorAll('.is-invalid');
    const feedbacks = form.querySelectorAll('.invalid-feedback');
    
    invalidInputs.forEach(input => {
        input.classList.remove('is-invalid');
    });
    
    feedbacks.forEach(feedback => {
        feedback.remove();
    });
}

// 生成图表（如果使用图表功能）
function generateChart() {
    // 这里可以添加使用Chart.js等库生成图表的代码
    console.log('图表功能待实现');
} 