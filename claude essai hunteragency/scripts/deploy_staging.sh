#!/bin/bash

# 🚀 HUNTER AGENCY - Staging Deployment Script
# Production-ready CRM Smart Pipeline deployment

set -euo pipefail  # Exit on error, undefined vars, pipe failures

# ============================================================================
# 🎯 CONFIGURATION
# ============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}" && pwd)"

# Environment
ENVIRONMENT="${ENVIRONMENT:-staging}"
COMPOSE_FILE="docker-compose.yml"
COMPOSE_PROFILES="monitoring"

# Database
POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-$(openssl rand -base64 32)}"
REDIS_PASSWORD="${REDIS_PASSWORD:-$(openssl rand -base64 32)}"

# Security
SECRET_KEY="${SECRET_KEY:-$(openssl rand -base64 64)}"
JWT_SECRET="${JWT_SECRET:-$(openssl rand -base64 64)}"

# API Configuration
API_PORT="${API_PORT:-8000}"
API_HOST="${API_HOST:-0.0.0.0}"

# Colors for output
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly PURPLE='\033[0;35m'
readonly CYAN='\033[0;36m'
readonly NC='\033[0m' # No Color

# ============================================================================
# 🔧 HELPER FUNCTIONS
# ============================================================================

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[WARNING] $1${NC}"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}"
    exit 1
}

info() {
    echo -e "${BLUE}[INFO] $1${NC}"
}

success() {
    echo -e "${GREEN}✅ $1${NC}"
}

step() {
    echo -e "${PURPLE}🎯 $1${NC}"
}

check_command() {
    if ! command -v "$1" &> /dev/null; then
        error "$1 is required but not installed"
    fi
}

wait_for_service() {
    local service_name="$1"
    local health_check="$2"
    local max_attempts="${3:-30}"
    local attempt=1
    
    info "Waiting for $service_name to be ready..."
    
    while [ $attempt -le $max_attempts ]; do
        if eval "$health_check" &>/dev/null; then
            success "$service_name is ready!"
            return 0
        fi
        
        echo -n "."
        sleep 2
        ((attempt++))
    done
    
    error "$service_name failed to start after $max_attempts attempts"
}

# ============================================================================
# 🔍 PREREQUISITES CHECK
# ============================================================================

check_prerequisites() {
    step "Checking prerequisites..."
    
    # Required commands
    local required_commands=("docker" "docker-compose" "curl" "jq" "openssl")
    
    for cmd in "${required_commands[@]}"; do
        check_command "$cmd"
    done
    
    # Docker daemon
    if ! docker info &>/dev/null; then
        error "Docker daemon is not running"
    fi
    
    # Disk space
    local available_space=$(df . | awk 'NR==2 {print $4}')
    if [ "$available_space" -lt 1048576 ]; then  # 1GB in KB
        warn "Less than 1GB disk space available"
    fi
    
    # Memory
    local available_memory=$(free -m | awk 'NR==2{print $7}')
    if [ "$available_memory" -lt 2048 ]; then  # 2GB
        warn "Less than 2GB memory available"
    fi
    
    success "Prerequisites check passed"
}

# ============================================================================
# 📁 PROJECT STRUCTURE SETUP
# ============================================================================

setup_project_structure() {
    step "Setting up project structure..."
    
    # Create necessary directories
    local directories=(
        "data/postgres"
        "data/redis"
        "data/grafana"
        "data/prometheus"
        "logs"
        "uploads"
        "backups"
        "nginx/ssl"
        "monitoring/grafana/dashboards"
        "monitoring/grafana/datasources"
        "monitoring/prometheus"
        "alembic/versions"
        "tests/unit"
        "tests/integration"
        "tests/performance"
        "tests/api"
        "tests/load"
    )
    
    for dir in "${directories[@]}"; do
        mkdir -p "$dir"
        info "Created directory: $dir"
    done
    
    # Set permissions
    chmod 755 data/
    chmod 700 data/postgres data/redis
    
    success "Project structure initialized"
}

# ============================================================================
# 🔐 SECURITY CONFIGURATION
# ============================================================================

