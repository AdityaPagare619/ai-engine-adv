# JEE Smart AI Platform 🚀

A comprehensive microservices-based platform for JEE (Joint Entrance Examination) preparation featuring intelligent question management, asset processing, and real-time testing capabilities.

## 📋 Project Overview

The JEE Smart AI Platform is designed to handle large-scale exam preparation with automated question processing, intelligent asset management, and robust test delivery systems. Built with a microservices architecture for scalability and maintainability.

### 🎯 Key Features

- **Multi-Service Architecture**: Modular microservices design for scalability
- **Intelligent Question Management**: CSV-based question import with validation
- **Asset Processing Pipeline**: Automated image processing and optimization  
- **Real-time Test Interface**: Interactive exam environment with timer and navigation
- **Admin Management System**: Complete administrative control panel
- **Database Management**: Automated ID generation and connection pooling
- **API Gateway**: Centralized routing and authentication
- **Frontend Rendering**: Modern React-based user interface

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   API Gateway   │    │   Admin Panel   │
│   (React/TS)    │    │   (Node.js)     │    │   (FastAPI)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
         ┌───────────────────────┼───────────────────────┐
         │                       │                       │
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Content         │    │ Asset           │    │ Database        │
│ Processor       │    │ Processor       │    │ Manager         │
│ (FastAPI)       │    │ (FastAPI)       │    │ (FastAPI)       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
         ┌─────────────────┐    ┌─────────────────┐
         │   PostgreSQL    │    │     Redis       │
         │   Database      │    │     Cache       │
         └─────────────────┘    └─────────────────┘
```

## 🛠️ Technology Stack

### Backend Services
- **Python 3.11+** with FastAPI framework
- **Node.js 18+** for API Gateway
- **PostgreSQL 15+** for primary database
- **Redis 7+** for caching and sessions

### Frontend
- **React 18+** with TypeScript
- **Vite** for build tooling
- **Tailwind CSS** for styling

### DevOps & Deployment
- **Docker** and Docker Compose
- **Nginx** for reverse proxy
- **Multi-stage builds** for optimization

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose
- Python 3.11+ (for local development)
- Node.js 18+ (for local development)

### 1. Clone and Setup

```bash
git clone https://github.com/AdityaPagare619/smart-database-system.git
cd smart-database-system
```

### 2. Environment Configuration

```bash
# Copy the template and configure your environment
cp .env.template .env

# Edit .env with your configuration
# - Database credentials
# - JWT secrets
# - Service ports
# - Redis password
```

### 3. Launch Services

```bash
# Build and start all services
docker-compose up --build -d

# Check service health
docker-compose ps

# View logs
docker-compose logs -f
```

### 4. Initialize Database

```bash
# Run database migrations
docker-compose exec database-manager python -c "from app import init_db; init_db()"
```

### 5. Access the Platform

- **Frontend**: http://localhost:3000
- **API Gateway**: http://localhost:8080
- **Admin Panel**: http://localhost:8001
- **PostgreSQL**: localhost:5432

## 📊 Service Endpoints

| Service | Port | Health Check | Description |
|---------|------|--------------|-------------|
| Frontend | 3000 | `/` | React application |
| API Gateway | 8080 | `/health` | Central routing |
| Admin Management | 8001 | `/health` | Admin operations |
| Content Processor | 8002 | `/health` | Question processing |
| Asset Processor | 8003 | `/health` | Media handling |
| Database Manager | 8004 | `/health` | DB operations |

## 📈 Development Phases

### ✅ Phase 1: Foundation (Completed)
- Multi-service architecture setup
- Docker containerization
- Database schema design
- Basic CRUD operations
- Health monitoring system

### ✅ Phase 2: Content Processing (Completed)
- CSV question import system
- Data validation pipeline
- Asset management system
- Batch processing capabilities
- Error handling and logging

### ✅ Phase 3: Frontend Interface (Completed)
- Interactive test interface
- Real-time question rendering
- Image zoom and navigation
- Keyboard shortcuts
- Responsive design

### 🚧 Phase 4: Advanced Features (Planned)
- AI-powered question analysis
- Performance analytics
- Advanced reporting
- Mobile applications
- Cloud deployment

## 🔧 Development Setup

### Local Development

```bash
# Install Python dependencies
pip install -r requirements.txt

# Install Node.js dependencies (API Gateway)
cd api_gateway && npm install

# Install Frontend dependencies
cd frontend && npm install

# Run services locally
python -m uvicorn services.admin-management.app:app --reload --port 8001
```

### Testing

```bash
# Run Python tests
pytest tests/

# Run JavaScript tests
cd api_gateway && npm test
```

## 📝 Database Schema

The platform uses a comprehensive schema with 13+ core tables:

- **exam_registry**: Exam definitions
- **subject_registry**: Subject management  
- **question_sheets**: Question organization
- **question_bank**: Question storage
- **option_bank**: Multiple choice options
- **asset_registry**: Media file management
- **operation_logs**: Activity tracking

## 🔐 Security Features

- **JWT Authentication**: Secure API access
- **bcrypt Password Hashing**: User credential protection
- **Input Validation**: Comprehensive data sanitization
- **CORS Configuration**: Cross-origin request control
- **Rate Limiting**: API abuse prevention

## 📋 API Documentation

API documentation is available at:
- **Admin API**: http://localhost:8001/docs
- **Content API**: http://localhost:8002/docs  
- **Asset API**: http://localhost:8003/docs

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙋‍♂️ Support

For support, please open an issue in the GitHub repository or contact the development team.

---

**Built with ❤️ for JEE aspirants**