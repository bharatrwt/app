let selectedFile = null;
let messageId = null;
let pollInterval = null;

document.addEventListener('DOMContentLoaded', () => {
    loadTasks();
    setupFileUpload();
    setupImagePreview();
    document.getElementById('message-form').addEventListener('submit', handleSubmit);
});

async function loadTasks() {
    try {
        const response = await fetch('/user/api/tasks/assigned');
        const data = await response.json();
        
        const select = document.getElementById('task_id');
        select.innerHTML = '<option value="">No task selected</option>' +
            data.tasks.map(task => `<option value="${task.id}">${task.title}</option>`).join('');
        
        // Check if task_id in URL
        const params = new URLSearchParams(window.location.search);
        const taskId = params.get('task_id');
        if (taskId) {
            select.value = taskId;
        }
    } catch (error) {
        console.error('Error loading tasks:', error);
    }
}

function setupFileUpload() {
    const dropZone = document.getElementById('drop-zone');
    const fileInput = document.getElementById('recipients_file');
    
    dropZone.addEventListener('click', () => fileInput.click());
    
    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.classList.add('border-green-500', 'bg-green-50');
    });
    
    dropZone.addEventListener('dragleave', () => {
        dropZone.classList.remove('border-green-500', 'bg-green-50');
    });
    
    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.classList.remove('border-green-500', 'bg-green-50');
        
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            handleFileSelect(files[0]);
        }
    });
    
    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handleFileSelect(e.target.files[0]);
        }
    });
}

function handleFileSelect(file) {
    const validTypes = ['text/csv', 'application/vnd.ms-excel', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'];
    
    if (!validTypes.includes(file.type) && !file.name.endsWith('.csv') && !file.name.endsWith('.xlsx')) {
        alert('Please upload a CSV or XLSX file');
        return;
    }
    
    if (file.size > 10 * 1024 * 1024) {
        alert('File size must be less than 10MB');
        return;
    }
    
    selectedFile = file;
    document.getElementById('file-name').textContent = file.name;
    document.getElementById('file-info').classList.remove('hidden');
}

function setupImagePreview() {
    const mediaUrlInput = document.getElementById('media_url');
    const imagePreview = document.getElementById('image-preview');
    const previewImg = document.getElementById('preview-img');
    
    mediaUrlInput.addEventListener('blur', () => {
        const url = mediaUrlInput.value;
        if (url) {
            previewImg.src = url;
            previewImg.onload = () => {
                imagePreview.classList.remove('hidden');
            };
            previewImg.onerror = () => {
                imagePreview.classList.add('hidden');
                alert('Invalid or inaccessible image URL');
            };
        }
    });
}

async function handleSubmit(e) {
    e.preventDefault();
    
    if (!selectedFile) {
        alert('Please upload a recipients file');
        return;
    }
    
    const formData = new FormData();
    formData.append('task_id', document.getElementById('task_id').value);
    formData.append('media_url', document.getElementById('media_url').value);
    formData.append('title', document.getElementById('title').value);
    formData.append('body', document.getElementById('body').value);
    formData.append('recipients_file', selectedFile);
    
    const submitBtn = document.getElementById('submit-btn');
    submitBtn.disabled = true;
    submitBtn.textContent = 'Sending...';
    
    try {
        const response = await fetch('/messages/api/send', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (response.ok) {
            messageId = data.message_id;
            document.getElementById('file-count').textContent = data.total_recipients;
            document.getElementById('progress-section').classList.remove('hidden');
            
            // Start polling for updates
            startPolling();
            
            alert(`Message queued successfully! ${data.total_recipients} recipients`);
        } else {
            alert(data.error || 'Failed to send messages');
            submitBtn.disabled = false;
            submitBtn.textContent = 'Send Messages';
        }
    } catch (error) {
        console.error('Error sending messages:', error);
        alert('Failed to send messages');
        submitBtn.disabled = false;
        submitBtn.textContent = 'Send Messages';
    }
}

function startPolling() {
    // Poll every 2 seconds
    pollInterval = setInterval(async () => {
        try {
            const response = await fetch(`/messages/api/messages/${messageId}/status`);
            const data = await response.json();
            
            if (response.ok) {
                updateStats(data.stats);
                
                // Stop polling if completed
                if (data.message.status === 'completed' || data.message.status === 'failed') {
                    clearInterval(pollInterval);
                    document.getElementById('submit-btn').textContent = 'Completed';
                }
            }
        } catch (error) {
            console.error('Error polling status:', error);
        }
    }, 2000);
}

function updateStats(stats) {
    document.getElementById('stat-queued').textContent = stats.queued || 0;
    document.getElementById('stat-sent').textContent = stats.sent || 0;
    document.getElementById('stat-delivered').textContent = stats.delivered || 0;
    document.getElementById('stat-failed').textContent = stats.failed || 0;
    
    const total = stats.queued + stats.sent + stats.delivered + stats.failed;
    const progress = total > 0 ? ((stats.sent + stats.delivered + stats.failed) / total * 100) : 0;
    document.getElementById('progress-bar').style.width = progress + '%';
}
