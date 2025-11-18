// Load businesses on page load
document.addEventListener('DOMContentLoaded', () => {
    loadBusinesses();
    
    // Setup form submission
    document.getElementById('business-form').addEventListener('submit', handleSubmit);
});

async function loadBusinesses() {
    try {
        const response = await fetch('/admin/api/businesses');
        const data = await response.json();
        
        const tbody = document.getElementById('businesses-table');
        const emptyState = document.getElementById('empty-state');
        
        if (data.businesses.length === 0) {
            tbody.innerHTML = '';
            emptyState.classList.remove('hidden');
        } else {
            emptyState.classList.add('hidden');
            tbody.innerHTML = data.businesses.map(business => `
                <tr class="hover:bg-gray-50">
                    <td class="px-4 py-3 text-sm font-medium text-gray-900">${business.business_name}</td>
                    <td class="px-4 py-3 text-sm text-gray-600">${business.phone_id}</td>
                    <td class="px-4 py-3 text-sm text-gray-600">${business.waba_id}</td>
                    <td class="px-4 py-3 text-sm">
                        <span class="px-2 py-1 rounded-full text-xs font-medium ${business.status === 'active' ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'}">
                            ${business.status}
                        </span>
                    </td>
                    <td class="px-4 py-3 text-sm text-gray-600">${new Date(business.created_at).toLocaleDateString()}</td>
                    <td class="px-4 py-3 text-sm text-right">
                        <button onclick="editBusiness('${business.id}')" class="p-2 text-indigo-600 hover:bg-indigo-50 rounded-lg mr-2">
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"></path>
                            </svg>
                        </button>
                        <button onclick="deleteBusiness('${business.id}', '${business.business_name}')" class="p-2 text-red-600 hover:bg-red-50 rounded-lg">
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path>
                            </svg>
                        </button>
                    </td>
                </tr>
            `).join('');
        }
    } catch (error) {
        console.error('Error loading businesses:', error);
        alert('Failed to load businesses');
    }
}

function openCreateModal() {
    document.getElementById('modal-title').textContent = 'Add Business';
    document.getElementById('business-id').value = '';
    document.getElementById('business-form').reset();
    document.getElementById('business-modal').classList.remove('hidden');
}

async function editBusiness(id) {
    try {
        const response = await fetch(`/admin/api/businesses/${id}`);
        const data = await response.json();
        const business = data.business;
        
        document.getElementById('modal-title').textContent = 'Edit Business';
        document.getElementById('business-id').value = business.id;
        document.getElementById('business_name').value = business.business_name;
        document.getElementById('business_token').value = '***ENCRYPTED***';
        document.getElementById('phone_id').value = business.phone_id;
        document.getElementById('waba_id').value = business.waba_id;
        document.getElementById('status').value = business.status;
        
        document.getElementById('business-modal').classList.remove('hidden');
    } catch (error) {
        console.error('Error loading business:', error);
        alert('Failed to load business details');
    }
}

async function handleSubmit(e) {
    e.preventDefault();
    
    const id = document.getElementById('business-id').value;
    const data = {
        business_name: document.getElementById('business_name').value,
        business_token: document.getElementById('business_token').value,
        phone_id: document.getElementById('phone_id').value,
        waba_id: document.getElementById('waba_id').value,
        status: document.getElementById('status').value
    };
    
    try {
        const url = id ? `/admin/api/businesses/${id}` : '/admin/api/businesses';
        const method = id ? 'PUT' : 'POST';
        
        const response = await fetch(url, {
            method,
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(data)
        });
        
        if (response.ok) {
            closeModal();
            loadBusinesses();
            alert(id ? 'Business updated successfully' : 'Business created successfully');
        } else {
            const error = await response.json();
            alert(error.error || 'Failed to save business');
        }
    } catch (error) {
        console.error('Error saving business:', error);
        alert('Failed to save business');
    }
}

async function deleteBusiness(id, name) {
    if (!confirm(`Are you sure you want to delete "${name}"?`)) return;
    
    try {
        const response = await fetch(`/admin/api/businesses/${id}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            loadBusinesses();
            alert('Business deleted successfully');
        } else {
            alert('Failed to delete business');
        }
    } catch (error) {
        console.error('Error deleting business:', error);
        alert('Failed to delete business');
    }
}

function closeModal() {
    document.getElementById('business-modal').classList.add('hidden');
}
