/* ═══════════════════════════════════════════════════
   SKYY – Main JavaScript
   ═══════════════════════════════════════════════════ */

/**
 * Open the add task modal with empty fields
 */
function openAddModal() {
    document.getElementById('modal-title').textContent = 'New Task';
    document.getElementById('modal-submit').textContent = 'Create Task';
    document.getElementById('todo-id').value = '';
    document.getElementById('todo-title').value = '';
    document.getElementById('todo-desc').value = '';
    document.getElementById('todo-priority').value = 'medium';
    document.getElementById('todo-due').value = '';
    document.getElementById('todo-modal').style.display = 'flex';
    document.getElementById('todo-title').focus();
}

/**
 * Open the edit modal pre-filled with task data
 * Uses data attributes to prevent XSS
 */
function openEditModal(id, title, description, priority, dueDate) {
    document.getElementById('modal-title').textContent = 'Edit Task';
    document.getElementById('modal-submit').textContent = 'Save Changes';
    document.getElementById('todo-id').value = id;
    document.getElementById('todo-title').value = title;
    document.getElementById('todo-desc').value = description || '';
    document.getElementById('todo-priority').value = priority || 'medium';
    document.getElementById('todo-due').value = dueDate || '';
    document.getElementById('todo-modal').style.display = 'flex';
    document.getElementById('todo-title').focus();
}

/**
 * Get CSRF token from meta tag or cookie
 */
function getCsrfToken() {
    const meta = document.querySelector('meta[name="csrf-token"]');
    if (meta) return meta.getAttribute('content');
    
    // Fallback: get from cookie
    const match = document.cookie.match(/csrf_token=([^;]+)/);
    return match ? match[1] : '';
}

/**
 * Close the modal
 */
function closeModal() {
    document.getElementById('todo-modal').style.display = 'none';
}

/**
 * Save a task (create or update)
 */
async function saveTodo(event) {
    event.preventDefault();

    const id = document.getElementById('todo-id').value;
    const title = document.getElementById('todo-title').value.trim();
    const description = document.getElementById('todo-desc').value.trim();
    const priority = document.getElementById('todo-priority').value;
    const dueDate = document.getElementById('todo-due').value;

    if (!title) return;

    const payload = {
        title,
        description,
        priority,
        due_date: dueDate || null,
    };

    const csrfToken = getCsrfToken();
    const headers = {
        'Content-Type': 'application/json',
        'X-CSRF-Token': csrfToken,
    };

    try {
        if (id) {
            // Update existing task
            const url = window.URLS.update.replace('/0', '/' + id);
            const response = await fetch(url, {
                method: 'PUT',
                headers: headers,
                body: JSON.stringify(payload),
            });

            if (!response.ok) throw new Error('Failed to update task');

            closeModal();
            // Reload to reflect changes
            location.reload();
        } else {
            // Create new task
            const response = await fetch(window.URLS.add, {
                method: 'POST',
                headers: headers,
                body: JSON.stringify(payload),
            });

            if (!response.ok) throw new Error('Failed to create task');

            const todo = await response.json();
            addTodoToList(todo);
            closeModal();
        }
    } catch (error) {
        console.error('Error saving task:', error);
        alert('Something went wrong. Please try again.');
    }
}

/**
 * Toggle a task's completed status
 */
async function toggleTodo(id) {
    const url = window.URLS.toggle.replace('/0', '/' + id);
    const csrfToken = getCsrfToken();
    try {
        const response = await fetch(url, { 
            method: 'POST',
            headers: { 'X-CSRF-Token': csrfToken },
        });
        if (!response.ok) throw new Error('Failed to toggle task');

        const data = await response.json();
        const todoItem = document.querySelector(`.todo-item[data-id="${id}"]`);
        if (todoItem) {
            todoItem.classList.toggle('completed', data.completed);
            const checkIcon = todoItem.querySelector('.todo-check i');
            if (data.completed) {
                checkIcon.className = 'fas fa-check-circle';
            } else {
                checkIcon.className = 'far fa-circle';
            }
        }
    } catch (error) {
        console.error('Error toggling task:', error);
    }
}

/**
 * Delete a task with confirmation
 */
