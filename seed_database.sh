#!/bin/bash

echo "🗄️  Setting up PostgreSQL database..."

echo "⚙️  Running Django migrations..."
python3 manage.py migrate

# Load sample data from JSON files
echo "📊 Loading seed data..."
python3 manage.py loaddata users
python3 manage.py loaddata tokens  
python3 manage.py loaddata types
python3 manage.py loaddata rocks

echo "✅ Database setup complete!"