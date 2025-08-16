#!/bin/bash

# Customer Feedback Dashboard Setup Script

echo "🚀 Setting up Customer Feedback Dashboard..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file from example..."
    cp env.example .env
    echo "⚠️  Please edit .env file with your actual API keys before continuing."
    echo "   Required: SUPABASE_URL, SUPABASE_ANON_KEY, SUPABASE_SERVICE_ROLE_KEY"
    echo "   Optional but recommended: HUGGINGFACE_API_TOKEN, IBM_WATSON_NLU_API_KEY, REPLICATE_API_TOKEN"
    read -p "Press Enter to continue after editing .env file..."
fi

# Build and start services
echo "🐳 Building Docker containers..."
docker-compose build

echo "🚀 Starting services..."
docker-compose up -d

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 10

# Check service health
echo "🔍 Checking service health..."

# Check backend
if curl -f http://localhost:8000/health &> /dev/null; then
    echo "✅ Backend is running at http://localhost:8000"
else
    echo "❌ Backend is not responding. Check logs with: docker-compose logs backend"
fi

# Check frontend
if curl -f http://localhost:3000 &> /dev/null; then
    echo "✅ Frontend is running at http://localhost:3000"
else
    echo "❌ Frontend is not responding. Check logs with: docker-compose logs frontend"
fi

# Check Redis
if docker-compose exec redis redis-cli ping &> /dev/null; then
    echo "✅ Redis is running"
else
    echo "❌ Redis is not responding. Check logs with: docker-compose logs redis"
fi

echo ""
echo "🎉 Setup complete!"
echo ""
echo "📋 Quick Start:"
echo "   • Frontend: http://localhost:3000"
echo "   • Backend API: http://localhost:8000"
echo "   • API Documentation: http://localhost:8000/docs"
echo ""
echo "🔑 Demo Accounts:"
echo "   • Demo: demo@cfd.app / demo12345 (read-only)"
echo "   • Member: member@cfd.app / member12345 (full features)"
echo "   • Admin: admin@cfd.app / admin12345 (admin features)"
echo ""
echo "🛠️  Useful Commands:"
echo "   • View logs: docker-compose logs -f [service]"
echo "   • Stop services: docker-compose down"
echo "   • Restart services: docker-compose restart"
echo "   • Shell access: docker-compose exec [service] bash"
echo ""
echo "📚 Next Steps:"
echo "   1. Set up your Supabase database using database/schema.sql"
echo "   2. Configure your AI service API keys in .env"
echo "   3. Visit http://localhost:3000 to start using the dashboard"
echo ""
