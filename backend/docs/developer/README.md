# Developer Guide - RecallIQ

This guide provides comprehensive information for developers working on RecallIQ, including setup, architecture, and contribution guidelines.

## 📋 Table of Contents

1. [Development Setup](#development-setup)
2. [Project Structure](#project-structure)
3. [Development Workflow](#development-workflow)
4. [Code Standards](#code-standards)
5. [Testing](#testing)
6. [Debugging](#debugging)
7. [Common Tasks](#common-tasks)

## 🚀 Development Setup

### Prerequisites

```bash
# Check versions
python --version  # Should be 3.8+
node --version    # Should be 16+
npm --version     # Should be 8+
```

### Backend Setup

1. **Clone the Repository**
```bash
git clone <repository-url>
cd RecallIQ/Version\ 2
```

2. **Create Virtual Environment**
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
```

3. **Install Dependencies**
```bash
pip install -r requirements.txt
```

4. **Environment Configuration**
```bash
# Copy environment template
cp .env.example .env

# Edit .env file with your settings
DATABASE_URL=sqlite:///db.sqlite3
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
```

5. **Database Setup**
```bash
# Run migrations
python manage.py makemigrations
python manage.py migrate

# Create test data
python setup_users.py
```

### Frontend Setup

1. **Navigate to Frontend Directory**
```bash
cd frontend
```

2. **Install Dependencies**
```bash
npm install
```

3. **Environment Configuration**
```bash
# Create .env file
echo "REACT_APP_API_URL=http://localhost:8000/api" > .env
```

### Running the Development Servers

**Terminal 1 - Backend:**
```bash
cd "RecallIQ/Version 2"
python manage.py runserver
```

**Terminal 2 - Frontend:**
```bash
cd "RecallIQ/Version 2/frontend"
npm start
```

**Access the Application:**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000/api
- Admin Panel: http://localhost:8000/admin

## 📁 Project Structure

```
RecallIQ/Version 2/
├── backend/
│   ├── recalliq/              # Django project settings
│   ├── core/                  # Core app (users, authentication)
│   ├── tenants/               # Multi-tenancy management
│   ├── emails/                # Email templates and providers
│   ├── batches/               # Campaign management
│   ├── logs/                  # Activity logging
│   ├── manage.py              # Django management script
│   └── requirements.txt       # Python dependencies
├── frontend/
│   ├── public/                # Static files
│   ├── src/
│   │   ├── components/        # Reusable React components
│   │   ├── pages/             # Page components
│   │   ├── context/           # React Context providers
│   │   ├── utils/             # Utility functions
│   │   └── App.js             # Main application component
│   ├── package.json           # Node.js dependencies
│   └── tailwind.config.js     # Tailwind CSS configuration
├── docs/                      # Documentation
└── README.md                  # Project overview
```

## 🔄 Development Workflow

### Git Workflow

1. **Create Feature Branch**
```bash
git checkout -b feature/your-feature-name
```

2. **Make Changes**
```bash
# Make your changes
git add .
git commit -m "feat: add new feature description"
```

3. **Push and Create PR**
```bash
git push origin feature/your-feature-name
# Create Pull Request on GitHub
```

### Commit Message Convention

Follow conventional commits:
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `style:` Code style changes
- `refactor:` Code refactoring
- `test:` Adding tests
- `chore:` Maintenance tasks

## 📝 Code Standards

### Python (Backend)

**Django Best Practices:**
```python
# Use class-based views
class UserListAPIView(generics.ListCreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

# Follow Django naming conventions
class TenantEmail(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    email = models.EmailField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'tenant_emails'
        ordering = ['-created_at']
```

**Code Formatting:**
```bash
# Use Black for formatting
pip install black
black .

# Use isort for imports
pip install isort
isort .
```

### JavaScript (Frontend)

**React Best Practices:**
```javascript
// Use functional components with hooks
const UserProfile = () => {
  const [user, setUser] = useState(null);
  const { isAuthenticated } = useAuth();

  useEffect(() => {
    if (isAuthenticated) {
      fetchUserProfile();
    }
  }, [isAuthenticated]);

  return (
    <div className="user-profile">
      {user && <UserDetails user={user} />}
    </div>
  );
};

// Export default at the bottom
export default UserProfile;
```

**Code Formatting:**
```bash
# Use Prettier
npm install --save-dev prettier
npm run format
```

## 🧪 Testing

### Backend Testing

```bash
# Run all tests
python manage.py test

# Run specific app tests
python manage.py test core

# Run with coverage
pip install coverage
coverage run --source '.' manage.py test
coverage report
```

**Writing Tests:**
```python
from django.test import TestCase
from django.contrib.auth import get_user_model

class UserModelTest(TestCase):
    def setUp(self):
        self.User = get_user_model()
    
    def test_create_user(self):
        user = self.User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.assertEqual(user.username, 'testuser')
        self.assertTrue(user.check_password('testpass123'))
```

### Frontend Testing

```bash
# Run tests
npm test

# Run tests with coverage
npm test -- --coverage
```

**Writing Tests:**
```javascript
import { render, screen } from '@testing-library/react';
import { AuthProvider } from '../context/AuthContext';
import Dashboard from '../pages/Dashboard';

test('renders dashboard for authenticated user', () => {
  render(
    <AuthProvider>
      <Dashboard />
    </AuthProvider>
  );
  
  expect(screen.getByText('Dashboard')).toBeInTheDocument();
});
```

## 🐛 Debugging

### Backend Debugging

**Django Debug Toolbar:**
```python
# settings.py
if DEBUG:
    INSTALLED_APPS += ['debug_toolbar']
    MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']
```

**Logging Configuration:**
```python
# settings.py
LOGGING = {
    'version': 1,
    'handlers': {
        'file': {
            'class': 'logging.FileHandler',
            'filename': 'debug.log',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'DEBUG',
        },
    },
}
```

### Frontend Debugging

**React Developer Tools:**
```bash
# Install browser extension
# Chrome: React Developer Tools
# Firefox: React Developer Tools
```

**Debug API Calls:**
```javascript
// utils/api.js
api.interceptors.request.use(request => {
  console.log('Starting Request', request);
  return request;
});

api.interceptors.response.use(
  response => {
    console.log('Response:', response);
    return response;
  },
  error => {
    console.error('API Error:', error);
    return Promise.reject(error);
  }
);
```

## 🛠️ Common Tasks

### Adding New API Endpoint

1. **Create Serializer:**
```python
# serializers.py
class NewModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = NewModel
        fields = '__all__'
```

2. **Create View:**
```python
# views.py
class NewModelViewSet(viewsets.ModelViewSet):
    queryset = NewModel.objects.all()
    serializer_class = NewModelSerializer
    permission_classes = [IsAuthenticated]
```

3. **Add URL:**
```python
# urls.py
from rest_framework.routers import DefaultRouter
router = DefaultRouter()
router.register(r'newmodels', NewModelViewSet)
```

### Adding New Frontend Page

1. **Create Page Component:**
```javascript
// pages/NewPage.js
import React from 'react';

const NewPage = () => {
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">New Page</h1>
      {/* Page content */}
    </div>
  );
};

export default NewPage;
```

2. **Add Route:**
```javascript
// App.js
import NewPage from './pages/NewPage';

// Add to routes
<Route path="new-page" element={<NewPage />} />
```

3. **Add Navigation:**
```javascript
// components/Layout.js
const navigation = [
  // existing items...
  { name: 'New Page', href: '/new-page', icon: IconName },
];
```

### Database Migrations

```bash
# Create migration
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Rollback migration
python manage.py migrate app_name 0001

# Show migration status
python manage.py showmigrations
```

### Adding New Dependencies

**Backend:**
```bash
# Add to requirements.txt
pip install new-package
pip freeze > requirements.txt
```

**Frontend:**
```bash
# Add package
npm install new-package

# Add dev dependency
npm install --save-dev new-dev-package
```

## 🔗 Related Documentation

- [API Documentation](./API.md)
- [Database Schema](./DATABASE.md)
- [Architecture Overview](./ARCHITECTURE.md)
- [Deployment Guide](./DEPLOYMENT.md)
- [Contributing Guidelines](./CONTRIBUTING.md)

## 📞 Getting Help

- **GitHub Issues**: Report bugs and request features
- **Discussion Forum**: Ask questions and discuss ideas
- **Code Review**: Submit pull requests for review

---

**Happy Coding!** 🚀