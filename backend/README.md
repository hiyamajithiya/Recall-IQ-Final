# 🎯 RecallIQ V2 - Enterprise Email Campaign Platform

**Production-Ready Multi-Tenant SaaS Solution**

## 🚀 Quick Start (3 Commands)

### **Start Backend (2 commands in separate terminals):**
```bash
# Terminal 1: Django API Server
python manage.py runserver
python manage.py runserver 8000 --settings=recalliq.settings.development

# Ter# 2. Database Setup
python manage.py migrate --settings=recalliq.settings.production
python manage.py create_superuser_tenant --username admin --email admin@yourcompany.com --password securepassword --tenant-name "Your Company"

# 3. Static Files 2: Background Automation Service  
python simple_automation_service.py
```

### **Start Frontend (1 command):**
```bash
# Terminal 3: React Frontend
cd frontend
npm start
```

### **Access Points:**
- **Frontend Application**: http://localhost:3000
- **Django Admin**: http://localhost:8000/admin
- **API Documentation**: http://localhost:8000/swagger/
- **Health Check**: http://localhost:8000/health/

---

## 📦 Project Structure

```
� RecallIQ V2/
├── 🎮 frontend/              # React + Tailwind CSS Frontend
├── 🔧 batches/               # Batch Email Campaign Management
├── 👥 core/                  # Core Business Logic & Analytics
├── 📨 emails/                # Email Templates & Providers
├── 📊 logs/                  # Email Logging & Tracking
├── 🏢 tenants/               # Multi-Tenant Management
├── ⚙️ recalliq/              # Django Project Settings
├── � docs/                  # Documentation
├── 🗄️ staticfiles/           # Static Assets
├── 🤖 simple_automation_service.py  # Background Automation
├── 🔧 manage.py              # Django Management
├── � requirements.txt       # Python Dependencies
└── 🔐 .env                   # Environment Configuration
```

---

## 🛠️ Development Setup

### **Prerequisites:**
```bash
# Python 3.9+
python --version

# Node.js 16+
node --version
npm --version
```

### **Backend Setup:**
```bash
# 1. Install Python dependencies
pip install -r requirements.txt

# 2. Make database migrations
python manage.py makemigrations core tenants batches emails logs 

# 3. Run database migrations
python manage.py migrate

# 4. Create superuser with tenant (REQUIRED for RecallIQ)
python manage.py create_superuser_tenant --username admin --email admin@example.com --password yourpassword --tenant-name "Your Organization"

# 5. Start Django server
python manage.py runserver
```

### **Frontend Setup:**
```bash
# 1. Navigate to frontend directory
cd frontend

# 2. Install dependencies
npm install

# 3. Start development server
npm start
```

### **Background Automation:**
```bash
# Start the automation service (handles scheduled batches)
python simple_automation_service.py
```

---

## � Essential Commands

### **Development:**
```bash
# Backend
python manage.py runserver               # Start Django API server
python simple_automation_service.py     # Start background automation
python manage.py migrate                # Apply database migrations
python manage.py create_superuser_tenant --username admin --email admin@example.com --password yourpassword --tenant-name "Your Organization"  # Create admin user with tenant
python manage.py shell                  # Django interactive shell
python manage.py collectstatic          # Collect static files
python manage.py rundev                 # Start Django + Celery (if Celery is configured)

# Frontend  
cd frontend && npm start                 # Start React dev server
cd frontend && npm run build             # Build for production
cd frontend && npm test                  # Run tests
cd frontend && npm install               # Install dependencies

# Database
python manage.py makemigrations          # Create new migrations
python manage.py dbshell                # Access database shell

# Testing
python manage.py test                    # Run Django tests
pytest                                  # Run pytest test suite

# Batch Management
python manage.py process_batches         # Process pending batches manually
python manage.py process_scheduled_batches  # Process scheduled batches
python manage.py ensure_automation       # Ensure automation is enabled
```

### **Production:**
```bash
# Environment Setup
cp .env.example .env                     # Copy environment template
# Edit .env with your production settings

# Database Setup
python manage.py migrate --settings=recalliq.settings.production
python manage.py collectstatic --settings=recalliq.settings.production

# Create Super Admin (REQUIRED)
python manage.py create_superuser_tenant --username admin --email admin@yourcompany.com --password securepassword --tenant-name "Your Company" --settings=recalliq.settings.production

# Process Management  
gunicorn recalliq.wsgi:application       # Production WSGI server
celery -A recalliq worker -l info        # Celery worker (if using Celery)
```

---

## 🏗️ Architecture Overview

```
📦 RecallIQ V2 Platform
├── 🎮 React Frontend (Port 3000)
│   ├── Batch Management UI
│   ├── Email Campaign Dashboard  
│   ├── User Management Interface
│   └── Analytics & Reporting
│
├── 🔧 Django Backend (Port 8000)
│   ├── REST API Endpoints
│   ├── Multi-Tenant Architecture
│   ├── Role-Based Access Control
│   └── Admin Interface
│
├── 📨 Email System
│   ├── Multi-Provider Support (SMTP/API)
│   ├── Template Management
│   ├── Delivery Tracking
│   └── Bounce Handling
│
├── 🤖 Automation Engine
│   ├── Scheduled Batch Processing
│   ├── Email Queue Management
│   ├── Document Status Tracking
│   └── Smart Retry Logic
│
└── 🗄️ Data Layer
    ├── SQLite (Development)
    ├── PostgreSQL (Production)
    ├── File Storage
    └── Session Management
```

