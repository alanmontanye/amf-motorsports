# Render Deployment Guide for AMF Motorsports

## Step 1: Create a New Web Service

1. Go to [render.com](https://render.com/) and sign up or sign in
2. Click "New" then "Web Service"
3. Connect your GitHub account if not already connected
4. Select the repository: **alanmontanye/amf-motorsports**

## Step 2: Configure Web Service Settings

Use these exact settings:

| Setting | Value |
|---------|-------|
| Name | `amf-motorsports` |
| Environment | `Python 3` |
| Region | *Choose closest to you* |
| Branch | `main` |
| Build Command | `chmod +x render_build.sh && ./render_build.sh` |
| Start Command | `gunicorn wsgi:app` |
| Plan | Free |

## Step 3: Environment Variables

Add these environment variables:

| Variable | Value |
|----------|-------|
| `FLASK_CONFIG` | `production` |
| `SECRET_KEY` | `b2988bea7b32c7a1e0991284b672a519` |
| `LOG_TO_STDOUT` | `1` |
| `INIT_KEY` | `amf_init_2025_secure` |

## Step 4: Create PostgreSQL Database

1. On Render dashboard, click "New" and select "PostgreSQL"
2. Use these settings:
   - Name: `amf-motorsports-db`
   - Database: `amf_db`
   - User: *Leave as default*
   - Region: *Same as web service*
   - Plan: Free

3. Once created, go to database "Info" tab
4. Copy the "Internal Connection String"
5. Go back to web service settings → Environment
6. Add new variable: `DATABASE_URL` with the copied connection string

## Step 5: Deploy and Initialize

1. Click "Create Web Service" to deploy your application
2. Wait for the deployment to complete (this may take a few minutes)
3. Once deployed, your application will be available at the URL shown (e.g., `https://amf-motorsports.onrender.com`)

4. To initialize the database, visit this URL in your browser:
   ```
   https://amf-motorsports.onrender.com/admin/initialize-database?key=amf_init_2025_secure
   ```
   
   You should see a JSON response confirming the database was initialized successfully.

## Step 6: Access Your Application

Your application will be available at the URL shown in the Render dashboard, typically:
`https://amf-motorsports.onrender.com`

## Troubleshooting

If you encounter any issues:
1. Check Render logs for errors (available on the Render dashboard)
2. Ensure database connection is working (visible in the logs)
3. Verify environment variables are set correctly
4. If database initialization fails, try visiting the initialization URL again
5. For persistent database issues, you may need to delete and recreate the database
