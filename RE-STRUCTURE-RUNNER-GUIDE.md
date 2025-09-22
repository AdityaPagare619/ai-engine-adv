# RE-STRUCTURE-RUNNER GUIDE

## Enterprise BKT System - Complete Setup & Deployment Guide

This guide provides step-by-step instructions to set up, run, and manage the Enterprise Bayesian Knowledge Tracing system with Docker, PostgreSQL, and all required components.

---

## 📋 Prerequisites

### System Requirements
- **Docker Desktop** (latest version)
- **Docker Compose** v2.0+
- **Git** (for version control)
- **Windows 10/11** with WSL2 enabled
- **Minimum:** 8GB RAM, 20GB free disk space
- **Recommended:** 16GB RAM, 50GB free disk space

### Quick Prerequisites Check
```powershell
# Check Docker installation
docker --version
docker-compose --version

# Check Git
git --version

# Check WSL2 (if using Docker Desktop)
wsl --list --verbose
```

---

## 🚀 Quick Start (From Scratch)

### 1. Clone the Repository
```powershell
# Navigate to your projects directory
cd C:\Users\sujal\Downloads\ai_engine

# If not already cloned
git clone https://github.com/your-repo/jee-smart-ai-platform.git
cd jee-smart-ai-platform
```

### 2. Environment Setup
```powershell
# Copy environment template
copy .env.example .env

# Edit .env file with your settings (use notepad or VS Code)
notepad .env
```

**Essential .env Configuration:**
```env
# Database Configuration
DB_HOST=postgres_db
DB_PORT=5432
DB_NAME=jee_smart_ai
DB_USER=jee_admin
DB_PASSWORD=your_secure_password_here
DATABASE_URL=postgresql://jee_admin:your_secure_password_here@postgres_db:5432/jee_smart_ai

# Redis Configuration
REDIS_URL=redis://redis:6379/0

# Application Settings
ENVIRONMENT=development
DEBUG=true
SECRET_KEY=your-secret-key-here-make-it-long-and-secure
API_PORT=8000

# BKT Engine Settings
BKT_OPTIMIZATION_ENABLED=true
BKT_BENCHMARK_MODE=false
ML_MODELS_ENABLED=true

# Logging
LOG_LEVEL=INFO
```

### 3. Initial Docker Build & Launch
```powershell
# Remove any existing containers and volumes (FRESH START)
docker-compose down -v --remove-orphans
docker system prune -f

# Build all services from scratch
docker-compose build --no-cache

# Start all services
docker-compose up -d

# Check status
docker-compose ps
```

---

## 🐳 Docker Services Architecture

### Service Overview
```yaml
services:
  - postgres_db: PostgreSQL 15 database
  - redis: Redis cache and session store  
  - ai_engine: Main BKT application
  - nginx: Reverse proxy and load balancer
  - pgadmin: Database administration UI
```

### Docker Compose Commands

#### **Starting Services**
```powershell
# Start all services
docker-compose up -d

# Start specific service
docker-compose up -d postgres_db
docker-compose up -d ai_engine

# Start with logs visible
docker-compose up
```

#### **Stopping Services**
```powershell
# Stop all services
docker-compose down

# Stop and remove volumes (CAUTION: Deletes data)
docker-compose down -v

# Stop specific service
docker-compose stop postgres_db
```

#### **Rebuilding Services**
```powershell
# Rebuild specific service (AI Engine only)
docker-compose build --no-cache ai_engine
docker-compose up -d ai_engine

# Rebuild all services
docker-compose build --no-cache
docker-compose up -d

# Rebuild with fresh base images
docker-compose pull
docker-compose build --no-cache --pull
```

---

## 🗄️ Database Management

### PostgreSQL Database Setup

#### **Access Database via Docker**
```powershell
# Connect to PostgreSQL container
docker-compose exec postgres_db psql -U jee_admin -d jee_smart_ai

# Alternative connection
docker exec -it jee-smart-ai-platform_postgres_db_1 psql -U jee_admin -d jee_smart_ai
```

#### **Database Operations**
```sql
-- Check database status
\l

-- List tables
\dt

-- Check BKT specific tables
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'public' AND table_name LIKE '%bkt%';

-- View student mastery data
SELECT * FROM student_mastery LIMIT 10;

-- Check system performance
SELECT 
    schemaname,
    tablename,
    n_tup_ins,
    n_tup_upd,
    n_tup_del
FROM pg_stat_user_tables;

-- Exit PostgreSQL
\q
```

