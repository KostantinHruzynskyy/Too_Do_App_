#!/usr/bin/env python3
"""
╔═══════════════════════════════════════════════════╗
║           SKYY – Database Seeder                  ║
║  Populates the database with sample data for      ║
║  development and testing purposes.                ║
╚═══════════════════════════════════════════════════╝

Usage:
    python scripts/seed.py [--users N] [--todos N]
"""

import sys
import os
import argparse
from datetime import datetime, timedelta, timezone

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db, bcrypt  # noqa: E402
from app.models import User, Todo  # noqa: E402


def seed_database(num_users=3, todos_per_user=5):
    """Seed the database with sample data."""
    app = create_app()

    with app.app_context():
        # Clear existing data
        Todo.query.delete()
        User.query.delete()
        db.session.commit()

        priorities = ['low', 'medium', 'high']
        sample_todos = [
            'Review project proposal',
            'Update API documentation',
            'Fix login page styling',
            'Write unit tests for auth',
            'Deploy to staging server',
            'Refactor database models',
            'Add password reset feature',
            'Optimize SQL queries',
            'Create user onboarding flow',
            'Implement dark mode toggle',
            'Set up CI/CD pipeline',
            'Audit security dependencies',
            'Design new dashboard layout',
            'Write integration tests',
            'Update README with setup guide',
        ]

        print(
            f'Seeding database with {num_users} users '
            f'and {todos_per_user} todos each...'
        )

        for i in range(num_users):
            username = f'demo_user_{i + 1}'
            email = f'demo{i + 1}@example.com'

            # Check if user exists
            existing = User.query.filter_by(email=email).first()
            if existing:
                print(f'  Skipping user {username} (already exists)')
                continue

            hashed_pw = bcrypt.generate_password_hash(
                'DemoP@ss123'
            ).decode('utf-8')
            user = User(
                username=username, email=email, password_hash=hashed_pw
            )
            db.session.add(user)
            db.session.flush()

            # Create todos for this user
            for j in range(todos_per_user):
                idx = (i * todos_per_user + j) % len(sample_todos)
                priority = priorities[(i + j) % len(priorities)]
                days_offset = j - 3  # Some past, some future

                todo = Todo(
                    title=sample_todos[idx],
                    description=f'Sample task #{j + 1} for {username}',
                    completed=j % 3 == 0,  # Every 3rd is completed
                    priority=priority,
                    due_date=datetime.now(timezone.utc) + timedelta(
                        days=days_offset
                    ),
                    user_id=user.id,
                )
                db.session.add(todo)

            print(f'  Created user: {username} ({email})')

        db.session.commit()

        # Print summary
        user_count = User.query.count()
        todo_count = Todo.query.count()
        print('\nSummary:')
        print(f'   Users: {user_count}')
        print(f'   Todos: {todo_count}')
        print('\nSeeding complete!')
        print('   Login with: demo_1@example.com / DemoP@ss123')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Seed the Skyy database')
    parser.add_argument('--users', type=int, default=3,
                        help='Number of users to create')
    parser.add_argument('--todos', type=int, default=5,
                        help='Todos per user')
    args = parser.parse_args()

    seed_database(args.users, args.todos)
