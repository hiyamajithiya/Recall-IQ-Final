# 🚀 RecallIQ - Quick Setup Guide

## Pre-configured Ready-to-Use Project!

This project comes **pre-configured** with working Google OAuth and Gmail SMTP credentials. Just follow these steps:

## ⚡ Quick Start (5 minutes)

### 1. **Copy Environment Files**
```bash
# Backend
cp .env.example .env

# Frontend  
cd frontend
cp .env.example .env
cd ..
```

### 2. **Install Dependencies**
```bash
# Backend dependencies
pip install -r requirements.txt

# Frontend dependencies
cd frontend
npm install
cd ..
```

### 3. **Setup Database**
```bash
python manage.py migrate
```

### 4. **Start Servers**

**Terminal 1 - Backend:**
```bash
python manage.py runserver 8000
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm start
```

### 5. **Access Application**
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000/api

## ✅ Pre-configured Features

### **Email OTP System**
- ✅ Gmail SMTP configured (`chinmaytechsoft@gmail.com`)
- ✅ OTP emails sent automatically
- ✅ Professional email templates

### **Google OAuth Login**
- ✅ Google Cloud Console configured
- ✅ Direct login/signup with Google account
- ✅ "Continue with Google" button ready

### **System Features**
- ✅ Multi-tenant architecture
- ✅ JWT authentication
- ✅ Encrypted password storage
- ✅ Email campaign management
- ✅ Batch processing automation

## 🧪 Test Your Setup

### Test Email OTP Registration:
1. Go to http://localhost:3000
2. Click "Register"
3. Fill form with **new email** (not previously used)
4. Click "Send Code"
5. Check email for OTP code
6. Complete registration

### Test Google OAuth:
1. Go to http://localhost:3000  
2. Click "Continue with Google"
3. Select Google account
4. Automatic login/registration

## 🔧 Configuration Details

All credentials are pre-configured in `.env.example`:

- **Gmail SMTP**: `chinmaytechsoft@gmail.com` (for OTP emails)
- **Google OAuth Client**: `589523695138-m7j8tq6lpls2l60jbn1di8aqo6qkk31e.apps.googleusercontent.com`
- **Database**: SQLite (ready for PostgreSQL in production)
- **Security**: Pre-configured encryption keys

## 📞 Support

If you encounter any issues:
1. Check both servers are running on correct ports
2. Verify `.env` files are copied correctly
3. Ensure all dependencies are installed

**Ready to use!** 🎉 The project is fully configured and production-ready.