---

## 🎯 Key Features

### **📧 Email Campaign Management**
- **Batch Processing**: Handle thousands of recipients efficiently
- **Smart Scheduling**: Schedule campaigns with timezone support
- **Template Management**: Rich HTML templates with dynamic variables
- **Multi-Provider Support**: Gmail, Outlook, SMTP, and custom providers
- **Document Tracking**: Track document receipt and responses
- **Delivery Analytics**: Open rates, bounce tracking, and reporting

### **👥 Multi-Tenant User Management**
- **Role-Based Access Control**: Super Admin, Tenant Admin, Staff, Sales Team
- **Tenant Isolation**: Complete data separation between organizations
- **User Permissions**: Granular access control per feature
- **Secure Authentication**: JWT tokens with refresh mechanisms
- **Password Management**: Secure reset flows with email verification

### **🚀 Advanced Automation**
- **Background Processing**: Automatic batch execution
- **Smart Retry Logic**: Handle email failures intelligently
- **Status Management**: Automatic batch state transitions
- **Document Reset Workflow**: Intelligent document status management
- **Queue Management**: Efficient email processing pipeline

### **📊 Analytics & Insights**
- **Real-time Dashboard**: Campaign performance metrics
- **Email Logs**: Comprehensive delivery tracking
- **Batch Statistics**: Success rates and failure analysis
- **Tenant Usage**: Multi-tenant analytics and reporting
- **Performance Monitoring**: System health and metrics

### **� Technical Excellence**
- **Clean Architecture**: Modular, maintainable codebase
- **API-First Design**: Complete REST API coverage
- **Modern Frontend**: React with Tailwind CSS
- **Database Flexibility**: SQLite for dev, PostgreSQL for production
- **Environment Management**: Multi-environment configuration

---

## � Important URLs

| Service | URL | Purpose |
|---------|-----|---------|
| **Frontend App** | http://localhost:3000 | Main application interface |
| **Backend API** | http://localhost:8000/api/ | REST API endpoints |
| **Admin Panel** | http://localhost:8000/admin/ | Django admin interface |
| **API Documentation** | http://localhost:8000/swagger/ | Interactive API docs |
| **Health Check** | http://localhost:8000/health/ | System health monitoring |

---

## 🛡️ Security & Configuration

### **🔐 Environment Setup**
```bash
# Copy environment template
cp .env.example .env

# Configure your settings in .env:
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///db.sqlite3
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
```

### **🔒 Security Features**
- **Encrypted Data Storage**: Sensitive data encrypted with Fernet
- **Secure Communication**: HTTPS/TLS for all endpoints
- **Password Security**: Django's built-in password hashing
- **Session Management**: Secure JWT token handling
- **Role-Based Permissions**: Fine-grained access control
- **Tenant Isolation**: Complete data separation
- **CORS Configuration**: Secure cross-origin requests

---

## � Deployment

### **� Production Setup**
```bash
# 1. Environment Configuration
cp .env.example .env
# Edit .env with production settings (PostgreSQL, etc.)

# 2. Install Dependencies
pip install -r requirements.txt
cd frontend && npm install

# 3. Database Setup
python manage.py makemigrations core tenants batches emails logs --settings=recalliq.settings.production
python manage.py migrate --settings=recalliq.settings.production
python manage.py createsuperuser

# 4. Static Files
python manage.py collectstatic --settings=recalliq.settings.production
cd frontend && npm run build

# 5. Start Services
gunicorn recalliq.wsgi:application --bind 0.0.0.0:8000
python simple_automation_service.py
```

### **🐳 Docker Deployment** (Optional)
```bash
# Build and run
docker-compose up -d

# Scale automation workers
docker-compose up --scale automation=3
```

---

## � Documentation & Support

### **📖 Additional Documentation**
- **User Guide**: [docs/user/README.md](docs/user/README.md)
- **Developer Guide**: [docs/developer/README.md](docs/developer/README.md)
- **API Reference**: Swagger UI at `/swagger/`
- **Troubleshooting**: [docs/user/TROUBLESHOOTING.md](docs/user/TROUBLESHOOTING.md)

### **🔧 Development Resources**
- **Health Monitoring**: Built-in diagnostics at `/health/`
- **Admin Interface**: Full Django admin at `/admin/`
- **Database Management**: Django ORM with migration system
- **Testing**: Comprehensive test suite with pytest

---

## 🎊 Project Status: **PRODUCTION-READY** ✅

RecallIQ V2 is a **complete, enterprise-grade email campaign platform** featuring:

✅ **Modern Tech Stack** (Django 4.2 + React 18)  
✅ **Multi-Tenant Architecture** with complete isolation  
✅ **Advanced Email Management** with multiple providers  
✅ **Smart Automation Engine** for background processing  
✅ **Professional UI/UX** with responsive design  
✅ **Comprehensive Security** with role-based access  
✅ **Production Deployment Ready** with Docker support  
✅ **Clean, Maintainable Codebase** following best practices  

**Ready for production deployment and customer onboarding! 🚀**

---

*Last Updated: August 14, 2025 - v2.0 Enterprise Edition*
