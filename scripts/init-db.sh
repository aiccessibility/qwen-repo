#!/bin/bash
# Database Initialization Script for Accessibility Platform

set -e

echo "🚀 Initializing database..."

# Wait for PostgreSQL to be ready
echo "⏳ Waiting for PostgreSQL to be ready..."
until pg_isready -h db -p 5432 -U postgres; do
    echo "PostgreSQL is unavailable - sleeping..."
    sleep 2
done

echo "✅ PostgreSQL is ready!"

# Run the initialization SQL
echo "📝 Running database schema initialization..."
psql -h db -U postgres -d accessibility_db -f /docker-entrypoint-initdb.d/init.sql

echo "✅ Database initialized successfully!"

# Create storage directories
echo "📁 Creating storage directories..."
mkdir -p /app/storage/reports/pdf
mkdir -p /app/storage/reports/html
mkdir -p /app/storage/reports/json
mkdir -p /app/storage/screenshots

echo "✅ Storage directories created!"

echo "🎉 Database initialization complete!"
