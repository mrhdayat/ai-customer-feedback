#!/bin/bash

# Customer Feedback Dashboard Docker Test Script

echo "🧪 Testing Customer Feedback Dashboard Docker Setup..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    if [ $2 -eq 0 ]; then
        echo -e "${GREEN}✅ $1${NC}"
    else
        echo -e "${RED}❌ $1${NC}"
    fi
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# Check if .env file exists
if [ ! -f .env ]; then
    print_warning ".env file not found. Creating from example..."
    cp env.example .env
    echo "Please edit .env file with your API keys"
    exit 1
fi

# Start services
echo "🚀 Starting Docker services..."
docker-compose up -d
sleep 15

# Test 1: Check if containers are running
echo ""
echo "🔍 Testing container status..."

# Backend container
if docker-compose ps | grep -q "backend.*Up"; then
    print_status "Backend container is running" 0
else
    print_status "Backend container is not running" 1
    echo "Backend logs:"
    docker-compose logs backend | tail -10
fi

# Frontend container
if docker-compose ps | grep -q "frontend.*Up"; then
    print_status "Frontend container is running" 0
else
    print_status "Frontend container is not running" 1
    echo "Frontend logs:"
    docker-compose logs frontend | tail -10
fi

# Redis container
if docker-compose ps | grep -q "redis.*Up"; then
    print_status "Redis container is running" 0
else
    print_status "Redis container is not running" 1
fi

# Test 2: Health checks
echo ""
echo "🏥 Testing service health..."

# Backend health
if curl -f -s http://localhost:8000/health > /dev/null; then
    print_status "Backend health check passed" 0
    
    # Get health details
    health_response=$(curl -s http://localhost:8000/health)
    echo "Health status: $health_response"
else
    print_status "Backend health check failed" 1
fi

# Frontend accessibility
if curl -f -s http://localhost:3000 > /dev/null; then
    print_status "Frontend is accessible" 0
else
    print_status "Frontend is not accessible" 1
fi

# Test 3: API endpoints
echo ""
echo "🔌 Testing API endpoints..."

# Test auth endpoints
if curl -f -s http://localhost:8000/api/auth/demo-tokens > /dev/null; then
    print_status "Demo tokens endpoint working" 0
else
    print_status "Demo tokens endpoint failed" 1
fi

# Test API documentation
if curl -f -s http://localhost:8000/docs > /dev/null; then
    print_status "API documentation accessible" 0
else
    print_status "API documentation not accessible" 1
fi

# Test 4: Database connectivity (if configured)
echo ""
echo "💾 Testing database connectivity..."

# This would require Supabase to be configured
# For now, we'll just check if the backend can start without errors
backend_logs=$(docker-compose logs backend | grep -i error)
if [ -z "$backend_logs" ]; then
    print_status "No database connection errors in backend logs" 0
else
    print_status "Database connection issues detected" 1
    echo "Error logs: $backend_logs"
fi

# Test 5: Redis connectivity
echo ""
echo "📊 Testing Redis connectivity..."

if docker-compose exec -T redis redis-cli ping | grep -q "PONG"; then
    print_status "Redis connectivity working" 0
else
    print_status "Redis connectivity failed" 1
fi

# Test 6: Environment variables
echo ""
echo "🔐 Testing environment configuration..."

# Check if required env vars are set (non-empty)
required_vars=("SUPABASE_URL" "BACKEND_SECRET_KEY")
all_env_ok=true

for var in "${required_vars[@]}"; do
    if grep -q "^${var}=.\+$" .env; then
        print_status "$var is configured" 0
    else
        print_status "$var is missing or empty" 1
        all_env_ok=false
    fi
done

# Test 7: Port accessibility
echo ""
echo "🌐 Testing port accessibility..."

# Check if ports are actually open
if nc -z localhost 8000 2>/dev/null; then
    print_status "Backend port 8000 is accessible" 0
else
    print_status "Backend port 8000 is not accessible" 1
fi

if nc -z localhost 3000 2>/dev/null; then
    print_status "Frontend port 3000 is accessible" 0
else
    print_status "Frontend port 3000 is not accessible" 1
fi

# Test 8: Performance test
echo ""
echo "⚡ Running basic performance test..."

# Simple response time test
response_time=$(curl -o /dev/null -s -w '%{time_total}' http://localhost:8000/health)
if (( $(echo "$response_time < 2.0" | bc -l) )); then
    print_status "Backend response time: ${response_time}s (Good)" 0
else
    print_status "Backend response time: ${response_time}s (Slow)" 1
fi

# Summary
echo ""
echo "📋 Test Summary:"
echo "=================="

if docker-compose ps | grep -q "Up"; then
    echo -e "${GREEN}✅ Docker services are running${NC}"
else
    echo -e "${RED}❌ Some Docker services are not running${NC}"
fi

if curl -f -s http://localhost:8000/health > /dev/null && curl -f -s http://localhost:3000 > /dev/null; then
    echo -e "${GREEN}✅ All services are accessible${NC}"
else
    echo -e "${RED}❌ Some services are not accessible${NC}"
fi

if [ "$all_env_ok" = true ]; then
    echo -e "${GREEN}✅ Environment configuration looks good${NC}"
else
    echo -e "${YELLOW}⚠️  Please check your environment configuration${NC}"
fi

echo ""
echo "🎯 Quick Access URLs:"
echo "   • Frontend: http://localhost:3000"
echo "   • Backend API: http://localhost:8000"
echo "   • API Docs: http://localhost:8000/docs"
echo "   • Health Check: http://localhost:8000/health"

echo ""
echo "🔧 Useful Commands:"
echo "   • View all logs: docker-compose logs -f"
echo "   • View backend logs: docker-compose logs -f backend"
echo "   • View frontend logs: docker-compose logs -f frontend"
echo "   • Stop services: docker-compose down"
echo "   • Rebuild services: docker-compose build --no-cache"

echo ""
echo "📚 Next Steps:"
echo "   1. Configure your Supabase database with database/schema.sql"
echo "   2. Add your AI service API keys to .env file"
echo "   3. Restart services: docker-compose restart"
echo "   4. Visit http://localhost:3000 and try the demo accounts"

echo ""
echo "🏁 Testing completed!"
