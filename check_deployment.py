#!/usr/bin/env python
"""
Deployment readiness checker for AMF Motorsports app
"""
import os
import sys
import importlib.util
import subprocess
import platform
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible"""
    version = sys.version_info
    print(f"Python version: {version.major}.{version.minor}.{version.micro}")
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python 3.8+ is recommended")
        return False
    else:
        print("✅ Python version is compatible")
        return True

def check_required_files():
    """Check if all required files for deployment exist"""
    required_files = [
        'wsgi.py',
        'Procfile',
        'runtime.txt',
        'requirements.txt',
        '.env',
        'app/__init__.py',
        'config.py'
    ]
    
    all_exist = True
    print("\nChecking required files:")
    
    for file in required_files:
        if os.path.exists(file):
            print(f"✅ {file} exists")
        else:
            print(f"❌ {file} is missing")
            all_exist = False
    
    return all_exist

def check_database():
    """Check if database exists and can be accessed"""
    print("\nChecking database:")
    
    if not os.path.exists('app.db'):
        print("❌ SQLite database not found")
        return False
    
    try:
        import sqlite3
        conn = sqlite3.connect('app.db')
        cursor = conn.cursor()
        
        # Get list of tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        if not tables:
            print("❌ Database exists but contains no tables")
            return False
        
        print(f"✅ Database exists with {len(tables)} tables")
        return True
    except Exception as e:
        print(f"❌ Error accessing database: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

def check_dependencies():
    """Check if all dependencies can be imported"""
    print("\nChecking dependencies:")
    
    dependencies = [
        "flask",
        "flask_sqlalchemy",
        "flask_migrate",
        "werkzeug",
        "gunicorn",
        "psycopg2",
        "whitenoise"
    ]
    
    all_installed = True
    
    for dep in dependencies:
        try:
            importlib.import_module(dep.replace('-', '_'))
            print(f"✅ {dep} is installed")
        except ImportError:
            print(f"❌ {dep} is not installed")
            all_installed = False
    
    return all_installed

def check_environment_variables():
    """Check if required environment variables are set"""
    print("\nChecking environment variables:")
    
    env_file_path = '.env'
    required_vars = [
        'SECRET_KEY',
        'FLASK_CONFIG',
    ]
    
    if not os.path.exists(env_file_path):
        print("❌ .env file not found")
        return False
    
    # Read .env file
    env_vars = {}
    with open(env_file_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                env_vars[key] = value
    
    all_set = True
    for var in required_vars:
        if var in env_vars and env_vars[var]:
            print(f"✅ {var} is set")
        else:
            print(f"❌ {var} is not set")
            all_set = False
    
    return all_set

def check_network_ports():
    """Check if required network ports are available"""
    print("\nChecking network ports:")
    
    ports_to_check = [5000, 8000]
    platform_system = platform.system()
    
    for port in ports_to_check:
        if platform_system == 'Windows':
            cmd = f"netstat -an | findstr :{port}"
        else:  # Linux/Mac
            cmd = f"netstat -an | grep ':{port}'"
        
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            if port == 5000 and not result.stdout:
                print(f"✅ Port {port} is available for development")
            elif port == 8000 and not result.stdout:
                print(f"✅ Port {port} is available for production")
            else:
                print(f"❌ Port {port} is in use")
        except Exception as e:
            print(f"❓ Could not check port {port}: {e}")

def check_mobile_responsive():
    """Check if the app has mobile-responsive elements"""
    print("\nChecking mobile responsiveness:")
    
    # Check for responsive meta tag in base template
    base_template_path = Path('app/templates/base.html')
    if not base_template_path.exists():
        print("❌ Base template not found")
    else:
        with open(base_template_path, 'r') as f:
            content = f.read()
            if 'viewport' in content and 'width=device-width' in content:
                print("✅ Responsive viewport meta tag found")
            else:
                print("❌ Responsive viewport meta tag not found")
    
    # Check for media queries in CSS
    css_path = Path('app/static/css/style.css')
    if not css_path.exists():
        print("❌ Main CSS file not found")
    else:
        with open(css_path, 'r') as f:
            content = f.read()
            if '@media' in content:
                print("✅ Media queries found in CSS")
            else:
                print("❌ No media queries found in CSS")

def main():
    """Run all checks and summarize results"""
    print("======================================================")
    print("AMF Motorsports Deployment Readiness Check")
    print("======================================================\n")
    
    results = []
    results.append(("Python Version", check_python_version()))
    results.append(("Required Files", check_required_files()))
    results.append(("Database", check_database()))
    results.append(("Dependencies", check_dependencies()))
    results.append(("Environment Variables", check_environment_variables()))
    check_network_ports()  # No boolean return
    check_mobile_responsive()  # No boolean return
    
    # Summarize results
    print("\n======================================================")
    print("Deployment Readiness Summary")
    print("======================================================")
    
    all_passed = True
    for name, result in results:
        if result:
            print(f"✅ {name}: Ready")
        else:
            print(f"❌ {name}: Not Ready")
            all_passed = False
    
    if all_passed:
        print("\n🎉 Your application is ready for deployment!")
    else:
        print("\n⚠️ Your application needs some fixes before deployment.")
    
    print("\nFor additional details on deployment, see README.md")

if __name__ == "__main__":
    main()