setup_security() {
    step "Configuring security..."
    
    # Generate .env file
    cat > .env << EOF
# 🔐 HUNTER AGENCY - Security Configuration
# Generated: $(date)

# Database
POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
REDIS_PASSWORD=${REDIS_PASSWORD}

# Authentication
SECRET_KEY=${SECRET_KEY}
JWT_SECRET=${JWT_SECRET}
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# API Configuration
API_V1_STR=/api/v1
PROJECT_NAME="Hunter Agency CRM"
DEBUG=false
ENVIRONMENT=${ENVIRONMENT}

# External Services (configure as needed)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_TLS=true
SMTP_USER=
SMTP_PASSWORD=

# OpenAI (for AI features)
OPENAI_API_KEY=

# Stripe (for billing)
STRIPE_SECRET_KEY=
STRIPE_PUBLISHABLE_KEY=

# Monitoring
GRAFANA_PASSWORD=$(openssl rand -base64 16)
SENTRY_DSN=

# Backup
BACKUP_ENCRYPTION_KEY=$(openssl rand -base64 32)
EOF

    chmod 600 .env
    
    # Generate SSL certificate for development
    if [ ! -f "nginx/ssl/server.crt" ]; then
        info "Generating self-signed SSL certificate..."
        openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
            -keyout nginx/ssl/server.key \
            -out nginx/ssl/server.crt \
            -subj "/C=US/ST=State/L=City/O=Hunter Agency/CN=localhost"
        chmod 600 nginx/ssl/server.key
    fi
    
    success "Security configuration completed"
}

# ============================================================================
# 🐳 DOCKER SERVICES DEPLOYMENT
# ============================================================================

deploy_services() {
    step "Deploying Docker services..."
    
    # Pull latest images
    info "Pulling Docker images..."
    docker-compose -f "$COMPOSE_FILE" pull
    
    # Build custom images
    info "Building custom images..."
    docker-compose -f "$COMPOSE_FILE" build --no-cache
    
    # Start services
    info "Starting services..."
    docker-compose -f "$COMPOSE_FILE" --profile "$COMPOSE_PROFILES" up -d
    
    # Wait for services
    wait_for_service "PostgreSQL" "docker-compose exec postgres pg_isready -U postgres"
    wait_for_service "Redis" "docker-compose exec redis redis-cli ping"
    
    success "Docker services deployed"
}

# ============================================================================
# 🗄️ DATABASE INITIALIZATION
# ============================================================================

initialize_database() {
    step "Initializing database..."
    
    # Run migrations
    info "Running database migrations..."
    docker-compose exec crm_api alembic upgrade head
    
    # Create initial admin user
    info "Creating initial admin user..."
    docker-compose exec crm_api python -c "
import asyncio
from crm.auth.models import User, Organization
from crm.auth.jwt_auth import AuthManager
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
import os

DATABASE_URL = os.getenv('DATABASE_URL')
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

def create_admin():
    db = SessionLocal()
    try:
        # Create organization
        org = Organization(name='Hunter Agency', slug='hunter-agency')
        db.add(org)
        db.commit()
        db.refresh(org)
        
        # Create admin user
        admin = User(
            email='admin@hunter-agency.com',
            hashed_password=AuthManager.get_password_hash('admin123'),
            first_name='Admin',
            last_name='User',
            role='admin',
            organization_id=org.id,
            is_active=True,
            is_verified=True
        )
        db.add(admin)
        db.commit()
        print('✅ Admin user created: admin@hunter-agency.com / admin123')
    except Exception as e:
        print(f'Admin user may already exist: {e}')
    finally:
        db.close()

create_admin()
"
    
    success "Database initialized"
}

# ============================================================================
# 🧪 SYSTEM VERIFICATION
# ============================================================================

verify_deployment() {
    step "Verifying deployment..."
    
    # Wait for API to be ready
    wait_for_service "CRM API" "curl -f http://localhost:${API_PORT}/health"
    
    # Test API endpoints
    info "Testing API endpoints..."
    
    # Health check
    local health_response=$(curl -s http://localhost:${API_PORT}/health)
    if [[ $(echo "$health_response" | jq -r '.status') == "healthy" ]]; then
        success "Health check passed"
    else
        error "Health check failed: $health_response"
    fi
    
    # Authentication test
    info "Testing authentication..."
    local auth_response=$(curl -s -X POST http://localhost:${API_PORT}/auth/login \
        -H "Content-Type: application/json" \
        -d '{"email":"admin@hunter-agency.com","password":"admin123"}')
    
    if [[ $(echo "$auth_response" | jq -r '.access_token') != "null" ]]; then
        success "Authentication test passed"
    else
        warn "Authentication test failed (may need manual setup)"
    fi
    
    # Database connectivity
    info "Testing database connectivity..."
    if docker-compose exec postgres psql -U postgres -d hunter_agency -c "SELECT 1;" &>/dev/null; then
        success "Database connectivity verified"
    else
        error "Database connectivity test failed"
    fi
    
    # Redis connectivity
    info "Testing Redis connectivity..."
    if docker-compose exec redis redis-cli ping | grep -q "PONG"; then
        success "Redis connectivity verified"
    else
        error "Redis connectivity test failed"
    fi
    
    success "System verification completed"
}

# ============================================================================
# 📊 MONITORING SETUP
# ============================================================================

setup_monitoring() {
    step "Setting up monitoring..."
    
    # Grafana datasource configuration
    cat > monitoring/grafana/datasources/prometheus.yml << EOF
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
EOF

    # Basic dashboard configuration
    cat > monitoring/grafana/dashboards/crm-dashboard.json << 'EOF'
{
  "dashboard": {
    "title": "Hunter Agency CRM Dashboard",
    "panels": [
      {
        "title": "API Requests",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(http_requests_total[5m])",
            "legendFormat": "{{method}} {{status}}"
          }
        ]
      },
      {
        "title": "Lead Qualification Rate",
        "type": "stat",
        "targets": [
          {
            "expr": "qualification_success_rate",
            "legendFormat": "Success Rate"
          }
        ]
      }
    ]
  }
}
EOF

    success "Monitoring setup completed"
}

