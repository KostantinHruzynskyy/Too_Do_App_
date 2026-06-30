"""
╔═══════════════════════════════════════════════════╗
║           SKYY – SECURE ROUTES                    ║
║  All user input is sanitized, validated,          ║
║  and rate-limited before processing.              ║
╚═══════════════════════════════════════════════════╝
"""

from flask import (
    Blueprint, render_template, redirect, url_for,
    flash, request, jsonify,
)
from flask_login import login_user, logout_user, login_required, current_user
from app import db, bcrypt, limiter
from app.models import User, Todo
from app.security import (
    sanitize_plain_text,
    sanitize_html,
    sanitize_json_input,
    validate_password_strength,
    PasswordValidationError,
    validate_username,
    validate_email_address,
    is_safe_redirect_url,
    validate_content_type,
    check_login_attempts,
    record_failed_login,
    require_csrf,
    RATE_LIMIT_LOGIN,
    RATE_LIMIT_REGISTER,
    RATE_LIMIT_API,
    MAX_TITLE_LENGTH,
    MAX_DESCRIPTION_LENGTH,
)
from datetime import datetime, date

main = Blueprint('main', __name__)
auth = Blueprint('auth', __name__)


@main.context_processor
def inject_now():
    return {'now': datetime.now}


# ═══════════════════════════════════════════════════════════════
#  HUB / LANDING ROUTES
# ═══════════════════════════════════════════════════════════════

@main.route('/')
def hub():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return render_template('hub.html')


@main.route('/hub')
def hub_page():
    return render_template('hub.html')


@main.route('/features')
def features():
    return render_template('hub.html')


@main.route('/about')
def about():
    return render_template('hub.html')


# ═══════════════════════════════════════════════════════════════
#  AUTH ROUTES
# ═══════════════════════════════════════════════════════════════

@auth.route('/login', methods=['GET', 'POST'])
@limiter.limit(RATE_LIMIT_LOGIN)
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    if request.method == 'POST':
        # Check brute-force lockout
        allowed, retry_after = check_login_attempts()
        if not allowed:
            flash(
                f'Too many login attempts. Try again in '
                f'{retry_after} seconds.',
                'danger',
            )
            return render_template('login.html')

        email = sanitize_plain_text(request.form.get('email', ''))
        password = request.form.get('password', '')

        if not email or not password:
            flash('Email and password are required.', 'danger')
            return render_template('login.html')

        user = User.query.filter_by(email=email).first()

        if user and bcrypt.check_password_hash(user.password_hash, password):
            login_user(user, remember=True)
            flash('Welcome back! ✨', 'success')

            # Validate next URL to prevent open redirect
            next_page = request.args.get('next')
            if next_page and is_safe_redirect_url(next_page):
                return redirect(next_page)
            return redirect(url_for('main.dashboard'))
        else:
            record_failed_login()
            flash('Invalid email or password.', 'danger')

    return render_template('login.html')


@auth.route('/register', methods=['GET', 'POST'])
@limiter.limit(RATE_LIMIT_REGISTER)
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    if request.method == 'POST':
        username = sanitize_plain_text(request.form.get('username', ''))
        email_raw = sanitize_plain_text(request.form.get('email', ''))
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        # Validate username
        valid_username, username_error = validate_username(username)
        if not valid_username:
            flash(username_error, 'danger')
            return render_template('register.html')

        # Validate email
        valid_email, email_result = validate_email_address(email_raw)
        if not valid_email:
            flash(email_result, 'danger')
            return render_template('register.html')
        email = email_result

        # Validate password match
        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('register.html')

        # Validate password strength
        try:
            validate_password_strength(password)
        except PasswordValidationError as e:
            flash(str(e), 'danger')
            return render_template('register.html')

        # Check for existing user
        if User.query.filter_by(email=email).first():
            flash('Email already registered.', 'danger')
            return render_template('register.html')

        if User.query.filter_by(username=username).first():
            flash('Username already taken.', 'danger')
            return render_template('register.html')

        # Create user with hashed password
        hashed_pw = bcrypt.generate_password_hash(password).decode('utf-8')
        user = User(
            username=username, email=email, password_hash=hashed_pw
        )
        db.session.add(user)
        db.session.commit()

        flash('Account created successfully! Welcome to Skyy 🚀', 'success')
        login_user(user, remember=True)
        return redirect(url_for('main.dashboard'))

    return render_template('register.html')


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))


