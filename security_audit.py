import os
import re


def safe_read(path):
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()


def check_secrets():
    """Check for hardcoded secrets."""
    print("1. Checking for hardcoded secrets...")
    secrets_found = []
    for root, dirs, files in os.walk("app"):
        for f in files:
            if f.endswith(".py"):
                path = os.path.join(root, f)
                content = safe_read(path)
                if "password = " in content and "os.getenv" not in content:
                    matches = re.findall(
                        r"password\s*=\s*[\"']([^\"']+)[\"']", content
                    )
                    for m in matches:
                        if m not in ["password", ""]:
                            secrets_found.append(f"{path}: {m}")
    if secrets_found:
        print("   WARNING:")
        for s in secrets_found:
            print("   -", s)
    else:
        print("   OK")


def check_sql_injection():
    """Check for SQL injection."""
    print("\n2. Checking SQL injection...")
    sql_issues = []
    for root, dirs, files in os.walk("app"):
        for f in files:
            if f.endswith(".py"):
                path = os.path.join(root, f)
                content = safe_read(path)
                if "execute(" in content and "text(" not in content:
                    sql_issues.append(f"{path}: raw execute")
    if sql_issues:
        print("   WARNING:")
        for s in sql_issues:
            print("   -", s)
    else:
        print("   OK")


def check_xss():
    """Check for XSS vulnerabilities."""
    print("\n3. Checking XSS...")
    xss = []
    for root, dirs, files in os.walk("app"):
        for f in files:
            if f.endswith(".py"):
                path = os.path.join(root, f)
                content = safe_read(path)
                if "render_template_string" in content:
                    xss.append(f"{path}")
    if xss:
        print("   WARNING:")
        for x in xss:
            print("   -", x)
    else:
        print("   OK")


def check_debug():
    """Check for debug mode."""
    print("\n4. Checking debug mode...")
    debug = []
    for root, dirs, files in os.walk("."):
        for f in files:
            if f.endswith(".py"):
                path = os.path.join(root, f)
                content = safe_read(path)
                if "debug=True" in content:
                    debug.append(f"{path}")
    if debug:
        print("   WARNING:")
        for d in debug:
            print("   -", d)
    else:
        print("   OK")


if __name__ == "__main__":
    print("=== Security Audit ===\n")
    check_secrets()
    check_sql_injection()
    check_xss()
    check_debug()
    print("\n=== DONE ===")
