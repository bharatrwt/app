document.addEventListener('DOMContentLoaded', () => {
    loadHistory();
});

async function loadHistory() {
    try {
        const response = await fetch('/user/api/messages/history');
        const data = await response.json();
        
        const tbody = document.getElementById('history-table');
        const emptyState = document.getElementById('empty-state');
        
        if (data.messages.length === 0) {
            tbody.innerHTML = '';
            emptyState.classList.remove('hidden');
        } else {
            emptyState.classList.add('hidden');
            tbody.innerHTML = data.messages.map(message => {
                const stats = message.stats || {};
                return `
                <tr class="hover:bg-gray-50">
                    <td class="px-4 py-3 text-sm font-medium text-gray-900">${message.title}</td>
                    <td class="px-4 py-3 text-sm text-gray-600">${message.total_recipients}</td>
                    <td class="px-4 py-3 text-sm text-gray-600">${stats.sent || 0}</td>
                    <td class="px-4 py-3 text-sm text-gray-600">${stats.delivered || 0}</td>
                    <td class="px-4 py-3 text-sm text-gray-600">${stats.seen || 0}</td>
                    <td class="px-4 py-3 text-sm text-gray-600">${new Date(message.created_at).toLocaleDateString()}</td>
                    <td class="px-4 py-3 text-sm">
                        <span class="px-2 py-1 rounded-full text-xs font-medium ${
                            message.status === 'completed' ? 'bg-green-100 text-green-800' :
                            message.status === 'queued' ? 'bg-yellow-100 text-yellow-800' :
                            message.status === 'failed' ? 'bg-red-100 text-red-800' :
                            'bg-blue-100 text-blue-800'
                        }">
                            ${message.status}
                        </span>
                    </td>
                </tr>
            `}).join('');
        }
    } catch (error) {
        console.error('Error loading history:', error);
        alert('Failed to load message history');
    }
}
