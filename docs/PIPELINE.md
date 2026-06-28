# ═══════════════════════════════════════════════════
#  SKYY – Development Pipeline & Checklist
#  Follow this process for every change
# ═══════════════════════════════════════════════════

## 📋 Pre-Development Checklist

- [ ] Read and understand the requirement
- [ ] Check existing code structure (`app/`, `tests/`, `scripts/`)
- [ ] Review security policies in `app/security.py`
- [ ] Plan the changes (routes, templates, models, tests)

---

## 🔧 Development Phase

### 1. Backend Changes
- [ ] Update `app/routes.py` (add/modify routes)
- [ ] Update `app/models.py` if database schema changes
- [ ] Add input validation & sanitization (use `app/security.py` helpers)
- [ ] Add rate limiting where needed (`@limiter.limit()`)
- [ ] Add CSRF protection for API routes (`@require_csrf`)
- [ ] Update `app/__init__.py` if new blueprints/extensions needed

### 2. Frontend Changes
- [ ] Create/update templates in `app/templates/`
- [ ] Update JavaScript in `app/static/js/main.js`
- [ ] Add CSS styles (inline or separate file)
- [ ] Ensure responsive design (mobile + desktop)
- [ ] Test all forms and buttons

### 3. Security Review
- [ ] All user input sanitized (`sanitize_plain_text`, `sanitize_html`)
- [ ] All API routes have CSRF + rate limiting
- [ ] No SQL injection risks (use SQLAlchemy ORM)
- [ ] No XSS vulnerabilities (escape output in templates)
- [ ] No open redirects (validate `next` URLs)
- [ ] Password policy enforced (12+ chars, complexity)

---

## 🧪 Testing Phase

### 1. Run Test Suite
```bash
python -m pytest tests/ -v --tb=short
```
- [ ] All tests pass (61/61)
- [ ] No warnings or errors
- [ ] Coverage report generated

### 2. Manual Testing
- [ ] Start server: `python run.py`
- [ ] Test registration (new user gets example tasks)
- [ ] Test login/logout
- [ ] Test task CRUD (create, read, update, delete)
- [ ] Test filtering & sorting
- [ ] Test on mobile viewport
- [ ] Check browser console for errors

### 3. Security Testing
```bash
python security_audit.py
```
- [ ] No critical vulnerabilities found
- [ ] All security headers present
- [ ] CSRF tokens working
- [ ] Rate limiting active

---

## 🚀 Deployment Phase

### 1. Build Executable (Windows)
```bash
python build_exe.py
```
- [ ] `dist/TooDooApp.exe` created
- [ ] Executable runs without errors
- [ ] No missing dependencies

### 2. Docker Build (if applicable)
```bash
docker-compose up --build
```
- [ ] Container starts successfully
- [ ] All services running (app, db, nginx)
- [ ] Health check passes

### 3. Git Commit
```bash
git add .
git commit -m "feat: description of changes"
git push origin main
```
- [ ] Commit message follows convention
- [ ] No sensitive data in commit (passwords, keys)
- [ ] `.env` not committed (check `.gitignore`)

---

## ✅ CI/CD Pipeline (GitHub Actions)

The pipeline runs automatically on push/PR:

### Job 1: Tests & Security (`test`)
- [ ] ✅ Checkout code
- [ ] ✅ Install dependencies
- [ ] ✅ Lint with flake8
- [ ] ✅ Security audit (`security_audit.py`)
- [ ] ✅ Run pytest with coverage
- [ ] ✅ Upload coverage report

### Job 2: Build Executable (`build`)
- [ ] ✅ Runs only on `main` branch
- [ ] ✅ Builds `TooDooApp.exe`
- [ ] ✅ Uploads artifact (30-day retention)

### Job 3: Docker Build (`docker`)
- [ ] ✅ Runs only on `main` branch
- [ ] ✅ Builds Docker image
- [ ] ✅ Caches layers for speed

---

## 📊 Post-Deployment Checklist

- [ ] Verify app is accessible (http://127.0.0.1:5000)
- [ ] Check logs for errors (`logs/skyy.log`)
- [ ] Monitor performance (response times)
- [ ] Review security audit results
- [ ] Update documentation if needed
- [ ] Notify team of changes

---

## 🐛 Bug Fixes

When fixing bugs:
1. [ ] Reproduce the bug locally
2. [ ] Write a failing test case
3. [ ] Fix the code
4. [ ] Verify test passes
5. [ ] Check for similar issues elsewhere
6. [ ] Update documentation if needed

---

## 🔄 Feature Development

When adding features:
1. [ ] Create feature branch: `git checkout -b feature/name`
2. [ ] Implement backend (routes, models, validation)
3. [ ] Implement frontend (templates, JS, CSS)
4. [ ] Write tests (unit + integration)
5. [ ] Run full test suite
6. [ ] Security review
7. [ ] Merge to `develop` branch
8. [ ] Create PR to `main`
9. [ ] Wait for CI/CD to pass
10. [ ] Merge and deploy

---

## 📝 Code Review Checklist

Before merging PRs:
- [ ] Code follows project style (PEP 8)
- [ ] All tests pass
- [ ] No security vulnerabilities
- [ ] Documentation updated
- [ ] No console.log or debug statements
- [ ] Error handling implemented
- [ ] Input validation present
- [ ] Rate limiting added (if needed)
- [ ] CSRF protection (if needed)

---

## 🚨 Emergency Hotfix

For critical production bugs:
1. [ ] Create hotfix branch from `main`
2. [ ] Fix the issue
3. [ ] Run tests
4. [ ] Fast-track review
5. [ ] Merge to `main`
6. [ ] Deploy immediately
7. [ ] Backport to `develop`

---

## 📚 Documentation

Keep docs updated:
- [ ] `README.md` – Setup instructions
- [ ] `SECURITY.md` – Security policies
- [ ] `docs/API.md` – API endpoints
- [ ] `docs/PIPELINE.md` – This file
- [ ] Code comments for complex logic

---

## 🎯 Quality Gates

Every change must pass:
- ✅ All tests (61/61)
- ✅ Lint checks (flake8)
- ✅ Security audit (no critical issues)
- ✅ Code review (1+ approvals)
- ✅ CI/CD pipeline (green)
- ✅ Manual testing (smoke test)

---

## 📞 Support

- **Issues**: GitHub Issues
- **Security**: security@skyy.app
- **Docs**: `/docs` folder
- **Logs**: `logs/skyy.log`

---

**Last Updated**: 2024
**Version**: 1.0.0
**Maintainer**: Kostantin Hruzynskyy