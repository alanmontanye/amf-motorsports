#!/usr/bin/env python
"""
Deployment utility script for AMF Motorsports app
"""
import os
import subprocess
import argparse
import sys
from datetime import datetime

def run_command(command, description=None):
    """Run a shell command and print its output"""
    if description:
        print(f"\n{description}...")
    
    try:
        result = subprocess.run(command, shell=True, check=True, 
                               text=True, capture_output=True)
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")
        if e.stderr:
            print(f"Error details: {e.stderr}")
        return False

def backup_database():
    """Create a database backup"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = os.path.join(os.getcwd(), 'backups')
    os.makedirs(backup_dir, exist_ok=True)
    
    backup_file = os.path.join(backup_dir, f'app_db_backup_{timestamp}.db')
    
    # Create backup
    import shutil
    try:
        shutil.copy('app.db', backup_file)
        print(f"Database backed up to {backup_file}")
        return True
    except Exception as e:
        print(f"Backup failed: {e}")
        return False

def prepare_for_heroku():
    """Prepare the app for Heroku deployment"""
    # Check if git is initialized
    if not os.path.exists('.git'):
        run_command('git init', 'Initializing git repository')
    
    # Check if Heroku CLI is installed
    if not run_command('heroku --version', 'Checking Heroku CLI'):
        print("Heroku CLI is not installed. Please install it first.")
        return False
    
    # Create necessary files if they don't exist
    if not os.path.exists('Procfile'):
        with open('Procfile', 'w') as f:
            f.write('web: gunicorn wsgi:app')
        print("Created Procfile")
    
    if not os.path.exists('runtime.txt'):
        with open('runtime.txt', 'w') as f:
            f.write('python-3.11.7')  # Adjust based on your Python version
        print("Created runtime.txt")
    
    # Update .gitignore if needed
    if not os.path.exists('.gitignore'):
        run_command('curl -o .gitignore https://raw.githubusercontent.com/github/gitignore/main/Python.gitignore',
                  'Creating .gitignore')
    
    print("App is ready for Heroku deployment")
    print("Next steps:")
    print("1. Run 'git add .'")
    print("2. Run 'git commit -m \"Prepare for deployment\"'")
    print("3. Run 'heroku create'")
    print("4. Run 'git push heroku main'")
    
    return True

def setup_docker():
    """Set up Docker environment"""
    if not run_command('docker --version', 'Checking Docker installation'):
        print("Docker is not installed. Please install Docker first.")
        return False
    
    if not run_command('docker-compose --version', 'Checking Docker Compose installation'):
        print("Docker Compose is not installed. Please install it first.")
        return False
    
    print("Docker environment is ready")
    print("To build and start the app, run 'docker-compose up -d'")
    return True

def set_environment_mode(mode):
    """Set the environment mode (development or production)"""
    env_file = '.env'
    env_vars = {}
    
    # Read existing env file if it exists
    if os.path.exists(env_file):
        with open(env_file, 'r') as f:
            for line in f:
                if '=' in line and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    env_vars[key] = value
    
    # Update FLASK_CONFIG
    env_vars['FLASK_CONFIG'] = mode
    
    # Write back to file
    with open(env_file, 'w') as f:
        for key, value in env_vars.items():
            f.write(f"{key}={value}\n")
    
    print(f"Environment mode set to {mode}")
    return True

def check_mobile_readiness():
    """Assess mobile readiness of the application"""
    issues_found = []
    
    # Check base template for viewport meta tag
    base_template = os.path.join('app', 'templates', 'base.html')
    if os.path.exists(base_template):
        with open(base_template, 'r') as f:
            content = f.read()
            if 'viewport' not in content:
                issues_found.append("Missing viewport meta tag in base template")
            if 'bootstrap' not in content.lower():
                issues_found.append("Bootstrap might not be included in base template")
    else:
        issues_found.append("Base template not found")
    
    # Check CSS for media queries
    css_file = os.path.join('app', 'static', 'css', 'style.css')
    if os.path.exists(css_file):
        with open(css_file, 'r') as f:
            content = f.read()
            if '@media' not in content:
                issues_found.append("No media queries found in CSS")
    else:
        issues_found.append("Main CSS file not found")
    
    # Print results
    if issues_found:
        print("Mobile optimization issues found:")
        for issue in issues_found:
            print(f"- {issue}")
    else:
        print("Application appears to be mobile-ready!")
        print("Remember to test on actual mobile devices or using browser dev tools.")
    
    return len(issues_found) == 0

def main():
    parser = argparse.ArgumentParser(description='AMF Motorsports Deployment Utility')
    
    # Create subparsers for different commands
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # Backup command
    backup_parser = subparsers.add_parser('backup', help='Backup the database')
    
    # Heroku command
    heroku_parser = subparsers.add_parser('heroku', help='Prepare for Heroku deployment')
    
    # Docker command
    docker_parser = subparsers.add_parser('docker', help='Set up Docker environment')
    
    # Mode command
    mode_parser = subparsers.add_parser('mode', help='Set environment mode')
    mode_parser.add_argument('mode_name', choices=['development', 'production'], 
                           help='Environment mode to set')
    
    # Mobile command
    mobile_parser = subparsers.add_parser('mobile', help='Check mobile readiness')
    
    args = parser.parse_args()
    
    if args.command == 'backup':
        backup_database()
    elif args.command == 'heroku':
        prepare_for_heroku()
    elif args.command == 'docker':
        setup_docker()
    elif args.command == 'mode':
        set_environment_mode(args.mode_name)
    elif args.command == 'mobile':
        check_mobile_readiness()
    else:
        parser.print_help()

if __name__ == '__main__':
    main()
