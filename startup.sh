#!/bin/bash
# Initialize database
python -c "from app import init_db; init_db()"
# Start the application
gunicorn app:app --bind 0.0.0.0:10000