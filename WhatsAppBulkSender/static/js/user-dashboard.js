document.addEventListener('DOMContentLoaded', () => {
    loadTasks();
});

async function loadTasks() {
    try {
        const response = await fetch('/user/api/tasks/assigned');
        const data = await response.json();
        
        const tbody = document.getElementById('tasks-table');
        const emptyState = document.getElementById('empty-state');
        const taskCount = document.getElementById('task-count');
        
        taskCount.textContent = data.tasks.length;
        
        if (data.tasks.length === 0) {
            tbody.innerHTML = '';
            emptyState.classList.remove('hidden');
        } else {
            emptyState.classList.add('hidden');
            tbody.innerHTML = data.tasks.map(task => `
                <tr class="hover:bg-gray-50">
                    <td class="px-4 py-3 text-sm font-medium text-gray-900">${task.title}</td>
                    <td class="px-4 py-3 text-sm text-gray-600">${task.description || 'N/A'}</td>
                    <td class="px-4 py-3 text-sm">
                        <select 
                            onchange="updateTaskStatus('${task.id}', this.value)" 
                            class="px-2 py-1 rounded-lg text-xs font-medium border border-gray-300 focus:ring-2 focus:ring-indigo-500 ${
                                task.status === 'completed' ? 'bg-green-100 text-green-800' :
                                task.status === 'ongoing' ? 'bg-blue-100 text-blue-800' :
                                'bg-yellow-100 text-yellow-800'
                            }">
                            <option value="pending" ${task.status === 'pending' ? 'selected' : ''}>Pending</option>
                            <option value="ongoing" ${task.status === 'ongoing' ? 'selected' : ''}>Ongoing</option>
                            <option value="completed" ${task.status === 'completed' ? 'selected' : ''}>Completed</option>
                        </select>
                    </td>
                    <td class="px-4 py-3 text-sm text-gray-600">${new Date(task.created_at).toLocaleDateString()}</td>
                    <td class="px-4 py-3 text-sm text-right">
                        <a href="/user/send-message?task_id=${task.id}" class="px-4 py-2 bg-green-600 hover:bg-green-700 text-white text-xs font-medium rounded-lg inline-flex items-center gap-2">
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"></path>
                            </svg>
                            Send Message
                        </a>
                    </td>
                </tr>
            `).join('');
        }
    } catch (error) {
        console.error('Error loading tasks:', error);
        alert('Failed to load tasks');
    }
}

async function updateTaskStatus(taskId, status) {
    try {
        const response = await fetch(`/user/api/tasks/${taskId}/status`, {
            method: 'PUT',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ status })
        });
        
        if (response.ok) {
            loadTasks();
        } else {
            alert('Failed to update task status');
        }
    } catch (error) {
        console.error('Error updating task status:', error);
        alert('Failed to update task status');
    }
}
