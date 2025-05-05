# AMF Motorsports ATV Management System

A comprehensive management system for tracking ATVs, parts, expenses, and sales for AMF Motorsports.

## Features

- Financial tracking for each ATV
- Parts inventory management
- eBay integration for listings and sales
- AI-powered part description generation
- Expense and income tracking
- Reporting and analytics

## Setup

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables in `.env`:
```
SECRET_KEY=your-secret-key
EBAY_APP_ID=your-ebay-app-id
OPENAI_API_KEY=your-openai-api-key
FLASK_CONFIG=development  # Use 'production' for production deployment
```

4. Initialize the database:
```bash
flask db upgrade
```

5. Run the development server:
```bash
flask run
```

## Deployment Options

### Deploying to Heroku

1. Create a Heroku account and install the Heroku CLI
2. Log in to Heroku and create a new app:
```bash
heroku login
heroku create amf-motorsports
```

3. Add PostgreSQL database:
```bash
heroku addons:create heroku-postgresql:hobby-dev
```

4. Set environment variables:
```bash
heroku config:set SECRET_KEY=your-production-secret-key
heroku config:set FLASK_CONFIG=production
heroku config:set LOG_TO_STDOUT=1
heroku config:set OPENAI_API_KEY=your-openai-api-key
heroku config:set EBAY_APP_ID=your-ebay-app-id
```

5. Deploy your application:
```bash
git push heroku main
```

6. Migrate data to PostgreSQL:
```bash
heroku run python db_migration_utils.py migrate
```

### Docker Deployment

1. Build and run with Docker Compose:
```bash
docker-compose up -d
```

2. Migrate data to PostgreSQL:
```bash
docker-compose exec web python db_migration_utils.py migrate
```

### Manual VPS Deployment

1. Set up a VPS with Ubuntu/Debian
2. Install dependencies:
```bash
sudo apt-get update
sudo apt-get install -y python3-pip python3-venv postgresql nginx
```

3. Clone the repository and set up virtual environment
4. Configure PostgreSQL database
5. Set up Gunicorn as a service
6. Configure Nginx as a reverse proxy

## Mobile Optimization

The application has been optimized for mobile use with:

- Responsive design using Bootstrap 5
- Mobile-optimized navigation with collapsible menu
- Touch-friendly buttons and interface elements
- Optimized tables and forms for smaller screens
- Reduced image sizes for faster loading on mobile networks

To test mobile optimization:
1. Access the application on your mobile device
2. Use browser developer tools to simulate various device sizes
3. Ensure all functionality works correctly on smaller screens

## Project Structure

- `/app`: Main application package
  - `/static`: CSS, JavaScript, and other static files
  - `/templates`: HTML templates
  - `/models.py`: Database models
  - `/routes`: Route handlers for different modules
- `/migrations`: Database migrations
- `config.py`: Application configuration
- `requirements.txt`: Python dependencies

## Contributing

1. Create a new branch for your feature
2. Make your changes
3. Submit a pull request

## License

This project is proprietary and confidential. All rights reserved.
