let users = [];
let businesses = [];

document.addEventListener('DOMContentLoaded', () => {
    loadData();
    document.getElementById('task-form').addEventListener('submit', handleSubmit);
});

async function loadData() {
    await Promise.all([loadTasks(), loadUsers(), loadBusinesses()]);
}

async function loadTasks() {
    try {
        const response = await fetch('/admin/api/tasks');
        const data = await response.json();
        
        const tbody = document.getElementById('tasks-table');
        const emptyState = document.getElementById('empty-state');
        
        if (data.tasks.length === 0) {
            tbody.innerHTML = '';
            emptyState.classList.remove('hidden');
        } else {
            emptyState.classList.add('hidden');
            tbody.innerHTML = data.tasks.map(task => {
                const user = users.find(u => u.id === task.assigned_user_id);
                const business = businesses.find(b => b.id === task.business_id);
                
                return `
                <tr class="hover:bg-gray-50">
                    <td class="px-4 py-3 text-sm font-medium text-gray-900">${task.title}</td>
                    <td class="px-4 py-3 text-sm text-gray-600">${user ? user.name : 'N/A'}</td>
                    <td class="px-4 py-3 text-sm text-gray-600">${business ? business.business_name : 'N/A'}</td>
                    <td class="px-4 py-3 text-sm">
                        <span class="px-2 py-1 rounded-full text-xs font-medium ${
                            task.status === 'completed' ? 'bg-green-100 text-green-800' :
                            task.status === 'ongoing' ? 'bg-blue-100 text-blue-800' :
                            'bg-yellow-100 text-yellow-800'
                        }">
                            ${task.status}
                        </span>
                    </td>
                    <td class="px-4 py-3 text-sm text-gray-600">${new Date(task.created_at).toLocaleDateString()}</td>
                    <td class="px-4 py-3 text-sm text-right">
                        <button onclick="editTask('${task.id}')" class="p-2 text-indigo-600 hover:bg-indigo-50 rounded-lg mr-2">
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"></path>
                            </svg>
                        </button>
                        <button onclick="deleteTask('${task.id}', '${task.title}')" class="p-2 text-red-600 hover:bg-red-50 rounded-lg">
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path>
                            </svg>
                        </button>
                    </td>
                </tr>
            `}).join('');
        }
    } catch (error) {
        console.error('Error loading tasks:', error);
        alert('Failed to load tasks');
    }
}

async function loadUsers() {
    try {
        const response = await fetch('/admin/api/users');
        const data = await response.json();
        users = data.users.filter(u => u.role === 'user');
        
        const select = document.getElementById('assigned_user_id');
        select.innerHTML = '<option value="">Select a user...</option>' +
            users.map(user => `<option value="${user.id}">${user.name} (${user.email})</option>`).join('');
    } catch (error) {
        console.error('Error loading users:', error);
    }
}

async function loadBusinesses() {
    try {
        const response = await fetch('/admin/api/businesses');
        const data = await response.json();
        businesses = data.businesses.filter(b => b.status === 'active');
        
        const select = document.getElementById('business_id');
        select.innerHTML = '<option value="">Select a business...</option>' +
            businesses.map(business => `<option value="${business.id}">${business.business_name}</option>`).join('');
    } catch (error) {
        console.error('Error loading businesses:', error);
    }
}

function openCreateModal() {
    document.getElementById('modal-title').textContent = 'Create Task';
    document.getElementById('task-id').value = '';
    document.getElementById('task-form').reset();
    document.getElementById('task-modal').classList.remove('hidden');
}

async function editTask(id) {
    try {
        const response = await fetch(`/admin/api/tasks/${id}`);
        const data = await response.json();
        const task = data.task;
        
        document.getElementById('modal-title').textContent = 'Edit Task';
        document.getElementById('task-id').value = task.id;
        document.getElementById('title').value = task.title;
        document.getElementById('assigned_user_id').value = task.assigned_user_id;
        document.getElementById('business_id').value = task.business_id;
        document.getElementById('description').value = task.description || '';
        document.getElementById('status').value = task.status;
        
        document.getElementById('task-modal').classList.remove('hidden');
    } catch (error) {
        console.error('Error loading task:', error);
        alert('Failed to load task details');
    }
}

async function handleSubmit(e) {
    e.preventDefault();
    
    const id = document.getElementById('task-id').value;
    const data = {
        title: document.getElementById('title').value,
        assigned_user_id: document.getElementById('assigned_user_id').value,
        business_id: document.getElementById('business_id').value,
        description: document.getElementById('description').value,
        status: document.getElementById('status').value
    };
    
    try {
        const url = id ? `/admin/api/tasks/${id}` : '/admin/api/tasks';
        const method = id ? 'PUT' : 'POST';
        
        const response = await fetch(url, {
            method,
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(data)
        });
        
        if (response.ok) {
            closeModal();
            loadTasks();
            alert(id ? 'Task updated successfully' : 'Task created successfully');
        } else {
            const error = await response.json();
            alert(error.error || 'Failed to save task');
        }
    } catch (error) {
        console.error('Error saving task:', error);
        alert('Failed to save task');
    }
}

async function deleteTask(id, title) {
    if (!confirm(`Are you sure you want to delete task "${title}"?`)) return;
    
    try {
        const response = await fetch(`/admin/api/tasks/${id}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            loadTasks();
            alert('Task deleted successfully');
        } else {
            alert('Failed to delete task');
        }
    } catch (error) {
        console.error('Error deleting task:', error);
        alert('Failed to delete task');
    }
}

function closeModal() {
    document.getElementById('task-modal').classList.add('hidden');
}