async function deleteTodo(id) {
    if (!confirm('Are you sure you want to delete this task?')) return;

    const url = window.URLS.delete.replace('/0', '/' + id);
    const csrfToken = getCsrfToken();
    try {
        const response = await fetch(url, { 
            method: 'DELETE',
            headers: { 'X-CSRF-Token': csrfToken },
        });
        if (!response.ok) throw new Error('Failed to delete task');

        const todoItem = document.querySelector(`.todo-item[data-id="${id}"]`);
        if (todoItem) {
            todoItem.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
            todoItem.style.opacity = '0';
            todoItem.style.transform = 'translateX(20px)';
            setTimeout(() => todoItem.remove(), 300);
        }
    } catch (error) {
        console.error('Error deleting task:', error);
    }
}

/**
 * Add a new todo item to the list (without reload)
 * Uses safe DOM methods to prevent XSS
 */
function addTodoToList(todo) {
    const todoList = document.getElementById('todo-list');
    const emptyState = todoList.querySelector('.empty-state');

    // Remove empty state if it exists
    if (emptyState) {
        emptyState.remove();
    }

    const item = document.createElement('div');
    item.className = 'todo-item';
    item.dataset.id = todo.id;
    item.style.animation = 'modalIn 0.3s ease';

    const priorityLabel = todo.priority || 'medium';

    // Safe DOM construction instead of innerHTML
    const checkBtn = document.createElement('button');
    checkBtn.className = 'todo-check';
    checkBtn.onclick = () => toggleTodo(todo.id);
    const checkIcon = document.createElement('i');
    checkIcon.className = 'far fa-circle';
    checkBtn.appendChild(checkIcon);

    const content = document.createElement('div');
    content.className = 'todo-content';
    content.onclick = () => openEditModal(todo.id, todo.title, todo.description || '', priorityLabel, todo.due_date ? todo.due_date.substring(0, 10) : '');
    
    const titleDiv = document.createElement('div');
    titleDiv.className = 'todo-title';
    titleDiv.textContent = todo.title;
    content.appendChild(titleDiv);

    if (todo.description) {
        const descDiv = document.createElement('div');
        descDiv.className = 'todo-desc';
        descDiv.textContent = todo.description.substring(0, 80) + (todo.description.length > 80 ? '...' : '');
        content.appendChild(descDiv);
    }

    const meta = document.createElement('div');
    meta.className = 'todo-meta';

    if (todo.due_date) {
        const dueSpan = document.createElement('span');
        dueSpan.className = 'todo-due';
        dueSpan.innerHTML = `<i class="far fa-calendar"></i> ${new Date(todo.due_date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}`;
        meta.appendChild(dueSpan);
    }

    const prioritySpan = document.createElement('span');
    prioritySpan.className = `priority-badge priority-${priorityLabel}`;
    prioritySpan.textContent = priorityLabel;
    meta.appendChild(prioritySpan);

    const deleteBtn = document.createElement('button');
    deleteBtn.className = 'todo-delete';
    deleteBtn.title = 'Delete';
    deleteBtn.onclick = () => deleteTodo(todo.id);
    deleteBtn.innerHTML = '<i class="fas fa-trash-alt"></i>';
    meta.appendChild(deleteBtn);

    item.appendChild(checkBtn);
    item.appendChild(content);
    item.appendChild(meta);

    const sortSelect = document.getElementById('sort-select');
    if (sortSelect && sortSelect.value === 'created') {
        todoList.prepend(item);
    } else {
        todoList.appendChild(item);
    }
}

/**
 * Escape HTML special characters
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * Escape JavaScript string for embedding in onclick attributes
 */
function escapeJs(text) {
    if (!text) return '';
    return text
        .replace(/\\/g, '\\\\')
        .replace(/'/g, "\\'")
        .replace(/"/g, '\\"')
        .replace(/\n/g, '\\n')
        .replace(/\r/g, '\\r');
}

/**
 * Close modal on overlay click
 */
document.addEventListener('DOMContentLoaded', function () {
    const modalOverlay = document.getElementById('todo-modal');
    if (modalOverlay) {
        modalOverlay.addEventListener('click', function (event) {
            if (event.target === modalOverlay) {
                closeModal();
            }
        });

        // Close modal on Escape key
        document.addEventListener('keydown', function (event) {
            if (event.key === 'Escape' && modalOverlay.style.display === 'flex') {
                closeModal();
            }
        });
    }

    // Sync sort select with URL params
    const sortSelect = document.getElementById('sort-select');
    if (sortSelect) {
        sortSelect.addEventListener('change', function () {
            const params = new URLSearchParams(window.location.search);
            params.set('sort', this.value);
            window.location.search = params.toString();
        });
    }
});