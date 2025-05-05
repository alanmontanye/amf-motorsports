#!/usr/bin/env python
"""
GitHub Repository Setup Utility for AMF Motorsports
"""
import os
import subprocess
import sys
import time

def load_github_env():
    """Load GitHub environment variables from .github-env file"""
    env_vars = {}
    
    if not os.path.exists('.github-env'):
        print("Error: .github-env file not found!")
        print("Please create this file with your GitHub details.")
        return None
    
    with open('.github-env', 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                env_vars[key] = value
    
    # Validate required variables
    required_vars = ['GITHUB_USERNAME', 'GITHUB_EMAIL']
    for var in required_vars:
        if not env_vars.get(var):
            print(f"Error: {var} is missing or empty in .github-env")
            return None
    
    # Fill in repo URL if needed
    if not env_vars.get('GITHUB_REPO_URL') or '//' in env_vars['GITHUB_REPO_URL']:
        username = env_vars['GITHUB_USERNAME']
        repo_name = env_vars.get('GITHUB_REPO_NAME', 'amf-motorsports')
        env_vars['GITHUB_REPO_URL'] = f"https://github.com/{username}/{repo_name}.git"
    
    return env_vars

def run_command(command):
    """Run a shell command and return True if successful"""
    try:
        subprocess.run(command, shell=True, check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error executing: {command}")
        print(f"Error details: {e}")
        return False

def configure_git(username, email):
    """Configure Git with the provided username and email"""
    print(f"Configuring Git with username: {username}")
    if not run_command(f'git config --global user.name "{username}"'):
        return False
    
    print(f"Configuring Git with email: {email}")
    if not run_command(f'git config --global user.email "{email}"'):
        return False
    
    return True

def setup_and_push(repo_url):
    """Set up Git remote and push to GitHub"""
    # First check if origin already exists
    try:
        result = subprocess.run('git remote -v', shell=True, capture_output=True, text=True)
        if 'origin' in result.stdout:
            # Remove existing origin
            print("Removing existing origin remote...")
            run_command('git remote remove origin')
    except Exception:
        pass
    
    # Add new origin
    print(f"Adding remote repository: {repo_url}")
    if not run_command(f'git remote add origin {repo_url}'):
        return False
    
    # Rename branch to main if needed
    print("Renaming branch to main...")
    run_command('git branch -M main')
    
    # Push to GitHub
    print("Pushing code to GitHub...")
    if not run_command('git push -u origin main'):
        print("\nPush failed. You might need to:")
        print("1. Create the repository on GitHub first")
        print("2. Ensure you have the correct permissions")
        print("3. Check your internet connection")
        return False
    
    return True

def main():
    """Main function to configure and push to GitHub"""
    print("===== GitHub Repository Setup =====")
    
    # Load environment variables
    env_vars = load_github_env()
    if not env_vars:
        sys.exit(1)
    
    # Configure Git
    if not configure_git(env_vars['GITHUB_USERNAME'], env_vars['GITHUB_EMAIL']):
        sys.exit(1)
    
    # Push to GitHub
    if not setup_and_push(env_vars['GITHUB_REPO_URL']):
        sys.exit(1)
    
    print("\n===== Success! =====")
    print(f"Your code has been pushed to: {env_vars['GITHUB_REPO_URL']}")
    print("\nNext steps:")
    print("1. Go to Render.com and create an account (if you don't have one)")
    print("2. Click 'New Web Service' and connect your GitHub account")
    print("3. Select the repository you just created")
    print("4. Configure your Render web service with these settings:")
    print("   - Build Command: pip install -r requirements.txt")
    print("   - Start Command: gunicorn wsgi:app")
    print("5. Set the following environment variables in Render:")
    print("   - FLASK_CONFIG: production")
    print("   - SECRET_KEY: (generate a random string)")
    print("   - LOG_TO_STDOUT: 1")
    print("6. Deploy your application!")

if __name__ == "__main__":
    main()
