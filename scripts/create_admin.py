#!/usr/bin/env python3
"""
╔═══════════════════════════════════════════════════╗
║           SKYY – Create Admin User                ║
║  Creates an admin user for the application        ║
╚═══════════════════════════════════════════════════╝

Usage:
    python scripts/create_admin.py
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db, bcrypt  # noqa: E402
from app.models import User  # noqa: E402


def create_admin():
    """Create an admin user."""
    app = create_app()

    with app.app_context():
        # Admin credentials
        admin_username = "admin"
        admin_email = "admin@skyy.app"
        admin_password = "AdminP@ss123!"

        # Check if admin already exists
        existing_admin = User.query.filter_by(email=admin_email).first()
        if existing_admin:
            print(f"Admin user already exists: {admin_email}")
            print(f"   Username: {admin_username}")
            print(f"   Is Admin: {existing_admin.is_admin}")
            return

        # Check if username is taken
        existing_username = User.query.filter_by(
            username=admin_username
        ).first()
        if existing_username:
            print(f"Username '{admin_username}' is already taken")
            return

        # Create admin user
        hashed_pw = bcrypt.generate_password_hash(
            admin_password
        ).decode('utf-8')
        admin = User(
            username=admin_username,
            email=admin_email,
            password_hash=hashed_pw,
            is_admin=True
        )

        db.session.add(admin)
        db.session.commit()

        print("=" * 60)
        print("  ADMIN USER CREATED SUCCESSFULLY!")
        print("=" * 60)
        print(f"\n  Username: {admin_username}")
        print(f"  Email:    {admin_email}")
        print(f"  Password: {admin_password}")
        print("\n  Please change the password after first login!")
        print("=" * 60)


if __name__ == "__main__":
    create_admin()
