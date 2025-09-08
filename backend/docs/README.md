# 🎯 RecallIQ Documentation - Enterprise Email Campaign Platform

RecallIQ is a production-ready multi-tenant SaaS platform for managing email campaigns with advanced automation, built with Django REST API and React. This documentation provides comprehensive guides for both technical and non-technical users.

## � Quick Navigation

### 👤 For End Users (Non-Technical)
- **[🚀 Quick Start Guide](./user/QUICK_START.md)** - Get started in 5 minutes with test accounts
- **[📱 User Manual](./user/README.md)** - Complete guide for daily usage
- **[🎯 Features Overview](./user/FEATURES.md)** - What RecallIQ can do for you
- **[❓ FAQ](./user/FAQ.md)** - Common questions and answers
- **[🛠️ Troubleshooting](./user/TROUBLESHOOTING.md)** - Solve common issues

### 🏢 For Administrators  
- **[👥 User Management Guide](./user/ADMIN_GUIDE.md)** - Managing users and permissions
- **[🏢 Organization Setup](./user/TENANT_ADMIN_GUIDE.md)** - Organization configuration
- **[📊 Analytics Guide](./user/ANALYTICS_GUIDE.md)** - Understanding reports and metrics

### 👨‍💻 For Developers
- **[🔧 Developer Setup](./developer/README.md)** - Development environment setup
- **[📚 API Documentation](./developer/API.md)** - Complete API reference
- **[🗄️ Database Schema](./developer/DATABASE.md)** - Database structure and relationships
- **[🏗️ Architecture Guide](./developer/ARCHITECTURE.md)** - System architecture overview
- **[🚀 Deployment Guide](./developer/DEPLOYMENT.md)** - Production deployment instructions

## 🎯 What is RecallIQ?

RecallIQ is a **complete email marketing and campaign management platform** designed for businesses of all sizes. Think of it as your digital marketing assistant that helps you:

- 📧 **Send Professional Emails**: Create beautiful email campaigns with templates
- 👥 **Manage Contacts**: Organize customers and prospects into groups  
- 📊 **Track Performance**: See who opens your emails and clicks your links
- ⏰ **Schedule Campaigns**: Send emails at the perfect time automatically
- 🏢 **Multi-Organization**: Manage multiple companies or departments separately

## ✨ Key Highlights

### 🔐 **Dual Authentication System**
- **Traditional Login**: Username/password with email OTP verification
- **Google OAuth**: One-click "Continue with Google" for instant access
- **Secure Registration**: Email verification ensures authentic users

### 📧 **Advanced Email Features**  
- **Rich Templates**: Professional email designs with drag-and-drop editing
- **Smart Variables**: Personalize emails with recipient names, companies, etc.
- **Multiple Providers**: Gmail, Outlook, Yahoo, and custom SMTP support
- **Bulk Campaigns**: Send thousands of emails efficiently with queue management

### 🏢 **Enterprise-Grade Multi-Tenancy**
- **Complete Isolation**: Each organization's data is completely separate
- **Role-Based Access**: Super Admin, Tenant Admin, Staff, and User roles
- **Scalable Architecture**: Handles multiple organizations seamlessly

### 📊 **Comprehensive Analytics**
- **Real-time Tracking**: Monitor email delivery, opens, and clicks
- **Performance Metrics**: Success rates, bounce tracking, engagement analytics
- **Detailed Logs**: Complete audit trail of all email activities
- **Export Reports**: Generate Excel reports for stakeholders

## 🌟 Current Working Features

### ✅ **Authentication & Security**
- Email OTP registration and verification system
- Google OAuth 2.0 login and signup integration  
- JWT token-based authentication with refresh tokens
- Password reset via email with secure tokens
- Role-based access control across all features

### ✅ **Email Campaign Management**
- Rich HTML email template editor with live preview
- Template variable system for personalization
- Multiple email provider configurations (Gmail SMTP, OAuth APIs)
- Bulk email campaigns with scheduling capabilities
- Email queue management with retry logic

### ✅ **Contact & Group Management**
- Advanced contact group creation and management
- Excel import/export functionality with templates
- Contact deduplication and validation
- Group-based email targeting and segmentation
- Bulk operations for contact management

