# JEE Smart AI Platform - Phase 3 Deployment Guide

## Overview
This guide covers the deployment of the complete JEE Smart AI Platform with API Gateway and all microservices in Phase 3.

## Architecture Overview

```
┌─────────────────┐    ┌──────────────────┐
│   API Gateway   │────│   Load Balancer  │
│   (Port 8080)   │    │                  │
└─────────────────┘    └──────────────────┘
         │
    ┌────┴────┐
    │         │
┌───▼───┐ ┌───▼─────────┐ ┌─────────────┐ ┌──────────────┐
│Admin  │ │Content      │ │Asset        │ │Database      │
│Service│ │Processor    │ │Processor    │ │Manager       │
│:8000  │ │:8000        │ │:8000        │ │:8000         │
└───────┘ └─────────────┘ └─────────────┘ └──────────────┘
    │           │               │               │
    └───────────┼───────────────┼───────────────┘
                │               │
        ┌───────▼───────┐ ┌─────▼─────┐
        │  PostgreSQL   │ │   Redis   │
        │    :5432      │ │   :6379   │
        └───────────────┘ └───────────┘
```

## Services Configuration

| Service | Container Name | Internal Port | External Port | Description |
|---------|---------------|---------------|---------------|-------------|
| API Gateway | jee_api_gateway | 8080 | 8080 | Main entry point |
| Admin Service | jee_admin_service | 8000 | - | User management |
| Content Processor | jee_content_processor | 8000 | - | CSV processing |
| Asset Processor | jee_asset_processor | 8000 | - | Image processing |
| Database Manager | jee_database_manager | 8000 | - | DB operations |
| PostgreSQL | jee_postgres | 5432 | 5432 | Database |
| Redis | jee_redis | 6379 | - | Cache/Sessions |

## Prerequisites

1. **Docker & Docker Compose**
   ```bash
   # Verify installation
   docker --version
   docker-compose --version
   ```

2. **Environment Configuration**
   ```bash
   # Copy and customize environment variables
   cp .env.example .env
   # Edit .env with your specific values
   ```

3. **Required Directories**
   ```bash
   # Create data directories
   mkdir -p data/uploads/assets
   mkdir -p database/migrations
   ```

## Deployment Steps

### 1. Environment Setup
```bash
# Set secure passwords and secrets
export JWT_SECRET=$(openssl rand -base64 32)
export DB_PASSWORD=$(openssl rand -base64 16)

# Update .env file with generated secrets
echo "JWT_SECRET=${JWT_SECRET}" >> .env
echo "DB_PASSWORD=${DB_PASSWORD}" >> .env
```

### 2. Build and Start Services
```bash
# Build all services
docker-compose --env-file .env build

# Start infrastructure services first
docker-compose --env-file .env up -d postgres redis

# Wait for infrastructure to be healthy
docker-compose --env-file .env logs -f postgres
# Press Ctrl+C when you see "database system is ready"

# Start application services
docker-compose --env-file .env up -d admin-service database-manager content-processor asset-processor

# Finally start API Gateway
docker-compose --env-file .env up -d api-gateway
```

### 3. Verify Deployment
```bash
# Check all service statuses
docker-compose --env-file .env ps

# Check service health
docker-compose --env-file .env logs api-gateway
docker-compose --env-file .env logs content-processor
docker-compose --env-file .env logs asset-processor

# Test API Gateway
curl -f http://localhost:8080/health
```

## Monitoring and Maintenance

### Health Checks
```bash
# System-wide health check
curl http://localhost:8080/health

# Individual service health (through gateway)
curl http://localhost:8080/admin/health
curl http://localhost:8080/content/health
curl http://localhost:8080/assets/health
curl http://localhost:8080/database/health
```

### Log Monitoring
```bash
# Follow all logs
docker-compose --env-file .env logs -f

# Follow specific service logs
docker-compose --env-file .env logs -f api-gateway
docker-compose --env-file .env logs -f content-processor
docker-compose --env-file .env logs -f asset-processor

# View recent logs
docker-compose --env-file .env logs --tail=100 api-gateway
```

### Resource Monitoring
```bash
# Check resource usage
docker stats

# Check disk usage
docker system df

# Check network connectivity
docker network ls
docker network inspect jee-smart-ai-platform_jee-network
```

### Maintenance Commands
```bash
# Restart specific service
docker-compose --env-file .env restart content-processor

# Update service
docker-compose --env-file .env up -d --build content-processor

# Scale services (if needed)
docker-compose --env-file .env up -d --scale content-processor=2

# Backup database
docker exec jee_postgres pg_dump -U jee_admin jee_smart_platform > backup.sql

# Cleanup unused resources
docker system prune -f
```

## Troubleshooting

### Common Issues

1. **Service Won't Start**
   ```bash
   # Check container logs
   docker-compose logs service-name
   
   # Check resource constraints
   docker system df
   free -m
   ```

2. **Database Connection Issues**
   ```bash
   # Test database connectivity
   docker exec jee_postgres pg_isready -U jee_admin
   
   # Connect to database
   docker exec -it jee_postgres psql -U jee_admin -d jee_smart_platform
   ```

3. **API Gateway Issues**
   ```bash
   # Check API Gateway routing
   curl -v http://localhost:8080/content/health
   
   # Check service discovery
   docker exec jee_api_gateway nslookup content-processor
   ```

### Performance Tuning

1. **Database Optimization**
   ```sql
   -- Check active connections
   SELECT count(*) FROM pg_stat_activity;
   
   -- Monitor slow queries
   SELECT query, mean_time, calls FROM pg_stat_statements ORDER BY mean_time DESC;
   ```

2. **Memory Optimization**
   ```yaml
   # Add to docker-compose.yml for memory limits
   deploy:
     resources:
       limits:
         memory: 512M
       reservations:
         memory: 256M
   ```

## Security Considerations

1. **Environment Variables**
   - Never commit `.env` file to version control
   - Use strong, unique passwords
   - Rotate secrets regularly

2. **Network Security**
   - Services communicate on internal network
   - Only API Gateway exposes external ports
   - Use HTTPS in production

3. **Database Security**
   - Use strong database passwords
   - Limit database connections
   - Regular security updates

## Production Deployment

For production deployment, consider:

1. **Load Balancing**: Use nginx or cloud load balancer
2. **SSL/TLS**: Implement HTTPS with valid certificates
3. **Monitoring**: Add Prometheus/Grafana for metrics
4. **Logging**: Centralized logging with ELK stack
5. **Backup**: Automated database and file backups
6. **Scaling**: Horizontal scaling for high availability

## Support

For issues and questions:
- Check logs first: `docker-compose logs service-name`
- Review health checks: `curl http://localhost:8080/health`
- Verify network connectivity between services
- Check resource utilization: `docker stats`