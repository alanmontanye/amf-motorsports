import os
from app import create_app

# Get the FLASK_CONFIG environment variable, defaulting to 'default'
app_config = os.environ.get('FLASK_CONFIG', 'default')
app = create_app(app_config)

if __name__ == "__main__":
    # For development server only - use gunicorn in production
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