### ✅ **Analytics & Reporting**
- Real-time email delivery tracking and status monitoring
- Comprehensive email logs with filtering and search
- Campaign performance analytics and metrics
- Success/failure rate monitoring with detailed reasons
- Excel export of logs and reports

### ✅ **Multi-Tenant Architecture**
- Complete tenant data isolation and security
- Organization-specific branding and configuration
- User management within tenant boundaries
- Tenant-admin capabilities for organization management
- Scalable multi-organization support

## 🛠️ **Technology Stack**

### **Backend (API Server)**
- **Framework**: Django 4.2 with Django REST Framework
- **Database**: PostgreSQL (production) / SQLite (development)  
- **Authentication**: JWT tokens with `djangorestframework-simplejwt`
- **Email Integration**: Gmail API, SMTP providers, OAuth 2.0
- **Background Processing**: Simple automation service for scheduled tasks

### **Frontend (User Interface)**
- **Framework**: React 18 with modern hooks and functional components
- **Styling**: Tailwind CSS with responsive design and dark mode
- **Routing**: React Router v6 with protected routes
- **State Management**: React Context API for global state
- **Forms**: React Hook Form with comprehensive validation
- **UI Components**: Headless UI with custom Tailwind components

### **Authentication & Security**
- **Google OAuth**: Google Identity Services SDK integration
- **Email OTP**: Secure 6-digit OTP system with expiration
- **JWT Tokens**: Access and refresh token implementation
- **Password Security**: Django's built-in password hashing
- **CORS**: Properly configured cross-origin resource sharing

## 🏗️ **System Architecture**

```
📊 RecallIQ Platform Architecture
├── 🎮 React Frontend (Port 3000)
│   ├── User Authentication (Login/Register/Google OAuth)
│   ├── Dashboard with Analytics and Metrics
│   ├── Email Template Editor with Rich Text
│   ├── Contact Group Management Interface
│   ├── Campaign Creation and Scheduling
│   ├── Email Logs and Performance Tracking
│   └── User Profile and Settings Management
│
├── 🔧 Django REST API (Port 8000)
│   ├── JWT Authentication with Refresh Tokens
│   ├── Google OAuth 2.0 Integration
│   ├── Email OTP Verification System
│   ├── Multi-Tenant Data Isolation
│   ├── Email Provider Management (Gmail/SMTP)
│   ├── Campaign Processing and Queue Management
│   ├── Analytics and Logging APIs
│   └── Role-Based Permission System
│
├── 📨 Email Processing Engine
│   ├── Gmail API Integration with OAuth 2.0
│   ├── SMTP Provider Support (Gmail, Outlook, Yahoo)
│   ├── Email Template Processing with Variables
│   ├── Bulk Email Queue with Rate Limiting
│   ├── Delivery Tracking and Status Updates
│   └── Bounce Handling and Retry Logic
│
├── 🤖 Automation Service
│   ├── Scheduled Campaign Processing
│   ├── Background Email Queue Processing
│   ├── System Health Monitoring
│   ├── Automated Status Updates
│   └── Batch Processing Management
│
└── 🗄️ Data Layer
    ├── PostgreSQL with Multi-Tenant Schema
    ├── User and Organization Management
    ├── Email Templates and Campaign Storage
    ├── Contact Groups and Recipient Management
    ├── Email Logs and Analytics Data
    └── Configuration and Settings Storage
```

## 🚀 **Getting Started**

### **For First-Time Users**
1. **[⚡ 5-Minute Quick Start](./user/QUICK_START.md)** - Get up and running immediately
2. **[🎯 Take a Feature Tour](./user/FEATURES.md)** - Discover what RecallIQ can do
3. **[📱 User Manual](./user/README.md)** - Learn daily operations

### **For Administrators**
1. **[👥 User Management](./user/ADMIN_GUIDE.md)** - Add and manage team members
2. **[🏢 Organization Setup](./user/TENANT_ADMIN_GUIDE.md)** - Configure your company settings
3. **[📊 Analytics Dashboard](./user/ANALYTICS_GUIDE.md)** - Understand performance metrics