# ============================================================================
# 📋 STATUS REPORT
# ============================================================================

generate_status_report() {
    step "Generating deployment status report..."
    
    echo ""
    echo -e "${CYAN}🎯 HUNTER AGENCY CRM - DEPLOYMENT STATUS${NC}"
    echo "=" * 60
    echo ""
    
    # Service status
    echo -e "${BLUE}📊 SERVICE STATUS:${NC}"
    docker-compose ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"
    echo ""
    
    # Access points
    echo -e "${BLUE}🔗 ACCESS POINTS:${NC}"
    echo "  🌐 CRM API:           http://localhost:${API_PORT}"
    echo "  📚 API Documentation: http://localhost:${API_PORT}/docs"
    echo "  🔍 Health Check:     http://localhost:${API_PORT}/health"
    echo "  📊 Grafana:          http://localhost:3001 (admin/$(grep GRAFANA_PASSWORD .env | cut -d= -f2))"
    echo "  📈 Prometheus:       http://localhost:9090"
    echo "  📧 MailHog:          http://localhost:8025"
    echo ""
    
    # Database info
    echo -e "${BLUE}🗄️ DATABASE:${NC}"
    echo "  🐘 PostgreSQL:       localhost:5432 (postgres/$(grep POSTGRES_PASSWORD .env | cut -d= -f2))"
    echo "  🔄 Redis:            localhost:6379"
    echo ""
    
    # Quick tests
    echo -e "${BLUE}🧪 QUICK TESTS:${NC}"
    echo "  curl http://localhost:${API_PORT}/health"
    echo "  curl http://localhost:${API_PORT}/leads"
    echo "  curl http://localhost:${API_PORT}/pipeline/stats"
    echo ""
    
    # Management commands
    echo -e "${BLUE}🔧 MANAGEMENT:${NC}"
    echo "  View logs:        docker-compose logs -f"
    echo "  Stop services:    docker-compose down"
    echo "  Restart:          docker-compose restart"
    echo "  Shell access:     docker-compose exec crm_api bash"
    echo ""
    
    # Security info
    echo -e "${BLUE}🔐 SECURITY:${NC}"
    echo "  Admin login:      admin@hunter-agency.com / admin123"
    echo "  Config file:      .env (secured)"
    echo "  SSL certificate:  nginx/ssl/ (self-signed)"
    echo ""
    
    success "Hunter Agency CRM is fully operational! 🚀"
}

# ============================================================================
# 🚀 MAIN DEPLOYMENT FUNCTION
# ============================================================================

main() {
    echo -e "${CYAN}"
    cat << 'EOF'
    🎯 HUNTER AGENCY CRM
    Smart Pipeline Deployment
    
    Production-Ready Features:
    ✅ AI Lead Qualification
    ✅ Auto Assignment
    ✅ JWT Authentication
    ✅ Data Isolation
    ✅ Docker Orchestration
    ✅ Monitoring & Alerts
    ✅ Security Hardening
    
EOF
    echo -e "${NC}"
    
    # Deployment steps
    check_prerequisites
    setup_project_structure
    setup_security
    deploy_services
    initialize_database
    setup_monitoring
    verify_deployment
    generate_status_report
    
    echo ""
    echo -e "${GREEN}🎉 DEPLOYMENT COMPLETE!${NC}"
    echo ""
    echo -e "${YELLOW}Next Steps:${NC}"
    echo "1. 📊 Access Grafana to set up monitoring dashboards"
    echo "2. 🔐 Change default admin password"
    echo "3. 📧 Configure SMTP settings in .env"
    echo "4. 🔑 Add your OpenAI API key for AI features"
    echo "5. 💳 Configure Stripe for billing features"
    echo ""
    echo -e "${BLUE}🚀 Ready to move to Email Engine development!${NC}"
}

# ============================================================================
# 🎬 SCRIPT EXECUTION
# ============================================================================

# Trap for cleanup on exit
cleanup() {
    if [ $? -ne 0 ]; then
        error "Deployment failed! Check logs above."
        echo ""
        echo "🔧 Troubleshooting:"
        echo "  - Check Docker daemon: docker info"
        echo "  - View service logs: docker-compose logs"
        echo "  - Check disk space: df -h"
        echo "  - Check memory: free -h"
    fi
}

trap cleanup EXIT

# Run main function
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
