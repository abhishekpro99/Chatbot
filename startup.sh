#!/bin/bash

# Optional: activate virtual environment (not needed in Azure App Service Linux, it handles venv itself)

# Collect static files (if needed)
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Run database migrations (optional, safe to run every time)
echo "Applying database migrations..."
python manage.py migrate

# Run the Django app using gunicorn
echo "Starting Gunicorn server..."
gunicorn hr_policy_bot_project.wsgi:application --bind 0.0.0.0:8000 --workers 4 --timeout 120 &


# Start the Bot app (port 3978)
echo "Starting Bot Framework aiohttp app..."
python bot_app.py
