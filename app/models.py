from app import db, login_manager
from flask_login import UserMixin
from datetime import datetime, timezone


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(
        db.String(80), unique=True, nullable=False, index=True
    )
    email = db.Column(
        db.String(120), unique=True, nullable=False, index=True
    )
    password_hash = db.Column(db.String(128), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )
    todos = db.relationship(
        'Todo', backref='author', lazy='dynamic',
        cascade='all, delete-orphan'
    )

    def __repr__(self):
        return f'<User {self.username}>'


class Todo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    completed = db.Column(db.Boolean, default=False)
    priority = db.Column(db.String(10), default='medium')
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )
    due_date = db.Column(db.DateTime, nullable=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey('user.id'), nullable=False
    )

    def __repr__(self):
        return f'<Todo {self.title}>'
