#!/usr/bin/env python3
"""
╔═══════════════════════════════════════════════════╗
║           SKYY – Desktop Application              ║
║  PyQt5 GUI that connects to the Skyy Web API      ║
╚═══════════════════════════════════════════════════╝

Usage:
    python desktop_app.py
    
Requirements:
    pip install PyQt5 requests
"""

import sys
import os
import json
import requests
from datetime import datetime, date
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QListWidget, QListWidgetItem,
    QTextEdit, QComboBox, QDateEdit, QMessageBox, QDialog,
    QFormLayout, QGroupBox, QSplitter, QFrame, QMenu, QAction,
    QStatusBar, QToolBar, QCheckBox, QInputDialog
)
from PyQt5.QtCore import Qt, QDate, QSize, pyqtSignal, QThread
from PyQt5.QtGui import QFont, QIcon, QColor, QPalette


# ═══════════════════════════════════════════════════════════════
#  CONFIGURATION
# ═══════════════════════════════════════════════════════════════

DEFAULT_API_URL = "http://127.0.0.1:5000"
API_URL = os.getenv("SKYY_API_URL", DEFAULT_API_URL)


# ═══════════════════════════════════════════════════════════════
#  API CLIENT
# ═══════════════════════════════════════════════════════════════

class SkyyAPIClient:
    """Client for communicating with the Skyy Web API."""
    
    def __init__(self, base_url=API_URL):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.csrf_token = None
        self.auth_token = None
    
    def _get_headers(self):
        """Get headers with CSRF token if available."""
        headers = {'Content-Type': 'application/json'}
        if self.csrf_token:
            headers['X-CSRF-Token'] = self.csrf_token
        return headers
    
    def _update_csrf_token(self, response):
        """Extract CSRF token from response."""
        # Try to get from cookies
        if 'csrf_token' in response.cookies:
            self.csrf_token = response.cookies['csrf_token']
    
    def register(self, username, email, password, confirm_password):
        """Register a new user."""
        url = f"{self.base_url}/register"
        data = {
            'username': username,
            'email': email,
            'password': password,
            'confirm_password': confirm_password
        }
        response = self.session.post(url, data=data, allow_redirects=True)
        self._update_csrf_token(response)
        return response
    
    def login(self, email, password):
        """Login with email and password."""
        url = f"{self.base_url}/login"
        data = {'email': email, 'password': password}
        response = self.session.post(url, data=data, allow_redirects=True)
        self._update_csrf_token(response)
        return response
    
    def logout(self):
        """Logout current user."""
        url = f"{self.base_url}/logout"
        response = self.session.get(url, allow_redirects=True)
        self.csrf_token = None
        return response
    
    def get_todos(self):
        """Get all todos for current user."""
        # First get the dashboard to obtain CSRF token
        url = f"{self.base_url}/dashboard"
        response = self.session.get(url)
        self._update_csrf_token(response)
        return response
    
    def add_todo(self, title, description, priority, due_date):
        """Add a new todo."""
        url = f"{self.base_url}/api/todos"
        data = {
            'title': title,
            'description': description,
            'priority': priority,
            'due_date': due_date
        }
        response = self.session.post(url, json=data, headers=self._get_headers())
        return response
    
    def update_todo(self, todo_id, **kwargs):
        """Update an existing todo."""
        url = f"{self.base_url}/api/todos/{todo_id}"
        response = self.session.put(url, json=kwargs, headers=self._get_headers())
        return response
    
    def delete_todo(self, todo_id):
        """Delete a todo."""
        url = f"{self.base_url}/api/todos/{todo_id}"
        response = self.session.delete(url, headers=self._get_headers())
        return response
    
    def toggle_todo(self, todo_id):
        """Toggle todo completion status."""
        url = f"{self.base_url}/api/todos/{todo_id}/toggle"
        response = self.session.post(url, headers=self._get_headers())
        return response
    
    def health_check(self):
        """Check API health."""
        url = f"{self.base_url}/health"
        try:
            response = self.session.get(url, timeout=5)
            return response.status_code == 200
        except:
            return False


# ═══════════════════════════════════════════════════════════════
#  LOGIN DIALOG
# ═══════════════════════════════════════════════════════════════