# ═══════════════════════════════════════════════════════════════
#  MAIN ROUTES
# ═══════════════════════════════════════════════════════════════

@main.route('/dashboard')
@login_required
def dashboard():
    filter_by = request.args.get('filter', 'all')
    sort_by = request.args.get('sort', 'created')

    # Validate filter parameter (allowlist)
    valid_filters = {'all', 'active', 'completed', 'high', 'medium', 'low'}
    if filter_by not in valid_filters:
        filter_by = 'all'

    # Validate sort parameter (allowlist)
    valid_sorts = {'created', 'priority', 'due'}
    if sort_by not in valid_sorts:
        sort_by = 'created'

    query = Todo.query.filter_by(user_id=current_user.id)

    if filter_by == 'active':
        query = query.filter_by(completed=False)
    elif filter_by == 'completed':
        query = query.filter_by(completed=True)
    elif filter_by == 'high':
        query = query.filter_by(priority='high')
    elif filter_by == 'medium':
        query = query.filter_by(priority='medium')
    elif filter_by == 'low':
        query = query.filter_by(priority='low')

    if sort_by == 'priority':
        query = query.order_by(
            db.case(
                (Todo.priority == 'high', 0),
                (Todo.priority == 'medium', 1),
                (Todo.priority == 'low', 2),
                else_=3
            )
        )
    elif sort_by == 'due':
        query = query.order_by(Todo.due_date.asc().nullslast())
    else:
        query = query.order_by(Todo.created_at.desc())

    todos = query.all()
    stats = {
        'total': Todo.query.filter_by(
            user_id=current_user.id
        ).count(),
        'completed': Todo.query.filter_by(
            user_id=current_user.id, completed=True
        ).count(),
        'active': Todo.query.filter_by(
            user_id=current_user.id, completed=False
        ).count(),
        'high_priority': Todo.query.filter_by(
            user_id=current_user.id, priority='high', completed=False
        ).count(),
    }

    return render_template(
        'dashboard.html',
        todos=todos,
        stats=stats,
        current_filter=filter_by,
        current_sort=sort_by
    )


# ═══════════════════════════════════════════════════════════════
#  HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════

def _validate_title(title):
    """Validate and sanitize todo title."""
    if not title:
        return None, jsonify({'error': 'Title is required.'}), 400
    if len(title) > MAX_TITLE_LENGTH:
        return None, jsonify({
            'error': f'Title must not exceed {MAX_TITLE_LENGTH} characters.',
        }), 400
    return sanitize_plain_text(title), None, None


def _validate_description(description):
    """Validate and sanitize todo description."""
    if not description:
        return description, None, None
    if len(description) > MAX_DESCRIPTION_LENGTH:
        return None, jsonify({
            'error': f'Description must not exceed '
                     f'{MAX_DESCRIPTION_LENGTH} characters.',
        }), 400
    return sanitize_html(description), None, None


def _validate_priority(priority):
    """Validate and return priority."""
    valid_priorities = {'low', 'medium', 'high'}
    if priority not in valid_priorities:
        return 'medium'
    return priority


def _validate_due_date(due_date_str):
    """Validate and parse due date string."""
    if not due_date_str:
        return None, None, None
    try:
        due_date = datetime.fromisoformat(due_date_str)
        if due_date.date() < date.today():
            return None, jsonify({
                'error': 'Due date cannot be in the past.',
            }), 400
        return due_date, None, None
    except (ValueError, TypeError):
        return None, jsonify({
            'error': 'Invalid date format. Use YYYY-MM-DD.',
        }), 400


def _update_title(todo, value):
    """Validate and update todo title."""
    title = value.strip()
    if not title:
        return jsonify({'error': 'Title cannot be empty.'}), 400
    if len(title) > MAX_TITLE_LENGTH:
        return jsonify({
            'error': f'Title must not exceed {MAX_TITLE_LENGTH} characters.',
        }), 400
    todo.title = sanitize_plain_text(title)
    return None, None


def _update_description(todo, value):
    """Validate and update todo description."""
    if len(value) > MAX_DESCRIPTION_LENGTH:
        return jsonify({
            'error': f'Description must not exceed '
                     f'{MAX_DESCRIPTION_LENGTH} characters.',
        }), 400
    todo.description = sanitize_html(value) if value else ''
    return None, None