### **For Developers**
1. **[🔧 Development Setup](./developer/README.md)** - Set up your development environment
2. **[📚 API Documentation](./developer/API.md)** - Integrate with RecallIQ APIs
3. **[🏗️ Architecture Guide](./developer/ARCHITECTURE.md)** - Understand system design

## 🔧 **System Requirements**

### **For End Users (Browser Access)**
- **Modern Web Browser**: Chrome 90+, Firefox 88+, Safari 14+, Edge 90+
- **Internet Connection**: Stable broadband for real-time features
- **Screen Resolution**: 1024x768 minimum (responsive design supports mobile)
- **JavaScript**: Must be enabled

### **For Development**
- **Python**: 3.9+ (3.11 recommended)
- **Node.js**: 16+ (18 LTS recommended)
- **Database**: PostgreSQL 12+ (SQLite included for development)
- **Operating System**: Windows 10+, macOS 10.15+, Linux (Ubuntu 20+)
- **Memory**: 4GB RAM minimum, 8GB recommended
- **Storage**: 2GB free space for development environment

### **For Production Deployment**
- **Server**: Linux VPS/dedicated server with 2GB+ RAM
- **Database**: PostgreSQL 13+ with backup strategy
- **Web Server**: Nginx with SSL certificate
- **Domain**: Custom domain with DNS management
- **Email Service**: SMTP access or API credentials for email providers

## 🌍 **Access Information**

### **Application URLs**
- **Production App**: `https://yourcompany.recalliq.com` (when deployed)
- **Development Server**: `http://localhost:3000` (frontend)
- **API Endpoint**: `http://localhost:8000/api/` (backend)
- **Admin Panel**: `http://localhost:8000/admin/` (Django admin)

### **Test Account Access**
Ready-to-use test credentials are available in the [Quick Start Guide](./user/QUICK_START.md#test-credentials).

## 📞 **Support & Resources**

### **Documentation Resources**
- **📖 Complete User Manual**: Step-by-step instructions for all features
- **🎥 Video Tutorials**: Coming soon - walkthrough videos for major features
- **📋 FAQ Database**: Answers to commonly asked questions
- **🛠️ Troubleshooting Guide**: Solutions to common technical issues

### **Getting Help**
- **📧 Email Support**: Contact your system administrator
- **💬 Community Forum**: Connect with other RecallIQ users (coming soon)
- **🐛 Bug Reports**: Use GitHub issues for technical problems
- **💡 Feature Requests**: Submit suggestions through the feedback system

### **Training & Onboarding**
- **🎓 User Training**: Available for new team members
- **👥 Group Sessions**: Team training for organizations
- **📚 Best Practices**: Guides for effective email marketing
- **🔍 Advanced Features**: In-depth tutorials for power users

## 📄 **Legal & Compliance**

- **🔒 Privacy Policy**: How we protect your data and communications
- **📋 Terms of Service**: Usage agreements and platform policies  
- **🌐 GDPR Compliance**: European data protection regulation compliance
- **📧 CAN-SPAM Act**: Email marketing regulation compliance
- **🔐 Security Standards**: Industry-standard security measures
- **📊 Data Retention**: Policies for data storage and deletion

## 🎊 **Project Status: Production-Ready ✅**

RecallIQ is a **complete, enterprise-grade platform** ready for business use:

✅ **User Authentication**: Email OTP and Google OAuth systems working  
✅ **Email Campaigns**: Full email marketing capabilities implemented  
✅ **Contact Management**: Advanced group and recipient management  
✅ **Multi-Tenancy**: Complete organization isolation and management  
✅ **Analytics**: Comprehensive reporting and tracking systems  
✅ **Security**: Enterprise-level security and data protection  
✅ **Responsive Design**: Works perfectly on desktop, tablet, and mobile  
✅ **Documentation**: Complete guides for users and developers  

**🚀 Ready for deployment and customer onboarding!**

---

**Welcome to RecallIQ!** Start your email marketing success story with our [Quick Start Guide](./user/QUICK_START.md) and explore the powerful features that will transform your business communications.

**Need Help?** Our comprehensive documentation covers everything from basic usage to advanced configurations. Check our [FAQ](./user/FAQ.md) for quick answers or dive into detailed guides for your specific role.

---

*Last Updated: August 22, 2025 | Version: 2.1 Enterprise Edition | Documentation: 2.0*