class LoginDialog(QDialog):
    """Login/Register dialog."""
    
    def __init__(self, api_client, parent=None):
        super().__init__(parent)
        self.api_client = api_client
        self.is_authenticated = False
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the dialog UI."""
        self.setWindowTitle("Skyy - Login")
        self.setFixedSize(400, 500)
        self.setStyleSheet(self.get_stylesheet())
        
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        
        # Logo/Title
        title = QLabel("☁️ Skyy")
        title.setFont(QFont("Arial", 24, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        subtitle = QLabel("Sign in to your account")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("color: #9ca3af;")
        layout.addWidget(subtitle)
        
        # Tab buttons
        tab_layout = QHBoxLayout()
        self.login_tab = QPushButton("Sign In")
        self.login_tab.setCheckable(True)
        self.login_tab.setChecked(True)
        self.login_tab.clicked.connect(self.show_login)
        
        self.register_tab = QPushButton("Register")
        self.register_tab.setCheckable(True)
        self.register_tab.clicked.connect(self.show_register)
        
        tab_layout.addWidget(self.login_tab)
        tab_layout.addWidget(self.register_tab)
        layout.addLayout(tab_layout)
        
        # Stack widgets
        self.stack = QFrame()
        self.stack_layout = QVBoxLayout(self.stack)
        self.stack_layout.setContentsMargins(0, 0, 0, 0)
        
        # Login form
        self.login_form = self.create_login_form()
        self.stack_layout.addWidget(self.login_form)
        
        # Register form
        self.register_form = self.create_register_form()
        self.register_form.hide()
        self.stack_layout.addWidget(self.register_form)
        
        layout.addWidget(self.stack)
        
        # Status label
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("color: #ef4444;")
        layout.addWidget(self.status_label)
        
        # Set tab button styles
        self.update_tab_styles()
    
    def create_login_form(self):
        """Create login form."""
        form = QFrame()
        layout = QFormLayout(form)
        layout.setSpacing(12)
        
        self.login_email = QLineEdit()
        self.login_email.setPlaceholderText("you@example.com")
        layout.addRow("Email:", self.login_email)
        
        self.login_password = QLineEdit()
        self.login_password.setEchoMode(QLineEdit.Password)
        self.login_password.setPlaceholderText("••••••••")
        layout.addRow("Password:", self.login_password)
        
        login_btn = QPushButton("Sign In")
        login_btn.setStyleSheet("""
            QPushButton {
                background: #6366f1;
                color: white;
                padding: 12px;
                border-radius: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #4f46e5;
            }
        """)
        login_btn.clicked.connect(self.do_login)
        layout.addRow(login_btn)
        
        return form
    
    def create_register_form(self):
        """Create register form."""
        form = QFrame()
        layout = QFormLayout(form)
        layout.setSpacing(12)
        
        self.reg_username = QLineEdit()
        self.reg_username.setPlaceholderText("yourname")
        layout.addRow("Username:", self.reg_username)
        
        self.reg_email = QLineEdit()
        self.reg_email.setPlaceholderText("you@example.com")
        layout.addRow("Email:", self.reg_email)
        
        self.reg_password = QLineEdit()
        self.reg_password.setEchoMode(QLineEdit.Password)
        self.reg_password.setPlaceholderText("••••••••")
        layout.addRow("Password:", self.reg_password)
        
        self.reg_confirm = QLineEdit()
        self.reg_confirm.setEchoMode(QLineEdit.Password)
        self.reg_confirm.setPlaceholderText("••••••••")
        layout.addRow("Confirm:", self.reg_confirm)
        
        register_btn = QPushButton("Create Account")
        register_btn.setStyleSheet("""
            QPushButton {
                background: #6366f1;
                color: white;
                padding: 12px;
                border-radius: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #4f46e5;
            }
        """)
        register_btn.clicked.connect(self.do_register)
        layout.addRow(register_btn)
        
        return form
    
    def show_login(self):
        """Show login form."""
        self.login_tab.setChecked(True)
        self.register_tab.setChecked(False)
        self.login_form.show()
        self.register_form.hide()
        self.update_tab_styles()
    
    def show_register(self):
        """Show register form."""
        self.register_tab.setChecked(True)
        self.login_tab.setChecked(False)
        self.register_form.show()
        self.login_form.hide()
        self.update_tab_styles()
    
    def update_tab_styles(self):
        """Update tab button styles."""
        active_style = """
            QPushButton {
                background: #6366f1;
                color: white;
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: bold;
            }
        """
        inactive_style = """
            QPushButton {
                background: transparent;
                color: #9ca3af;
                padding: 8px 16px;
                border-radius: 6px;
                border: 1px solid #2a2a4a;
            }
            QPushButton:hover {
                border-color: #6366f1;
                color: #6366f1;
            }
        """
        
        self.login_tab.setStyleSheet(active_style if self.login_tab.isChecked() else inactive_style)
        self.register_tab.setStyleSheet(active_style if self.register_tab.isChecked() else inactive_style)
    
    def do_login(self):
        """Perform login."""
        email = self.login_email.text().strip()
        password = self.login_password.text()
        
        if not email or not password:
            self.status_label.setText("Please fill in all fields")
            return
        
        try:
            response = self.api_client.login(email, password)
            if response.status_code == 200:
                self.is_authenticated = True
                self.accept()
            else:
                self.status_label.setText("Invalid email or password")
        except Exception as e:
            self.status_label.setText(f"Connection error: {str(e)}")
    
    def do_register(self):
        """Perform registration."""
        username = self.reg_username.text().strip()
        email = self.reg_email.text().strip()
        password = self.reg_password.text()
        confirm = self.reg_confirm.text()
        
        if not all([username, email, password, confirm]):
            self.status_label.setText("Please fill in all fields")
            return
        
        if password != confirm:
            self.status_label.setText("Passwords do not match")
            return
        
        if len(password) < 12:
            self.status_label.setText("Password must be at least 12 characters")
            return
        
        try:
            response = self.api_client.register(username, email, password, confirm)
            if response.status_code == 200:
                self.is_authenticated = True
                self.accept()
            else:
                self.status_label.setText("Registration failed")
        except Exception as e:
            self.status_label.setText(f"Connection error: {str(e)}")
    
    def get_stylesheet(self):
        """Get dialog stylesheet."""
        return """
            QDialog {
                background: #0f0f1a;
                color: #e8e8f0;
            }
            QLabel {
                color: #e8e8f0;
            }
            QLineEdit {
                background: #1e2a4a;
                border: 1px solid #2a2a4a;
                border-radius: 8px;
                padding: 10px;
                color: #e8e8f0;
                font-size: 14px;
            }
            QLineEdit:focus {
                border-color: #6366f1;
            }
        """


# ═══════════════════════════════════════════════════════════════
#  TODO ITEM WIDGET
# ═══════════════════════════════════════════════════════════════

class TodoItemWidget(QWidget):
    """Custom widget for displaying a todo item."""
    
    toggled = pyqtSignal(int)
    deleted = pyqtSignal(int)
    edited = pyqtSignal(int, str, str, str, str)
    
    def __init__(self, todo, parent=None):
        super().__init__(parent)
        self.todo_id = todo.get('id')
        self.setup_ui(todo)
    
    def setup_ui(self, todo):
        """Setup the todo item UI."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(12)
        
        # Checkbox
        self.checkbox = QCheckBox()
        self.checkbox.setChecked(todo.get('completed', False))
        self.checkbox.stateChanged.connect(self.on_toggle)
        layout.addWidget(self.checkbox)
        
        # Content
        content = QVBoxLayout()
        content.setSpacing(4)
        
        title = todo.get('title', '')
        if todo.get('completed'):
            title = f"<s>{title}</s>"
        self.title_label = QLabel(title)
        self.title_label.setFont(QFont("Arial", 10, QFont.Bold))
        content.addWidget(self.title_label)
        
        description = todo.get('description', '')
        if description:
            self.desc_label = QLabel(description[:80] + ('...' if len(description) > 80 else ''))
            self.desc_label.setStyleSheet("color: #9ca3af; font-size: 12px;")
            content.addWidget(self.desc_label)
        
        layout.addLayout(content, 1)
        
        # Priority badge
        priority = todo.get('priority', 'medium')
        priority_colors = {
            'high': '#ef4444',
            'medium': '#f59e0b',
            'low': '#6b7280'
        }
        priority_label = QLabel(priority.upper())
        priority_label.setStyleSheet(f"""
            background: {priority_colors.get(priority, '#6b7280')}22;
            color: {priority_colors.get(priority, '#6b7280')};
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 10px;
            font-weight: bold;
        """)
        layout.addWidget(priority_label)
        