def _update_completed(todo, value):
    """Validate and update todo completed status."""
    if isinstance(value, bool):
        todo.completed = value
        return None, None
    return jsonify({'error': 'Completed must be a boolean.'}), 400


def _update_priority(todo, value):
    """Validate and update todo priority."""
    valid_priorities = {'low', 'medium', 'high'}
    if value in valid_priorities:
        todo.priority = value
        return None, None
    return jsonify({
        'error': 'Invalid priority. Use low, medium, or high.',
    }), 400


def _update_due_date(todo, value):
    """Validate and update todo due date."""
    if value:
        try:
            todo.due_date = datetime.fromisoformat(value)
        except (ValueError, TypeError):
            return jsonify({
                'error': 'Invalid date format. Use YYYY-MM-DD.',
            }), 400
    else:
        todo.due_date = None
    return None, None


_UPDATE_HANDLERS = {
    'title': _update_title,
    'description': _update_description,
    'completed': _update_completed,
    'priority': _update_priority,
    'due_date': _update_due_date,
}


def _apply_field_update(todo, field, value):
    """Dispatch field update to appropriate handler."""
    handler = _UPDATE_HANDLERS.get(field)
    if handler:
        return handler(todo, value)
    return None, None


# ═══════════════════════════════════════════════════════════════
#  API ROUTES (with CSRF, rate limiting, input sanitization)
# ═══════════════════════════════════════════════════════════════

@main.route('/api/todos', methods=['POST'])
@login_required
@limiter.limit(RATE_LIMIT_API)
@validate_content_type
@require_csrf
def add_todo():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({'error': 'Invalid JSON payload.'}), 400

    allowed_fields = {'title', 'description', 'priority', 'due_date'}
    sanitized = sanitize_json_input(data, allowed_fields)

    title, error, code = _validate_title(sanitized.get('title', '').strip())
    if error:
        return error, code

    description, error, code = _validate_description(
        sanitized.get('description', '')
    )
    if error:
        return error, code

    priority = _validate_priority(sanitized.get('priority', 'medium'))

    due_date, error, code = _validate_due_date(sanitized.get('due_date'))
    if error:
        return error, code

    todo = Todo(
        title=title,
        description=description,
        priority=priority,
        due_date=due_date,
        user_id=current_user.id
    )
    db.session.add(todo)
    db.session.commit()

    return jsonify({
        'id': todo.id,
        'title': todo.title,
        'description': todo.description,
        'completed': todo.completed,
        'priority': todo.priority,
        'created_at': todo.created_at.isoformat(),
        'due_date': todo.due_date.isoformat() if todo.due_date else None,
    }), 201


@main.route('/api/todos/<int:todo_id>', methods=['PUT'])
@login_required
@limiter.limit(RATE_LIMIT_API)
@validate_content_type
@require_csrf
def update_todo(todo_id):
    todo = Todo.query.filter_by(
        id=todo_id, user_id=current_user.id
    ).first_or_404()
    data = request.get_json(silent=True)
    if not data:
        return jsonify({'error': 'Invalid JSON payload.'}), 400

    allowed_fields = {
        'title', 'description', 'completed', 'priority', 'due_date'
    }
    sanitized = sanitize_json_input(data, allowed_fields)

    for field in allowed_fields:
        if field in sanitized:
            error, code = _apply_field_update(todo, field, sanitized[field])
            if error:
                return error, code

    db.session.commit()
    return jsonify({'message': 'Todo updated successfully.'}), 200


@main.route('/api/todos/<int:todo_id>', methods=['DELETE'])
@login_required
@limiter.limit(RATE_LIMIT_API)
@require_csrf
def delete_todo(todo_id):
    todo = Todo.query.filter_by(
        id=todo_id, user_id=current_user.id
    ).first_or_404()
    db.session.delete(todo)
    db.session.commit()
    return jsonify({'message': 'Todo deleted successfully.'}), 200


@main.route('/api/todos/<int:todo_id>/toggle', methods=['POST'])
@login_required
@limiter.limit(RATE_LIMIT_API)
@require_csrf
def toggle_todo(todo_id):
    todo = Todo.query.filter_by(
        id=todo_id, user_id=current_user.id
    ).first_or_404()
    todo.completed = not todo.completed
    db.session.commit()
    return jsonify({'completed': todo.completed}), 200
