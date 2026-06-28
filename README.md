# ☁️ Skyy — Professional To-Do App

> **v2.0.0** — Enterprise-grade task management built with Python/Flask

[![Python](https://img.shields.io/badge/Python-3.12-blue)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.0-black)](https://flask.palletsprojects.com)
[![Security](https://img.shields.io/badge/Security-Enterprise-green)](app/security.py)
[![License](https://img.shields.io/badge/License-MIT-purple)](LICENSE)

---

## ✨ Features

- **🔐 Enterprise Security** — XSS prevention, CSRF protection, rate limiting, CSP headers, HSTS, brute-force lockout, password policy enforcement
- **👤 User Authentication** — Register, login, logout with bcrypt hashing & session management
- **📋 Full CRUD** — Create, read, update, delete tasks via REST API
- **🏷️ Smart Filtering** — All, Active, Completed, High/Medium/Low priority
- **📅 Due Dates** — Optional with overdue detection
- **🎨 Professional UI** — Dark theme, gradient accents, floating cards, fully responsive
- **🐳 Docker Ready** — Multi-stage build, Docker Compose with PostgreSQL + Redis + Nginx
- **🧪 Tested** — Comprehensive test suite with pytest
- **📊 Health Checks** — Liveness/readiness endpoint for container orchestration

---

## 🚀 Quick Start

### Prerequisites

- Python 3.12+
- pip

### Installation

```bash
# Clone the repository
git clone https://github.com/KostantinHruzynskyy/Too_Do_App.git
cd Too_Do_App

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt

# Run the app
python run.py
```

Open **http://127.0.0.1:5000** in your browser.

### Seed Sample Data

```bash
python scripts/seed.py --users 3 --todos 5
```

Login with: `demo_1@example.com` / `DemoP@ss123`

---

## 🐳 Docker Deployment

```bash
# Build and start the full stack
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

The stack includes:
- **Skyy Web** — Flask app with Gunicorn
- **PostgreSQL** — Production database
- **Redis** — Rate limiting & session storage
- **Nginx** — Reverse proxy with SSL termination

---

## 🧪 Testing

```bash
# Run all tests
python -m pytest tests/ -v

# With coverage
python -m pytest tests/ -v --cov=app --cov-report=term-missing
```

---

## 🛡️ Security

Skyy implements enterprise-grade security measures:

| Protection | Implementation |
|---|---|
| **XSS Prevention** | Input sanitization with `bleach`, HTML escaping |
| **SQL Injection** | Parameterized queries via SQLAlchemy ORM |
| **CSRF Protection** | Token-based validation for API routes |
| **Rate Limiting** | Per-endpoint limits (Flask-Limiter + Redis) |
| **Brute Force** | IP-based login attempt tracking & lockout |
| **Password Policy** | Min 12 chars, complexity requirements, common-pass blacklist |
| **Session Hardening** | HTTPOnly, Secure, SameSite cookies |
| **Security Headers** | CSP, HSTS, X-Frame-Options, X-Content-Type-Options |
| **Open Redirect** | Next-URL validation against allowlist |
| **Request Size** | 100KB max body limit |

---

## 📁 Project Structure

```
Too_Do_App/
├── app/
│   ├── __init__.py          # Flask app factory
│   ├── config.py            # Environment-based configuration
│   ├── health.py            # Health check endpoint
│   ├── logger.py            # Structured logging with rotation
│   ├── models.py            # User & Todo SQLAlchemy models
│   ├── routes.py            # Secure routes with validation
│   ├── security.py          # Enterprise security module
│   ├── static/
│   │   ├── css/style.css    # Professional dark theme
│   │   └── js/main.js       # Async CRUD operations
│   └── templates/
│       ├── base.html        # Base template
│       ├── index.html       # Landing page
│       ├── login.html       # Sign in
│       ├── register.html    # Sign up
│       └── dashboard.html   # Main app
├── tests/
│   ├── __init__.py
│   └── test_auth.py         # 20+ test cases
├── scripts/
│   └── seed.py              # Database seeder
├── logs/                    # Application logs
├── migrations/              # Database migrations
├── Dockerfile               # Multi-stage build
├── docker-compose.yml       # Full production stack
├── nginx.conf               # Nginx reverse proxy config
├── .env.example             # Environment template
├── .gitignore
├── Makefile                 # Common commands
├── requirements.txt         # Python dependencies
└── run.py                   # Entry point
```

---

## 🔧 Configuration

Copy `.env.example` to `.env` and customize:

```env
SECRET_KEY=your-256-bit-secret-key
DATABASE_URL=sqlite:///skyy_todo.db
FLASK_ENV=development
```

---

## 📸 Screenshots

| Landing | Dashboard |
|---|---|
| ![Landing](https://via.placeholder.com/400x250/1a1a2e/818cf8?text=Skyy+Landing) | ![Dashboard](https://via.placeholder.com/400x250/16213e/10b981?text=Skyy+Dashboard) |

---

## 👨‍💻 Author

**Kostantin Hruzynskyy**

[![GitHub](https://img.shields.io/badge/GitHub-KostantinHruzynskyy-181717?logo=github)](https://github.com/KostantinHruzynskyy)

---

## 📄 License

This project is licensed under the MIT License.