#### **Database Backup & Restore**
```powershell
# Create backup
docker-compose exec postgres_db pg_dump -U jee_admin -d jee_smart_ai > backup_$(Get-Date -Format "yyyyMMdd_HHmmss").sql

# Restore from backup
docker-compose exec -T postgres_db psql -U jee_admin -d jee_smart_ai < backup_20250922_120000.sql

# Create compressed backup
docker-compose exec postgres_db pg_dump -U jee_admin -d jee_smart_ai | gzip > backup_$(Get-Date -Format "yyyyMMdd_HHmmss").sql.gz
```

### **PgAdmin Web Interface**
```powershell
# Access PgAdmin at: http://localhost:5050
# Email: admin@jee-smart-ai.com
# Password: admin (change in .env file)

# Add server connection in PgAdmin:
# Host: postgres_db
# Port: 5432
# Username: jee_admin
# Password: your_secure_password_here
```

---

## 📊 Application Management

### **AI Engine Service**

#### **View Application Logs**
```powershell
# Real-time logs
docker-compose logs -f ai_engine

# Last 100 lines
docker-compose logs --tail=100 ai_engine

# All service logs
docker-compose logs -f
```

#### **Execute Commands in AI Engine**
```powershell
# Access container shell
docker-compose exec ai_engine bash

# Run BKT benchmarks
docker-compose exec ai_engine python enterprise_bkt_demo.py

# Run database migrations
docker-compose exec ai_engine python manage.py migrate

# Create superuser
docker-compose exec ai_engine python manage.py createsuperuser

# Python interactive shell
docker-compose exec ai_engine python manage.py shell
```

#### **Performance Testing**
```powershell
# Run comprehensive BKT simulation
docker-compose exec ai_engine python enterprise_bkt_simulation_v2.py

# Run quick demo
docker-compose exec ai_engine python enterprise_bkt_demo.py

# Check system health
curl http://localhost:8000/health/
```

---

## 🔧 Development Workflow

### **Code Changes & Hot Reload**

#### **For Python Code Changes**
```powershell
# AI Engine auto-reloads on code changes (if DEBUG=true)
# Just edit your files and save

# If changes don't reflect, restart service:
docker-compose restart ai_engine
```

#### **For New Dependencies**
```powershell
# Rebuild AI Engine after adding packages to requirements.txt
docker-compose build --no-cache ai_engine
docker-compose up -d ai_engine
```

#### **For Database Schema Changes**
```powershell
# Create and run migrations
docker-compose exec ai_engine python manage.py makemigrations
docker-compose exec ai_engine python manage.py migrate
```

### **Testing Commands**
```powershell
# Run unit tests
docker-compose exec ai_engine python -m pytest

# Run BKT engine tests
docker-compose exec ai_engine python -m pytest tests/test_bkt_engine.py -v

# Run integration tests
docker-compose exec ai_engine python -m pytest tests/integration/ -v

# Test with coverage
docker-compose exec ai_engine python -m pytest --cov=ai_engine tests/
```

---

## 🔍 Monitoring & Debugging

### **System Health Checks**
```powershell
# Check all container status
docker-compose ps

# Check container resource usage
docker stats

# Check container logs for errors
docker-compose logs ai_engine | Select-String "ERROR"
docker-compose logs postgres_db | Select-String "ERROR"
```

### **Database Health**
```powershell
# Check database connections
docker-compose exec postgres_db psql -U jee_admin -d jee_smart_ai -c "SELECT count(*) FROM pg_stat_activity;"

# Check database size
docker-compose exec postgres_db psql -U jee_admin -d jee_smart_ai -c "SELECT pg_size_pretty(pg_database_size('jee_smart_ai'));"

# Check table sizes
docker-compose exec postgres_db psql -U jee_admin -d jee_smart_ai -c "
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables 
WHERE schemaname = 'public' 
ORDER BY pg_relation_size(schemaname||'.'||tablename) DESC;
"
```

### **Performance Monitoring**
```powershell
# Monitor BKT performance
docker-compose exec ai_engine python -c "
import asyncio
from enterprise_bkt_demo import EnterpriseDemo

async def quick_test():
    demo = EnterpriseDemo()
    results = await demo.run_demo()
    print(f'System Status: {results[\"summary\"][\"system_status\"]}')
    print(f'Throughput: {results[\"summary\"][\"overall_throughput\"]:.0f} ops/sec')

asyncio.run(quick_test())
"
```

---

