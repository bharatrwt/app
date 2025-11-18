document.addEventListener('DOMContentLoaded', () => {
    loadUsers();
    document.getElementById('user-form').addEventListener('submit', handleSubmit);
});

async function loadUsers() {
    try {
        const response = await fetch('/admin/api/users');
        const data = await response.json();
        
        const tbody = document.getElementById('users-table');
        const emptyState = document.getElementById('empty-state');
        
        if (data.users.length === 0) {
            tbody.innerHTML = '';
            emptyState.classList.remove('hidden');
        } else {
            emptyState.classList.add('hidden');
            tbody.innerHTML = data.users.map(user => `
                <tr class="hover:bg-gray-50">
                    <td class="px-4 py-3 text-sm font-medium text-gray-900">${user.name}</td>
                    <td class="px-4 py-3 text-sm text-gray-600">${user.email}</td>
                    <td class="px-4 py-3 text-sm">
                        <span class="px-2 py-1 rounded-full text-xs font-medium ${user.role === 'admin' ? 'bg-purple-100 text-purple-800' : 'bg-blue-100 text-blue-800'}">
                            ${user.role}
                        </span>
                    </td>
                    <td class="px-4 py-3 text-sm text-gray-600">${new Date(user.created_at).toLocaleDateString()}</td>
                    <td class="px-4 py-3 text-sm text-right">
                        <button onclick="editUser('${user.id}')" class="p-2 text-indigo-600 hover:bg-indigo-50 rounded-lg mr-2">
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"></path>
                            </svg>
                        </button>
                        <button onclick="deleteUser('${user.id}', '${user.name}')" class="p-2 text-red-600 hover:bg-red-50 rounded-lg">
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path>
                            </svg>
                        </button>
                    </td>
                </tr>
            `).join('');
        }
    } catch (error) {
        console.error('Error loading users:', error);
        alert('Failed to load users');
    }
}

function openCreateModal() {
    document.getElementById('modal-title').textContent = 'Add User';
    document.getElementById('user-id').value = '';
    document.getElementById('user-form').reset();
    document.getElementById('password').required = true;
    document.getElementById('password-required').classList.remove('hidden');
    document.getElementById('password-hint').classList.add('hidden');
    document.getElementById('user-modal').classList.remove('hidden');
}

async function editUser(id) {
    try {
        const response = await fetch(`/admin/api/users/${id}`);
        const data = await response.json();
        const user = data.user;
        
        document.getElementById('modal-title').textContent = 'Edit User';
        document.getElementById('user-id').value = user.id;
        document.getElementById('name').value = user.name;
        document.getElementById('email').value = user.email;
        document.getElementById('password').value = '';
        document.getElementById('password').required = false;
        document.getElementById('password-required').classList.add('hidden');
        document.getElementById('password-hint').classList.remove('hidden');
        document.getElementById('role').value = user.role;
        
        document.getElementById('user-modal').classList.remove('hidden');
    } catch (error) {
        console.error('Error loading user:', error);
        alert('Failed to load user details');
    }
}

async function handleSubmit(e) {
    e.preventDefault();
    
    const id = document.getElementById('user-id').value;
    const data = {
        name: document.getElementById('name').value,
        email: document.getElementById('email').value,
        password: document.getElementById('password').value,
        role: document.getElementById('role').value
    };
    
    try {
        const url = id ? `/admin/api/users/${id}` : '/admin/api/users';
        const method = id ? 'PUT' : 'POST';
        
        const response = await fetch(url, {
            method,
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(data)
        });
        
        if (response.ok) {
            closeModal();
            loadUsers();
            alert(id ? 'User updated successfully' : 'User created successfully');
        } else {
            const error = await response.json();
            alert(error.error || 'Failed to save user');
        }
    } catch (error) {
        console.error('Error saving user:', error);
        alert('Failed to save user');
    }
}

async function deleteUser(id, name) {
    if (!confirm(`Are you sure you want to delete "${name}"?`)) return;
    
    try {
        const response = await fetch(`/admin/api/users/${id}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            loadUsers();
            alert('User deleted successfully');
        } else {
            alert('Failed to delete user');
        }
    } catch (error) {
        console.error('Error deleting user:', error);
        alert('Failed to delete user');
    }
}

function closeModal() {
    document.getElementById('user-modal').classList.add('hidden');
}