# Due date
        due_date = todo.get('due_date')
        if due_date:
            try:
                dt = datetime.fromisoformat(due_date)
                due_label = QLabel(dt.strftime('%b %d'))
                due_label.setStyleSheet("color: #9ca3af; font-size: 11px;")
                layout.addWidget(due_label)
            except:
                pass
        
        # Delete button
        delete_btn = QPushButton("🗑")
        delete_btn.setFixedSize(32, 32)
        delete_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                font-size: 16px;
            }
            QPushButton:hover {
                background: rgba(239, 68, 68, 0.1);
                border-radius: 4px;
            }
        """)
        delete_btn.clicked.connect(lambda: self.deleted.emit(self.todo_id))
        layout.addWidget(delete_btn)
        
        # Style
        self.setStyleSheet("""
            TodoItemWidget {
                background: #16213e;
                border: 1px solid #2a2a4a;
                border-radius: 8px;
            }
            TodoItemWidget:hover {
                border-color: #6366f1;
            }
        """)
    
    def on_toggle(self, state):
        """Handle checkbox toggle."""
        self.toggled.emit(self.todo_id)


# ═══════════════════════════════════════════════════════════════
#  ADD TODO DIALOG
# ═══════════════════════════════════════════════════════════════

class AddTodoDialog(QDialog):
    """Dialog for adding/editing a todo."""
    
    def __init__(self, parent=None, todo=None):
        super().__init__(parent)
        self.todo = todo
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the dialog UI."""
        self.setWindowTitle("Edit Task" if self.todo else "New Task")
        self.setFixedSize(450, 400)
        self.setStyleSheet(self.get_stylesheet())
        
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        
        # Title
        title_label = QLabel("Title:")
        layout.addWidget(title_label)
        
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("What needs to be done?")
        if self.todo:
            self.title_input.setText(self.todo.get('title', ''))
        layout.addWidget(self.title_input)
        
        # Description
        desc_label = QLabel("Description:")
        layout.addWidget(desc_label)
        
        self.desc_input = QTextEdit()
        self.desc_input.setPlaceholderText("Add some details...")
        self.desc_input.setMaximumHeight(100)
        if self.todo:
            self.desc_input.setText(self.todo.get('description', ''))
        layout.addWidget(self.desc_input)
        
        # Priority and Due Date
        row = QHBoxLayout()
        
        priority_layout = QVBoxLayout()
        priority_label = QLabel("Priority:")
        priority_layout.addWidget(priority_label)
        
        self.priority_combo = QComboBox()
        self.priority_combo.addItems(["Low", "Medium", "High"])
        self.priority_combo.setCurrentText(
            self.todo.get('priority', 'medium').capitalize() if self.todo else "Medium"
        )
        priority_layout.addWidget(self.priority_combo)
        row.addLayout(priority_layout)
        
        due_layout = QVBoxLayout()
        due_label = QLabel("Due Date:")
        due_layout.addWidget(due_label)
        
        self.due_date = QDateEdit()
        self.due_date.setCalendarPopup(True)
        self.due_date.setDate(QDate.currentDate())
        if self.todo and self.todo.get('due_date'):
            try:
                dt = datetime.fromisoformat(self.todo['due_date'])
                self.due_date.setDate(QDate(dt.year, dt.month, dt.day))
            except:
                pass
        due_layout.addWidget(self.due_date)
        row.addLayout(due_layout)
        
        layout.addLayout(row)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        save_btn = QPushButton("Save Task" if self.todo else "Create Task")
        save_btn.setStyleSheet("""
            QPushButton {
                background: #6366f1;
                color: white;
                padding: 10px 20px;
                border-radius: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #4f46e5;
            }
        """)
        save_btn.clicked.connect(self.accept)
        btn_layout.addWidget(save_btn)
        
        layout.addLayout(btn_layout)
    
    def get_data(self):
        """Get the form data."""
        return {
            'title': self.title_input.text().strip(),
            'description': self.desc_input.toPlainText().strip(),
            'priority': self.priority_combo.currentText().lower(),
            'due_date': self.due_date.date().toString(Qt.ISODate)
        }
    
    def get_stylesheet(self):
        """Get dialog stylesheet."""
        return """
            QDialog {
                background: #0f0f1a;
                color: #e8e8f0;
            }
            QLabel {
                color: #e8e8f0;
                font-weight: bold;
            }
            QLineEdit, QTextEdit {
                background: #1e2a4a;
                border: 1px solid #2a2a4a;
                border-radius: 8px;
                padding: 10px;
                color: #e8e8f0;
            }
            QLineEdit:focus, QTextEdit:focus {
                border-color: #6366f1;
            }
            QComboBox, QDateEdit {
                background: #1e2a4a;
                border: 1px solid #2a2a4a;
                border-radius: 8px;
                padding: 8px;
                color: #e8e8f0;
            }
            QPushButton {
                background: transparent;
                border: 1px solid #2a2a4a;
                border-radius: 8px;
                padding: 10px 20px;
                color: #e8e8f0;
            }
            QPushButton:hover {
                border-color: #6366f1;
            }
        """