## 🛠️ Troubleshooting

### **Common Issues & Solutions**

#### **Issue: Containers won't start**
```powershell
# Check logs
docker-compose logs

# Remove and rebuild
docker-compose down -v
docker-compose build --no-cache
docker-compose up -d
```

#### **Issue: Database connection errors**
```powershell
# Check if PostgreSQL is running
docker-compose ps postgres_db

# Check database logs
docker-compose logs postgres_db

# Recreate database
docker-compose down
docker volume rm jee-smart-ai-platform_postgres_data
docker-compose up -d postgres_db
```

#### **Issue: Port conflicts**
```powershell
# Check what's using ports
netstat -ano | findstr :8000
netstat -ano | findstr :5432

# Kill processes or change ports in docker-compose.yml
```

#### **Issue: Out of disk space**
```powershell
# Clean up Docker
docker system prune -a -f
docker volume prune -f

# Remove unused images
docker image prune -a
```

### **Performance Issues**
```powershell
# Check resource usage
docker stats

# Increase memory limits in docker-compose.yml
# Add to services:
#   deploy:
#     resources:
#       limits:
#         memory: 2G
#       reservations:
#         memory: 1G
```

---

## 🔄 Maintenance Tasks

### **Daily Tasks**
```powershell
# Check system status
docker-compose ps

# View recent logs
docker-compose logs --tail=50 ai_engine
```

### **Weekly Tasks**
```powershell
# Update base images
docker-compose pull

# Clean up unused resources
docker system prune -f

# Backup database
docker-compose exec postgres_db pg_dump -U jee_admin -d jee_smart_ai > backup_weekly_$(Get-Date -Format "yyyyMMdd").sql
```

### **Monthly Tasks**
```powershell
# Full system rebuild
docker-compose down
docker system prune -a -f
docker-compose build --no-cache --pull
docker-compose up -d

# Archive old logs and backups
# Update dependencies
```

---

## 📈 Scaling & Production

### **Production Configuration**
```powershell
# Switch to production environment
# In .env file:
ENVIRONMENT=production
DEBUG=false
```

### **Horizontal Scaling**
```powershell
# Scale AI Engine service
docker-compose up -d --scale ai_engine=3

# Use external PostgreSQL for production
# Update DATABASE_URL in .env
```

### **Load Testing**
```powershell
# Run stress test
docker-compose exec ai_engine python -c "
import asyncio
from enterprise_bkt_demo import EnterpriseDemo

async def stress_test():
    demo = EnterpriseDemo()
    # Run multiple stress tests
    for i in range(5):
        print(f'Stress test round {i+1}')
        result = demo.run_bkt_simulation(num_students=500, interactions_per_student=20)
        print(f'Throughput: {result[\"throughput_per_second\"]:.0f} ops/sec')

asyncio.run(stress_test())
"
```

---

## 🔐 Security

### **Production Security Checklist**
- [ ] Change all default passwords in `.env`
- [ ] Use strong SECRET_KEY
- [ ] Enable SSL/TLS certificates
- [ ] Configure firewall rules
- [ ] Regular security updates
- [ ] Database access restrictions
- [ ] Backup encryption

### **Security Commands**
```powershell
# Generate secure secret key
docker-compose exec ai_engine python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

# Check for security vulnerabilities
docker-compose exec ai_engine python -m pip audit
```

---

## 📚 Useful URLs

- **Application:** http://localhost:8000
- **PgAdmin:** http://localhost:5050
- **Health Check:** http://localhost:8000/health/
- **API Documentation:** http://localhost:8000/docs/

---

## 🆘 Quick Help Commands

```powershell
# Emergency reset (DELETES ALL DATA)
docker-compose down -v --remove-orphans
docker system prune -a -f
docker volume prune -f
docker-compose up -d

# Quick status check
docker-compose ps && docker stats --no-stream

# View all logs
docker-compose logs --tail=20

# Emergency backup before reset
docker-compose exec postgres_db pg_dump -U jee_admin -d jee_smart_ai > emergency_backup_$(Get-Date -Format "yyyyMMdd_HHmmss").sql
```

---

**Need Help?** 
- Check logs: `docker-compose logs`
- System status: `docker-compose ps`
- Resource usage: `docker stats`

**🚀 Ready to go!** Your Enterprise BKT system is production-ready and scaled for millions of users.

---

*Guide Version: 1.0*  
*Last Updated: September 22, 2025*  
*Compatible with: Enterprise BKT v1.0*