# ═══════════════════════════════════════════════════════════════
#  MAIN WINDOW
# ═══════════════════════════════════════════════════════════════

class SkyyMainWindow(QMainWindow):
    """Main application window."""
    
    def __init__(self, api_client):
        super().__init__()
        self.api_client = api_client
        self.todos = []
        self.setup_ui()
        self.load_todos()
    
    def setup_ui(self):
        """Setup the main window UI."""
        self.setWindowTitle("Skyy - To-Do App")
        self.setMinimumSize(900, 600)
        self.setStyleSheet(self.get_stylesheet())
        
        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        layout = QHBoxLayout(central)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Sidebar
        sidebar = self.create_sidebar()
        layout.addWidget(sidebar)
        
        # Main content
        content = self.create_content()
        layout.addWidget(content, 1)
        
        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")
    
    def create_sidebar(self):
        """Create the sidebar."""
        sidebar = QFrame()
        sidebar.setFixedWidth(250)
        sidebar.setStyleSheet("""
            QFrame {
                background: #1a1a2e;
                border-right: 1px solid #2a2a4a;
            }
        """)
        
        layout = QVBoxLayout(sidebar)
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Logo
        logo = QLabel("☁️ Skyy")
        logo.setFont(QFont("Arial", 20, QFont.Bold))
        layout.addWidget(logo)
        
        # Stats
        stats_group = QGroupBox("Statistics")
        stats_group.setStyleSheet("""
            QGroupBox {
                color: #9ca3af;
                border: 1px solid #2a2a4a;
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 12px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        stats_layout = QVBoxLayout(stats_group)
        
        self.total_label = QLabel("Total: 0")
        self.completed_label = QLabel("Completed: 0")
        self.active_label = QLabel("Active: 0")
        
        stats_layout.addWidget(self.total_label)
        stats_layout.addWidget(self.completed_label)
        stats_layout.addWidget(self.active_label)
        
        layout.addWidget(stats_group)
        
        # Filters
        filter_group = QGroupBox("Filters")
        filter_group.setStyleSheet("""
            QGroupBox {
                color: #9ca3af;
                border: 1px solid #2a2a4a;
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 12px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        filter_layout = QVBoxLayout(filter_group)
        
        self.filter_all = QPushButton("All Tasks")
        self.filter_all.setCheckable(True)
        self.filter_all.setChecked(True)
        self.filter_all.clicked.connect(lambda: self.set_filter('all'))
        
        self.filter_active = QPushButton("Active")
        self.filter_active.setCheckable(True)
        self.filter_active.clicked.connect(lambda: self.set_filter('active'))
        
        self.filter_completed = QPushButton("Completed")
        self.filter_completed.setCheckable(True)
        self.filter_completed.clicked.connect(lambda: self.set_filter('completed'))
        
        filter_layout.addWidget(self.filter_all)
        filter_layout.addWidget(self.filter_active)
        filter_layout.addWidget(self.filter_completed)
        
        layout.addWidget(filter_group)
        
        layout.addStretch()
        
        # Logout button
        logout_btn = QPushButton("🚪 Logout")
        logout_btn.clicked.connect(self.logout)
        layout.addWidget(logout_btn)
        
        return sidebar
    
    def create_content(self):
        """Create the main content area."""
        content = QFrame()
        content.setStyleSheet("background: #0f0f1a;")
        
        layout = QVBoxLayout(content)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)
        
        # Header
        header = QHBoxLayout()
        
        title = QLabel("My Tasks")
        title.setFont(QFont("Arial", 18, QFont.Bold))
        header.addWidget(title)
        
        header.addStretch()
        
        add_btn = QPushButton("+ New Task")
        add_btn.setStyleSheet("""
            QPushButton {
                background: #6366f1;
                color: white;
                padding: 10px 20px;
                border-radius: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #4f46e5;
            }
        """)
        add_btn.clicked.connect(self.add_todo)
        header.addWidget(add_btn)
        
        layout.addLayout(header)
        
        # Todo list
        self.todo_list = QListWidget()
        self.todo_list.setSpacing(8)
        self.todo_list.setStyleSheet("""
            QListWidget {
                background: transparent;
                border: none;
            }
            QListWidget::item {
                background: transparent;
            }
        """)
        layout.addWidget(self.todo_list)
        
        return content
    
    def set_filter(self, filter_type):
        """Set the current filter."""
        self.filter_all.setChecked(filter_type == 'all')
        self.filter_active.setChecked(filter_type == 'active')
        self.filter_completed.setChecked(filter_type == 'completed')
        self.load_todos()
    
    def load_todos(self):
        """Load todos from API."""
        self.todo_list.clear()
        self.todos = []
        
        try:
            # For now, we'll use a simple approach - get todos via API
            # In a real implementation, you'd have a proper API endpoint
            response = self.api_client.session.get(f"{self.api_client.base_url}/dashboard")
            
            # Since we can't easily parse HTML, we'll use a mock for now
            # In production, you'd have a proper JSON API endpoint
            self.status_bar.showMessage("Connected to server")
            
            # Update stats
            self.update_stats()
            
        except Exception as e:
            self.status_bar.showMessage(f"Error: {str(e)}")
    
    def update_stats(self):
        """Update statistics display."""
        total = len(self.todos)
        completed = sum(1 for t in self.todos if t.get('completed'))
        active = total - completed
        
        self.total_label.setText(f"Total: {total}")
        self.completed_label.setText(f"Completed: {completed}")
        self.active_label.setText(f"Active: {active}")
    
    def add_todo(self):
        """Add a new todo."""
        dialog = AddTodoDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            data = dialog.get_data()
            if data['title']:
                try:
                    response = self.api_client.add_todo(
                        data['title'],
                        data['description'],
                        data['priority'],
                        data['due_date']
                    )
                    if response.status_code == 201:
                        self.status_bar.showMessage("Task added successfully")
                        self.load_todos()
                    else:
                        self.status_bar.showMessage("Failed to add task")
                except Exception as e:
                    self.status_bar.showMessage(f"Error: {str(e)}")
    
    def logout(self):
        """Logout and close."""
        try:
            self.api_client.logout()
        except:
            pass
        self.close()
    
    def get_stylesheet(self):
        """Get main window stylesheet."""
        return """
            QMainWindow {
                background: #0f0f1a;
                color: #e8e8f0;
            }
            QLabel {
                color: #e8e8f0;
            }
            QPushButton {
                background: transparent;
                border: 1px solid #2a2a4a;
                border-radius: 8px;
                padding: 8px 16px;
                color: #e8e8f0;
            }
            QPushButton:hover {
                border-color: #6366f1;
                color: #6366f1;
            }
            QPushButton:checked {
                background: #6366f1;
                color: white;
            }
            QStatusBar {
                background: #1a1a2e;
                color: #9ca3af;
            }
        """


# ═══════════════════════════════════════════════════════════════
#  APPLICATION ENTRY POINT
# ═══════════════════════════════════════════════════════════════

def main():
    """Main application entry point."""
    app = QApplication(sys.argv)
    app.setApplicationName("Skyy")
    app.setOrganizationName("Skyy")
    
    # Create API client
    api_client = SkyyAPIClient()
    
    # Check API health
    if not api_client.health_check():
        QMessageBox.warning(
            None,
            "Connection Error",
            f"Cannot connect to Skyy API at {API_URL}\n\n"
            "Please make sure the server is running:\n"
            "  python run.py"
        )
    
    # Show login dialog
    login_dialog = LoginDialog(api_client)
    if login_dialog.exec_() != QDialog.Accepted:
        sys.exit(0)
    
    # Show main window
    main_window = SkyyMainWindow(api_client)
    main_window.show()
    
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()