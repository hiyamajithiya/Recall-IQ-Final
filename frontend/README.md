# RecallIQ Frontend

A modern React frontend for the RecallIQ multi-tenant email reminder system.

## Features

- **Modern React Architecture**: Built with React 18, React Router v6, and Context API
- **Beautiful UI**: Tailwind CSS with Headless UI components
- **Authentication**: JWT-based authentication with automatic token refresh
- **Dashboard**: Comprehensive analytics and insights with Chart.js
- **Email Templates**: Rich template editor with preview and testing
- **Contact Management**: Organize contacts into groups with bulk operations
- **Batch Management**: Create and monitor email campaigns
- **Real-time Tracking**: Monitor email delivery status and analytics
- **Responsive Design**: Mobile-first responsive design
- **Role-based Access**: Different views for Super Admin, Tenant Admin, and Staff
- **Form Validation**: React Hook Form with comprehensive validation

## Tech Stack

- **Framework**: React 18
- **Routing**: React Router v6
- **State Management**: Context API
- **Styling**: Tailwind CSS + Headless UI
- **Charts**: Chart.js + React Chart.js 2
- **Forms**: React Hook Form
- **HTTP Client**: Axios
- **Icons**: Heroicons
- **Notifications**: React Hot Toast
- **Date Handling**: date-fns

## Project Structure

```
src/
├── components/          # Reusable components
│   ├── Dashboard/      # Dashboard-specific components
│   ├── Templates/      # Template management components
│   ├── Layout.js       # Main app layout
│   └── ProtectedRoute.js
├── context/            # React contexts
│   └── AuthContext.js  # Authentication context
├── hooks/              # Custom hooks
├── pages/              # Page components
│   ├── Dashboard.js
│   ├── Templates.js
│   ├── Groups.js
│   ├── Batches.js
│   ├── Logs.js
│   ├── Analytics.js
│   ├── Users.js
│   ├── Tenants.js
│   ├── Login.js
│   └── Register.js
├── utils/              # Utility functions
│   └── api.js          # API client
├── App.js              # Main app component
├── index.js            # App entry point
└── index.css           # Global styles
```

## Installation

1. **Navigate to frontend directory**
   ```bash
   cd frontend
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Environment Configuration**
   Create a `.env` file in the frontend directory:
   ```bash
   REACT_APP_API_URL=http://localhost:8000/api
   ```

4. **Start development server**
   ```bash
   npm start
   ```

   The app will be available at `http://localhost:3000`

## Available Scripts

- `npm start` - Start development server
- `npm build` - Build for production
- `npm test` - Run tests
- `npm run eject` - Eject from Create React App (not recommended)

## Features Overview

### Authentication
- JWT-based authentication with automatic token refresh
- Login and registration pages
- Protected routes based on user roles
- Logout functionality

### Dashboard
- Overview statistics and metrics
- Email activity charts
- Recent activity feed
- Upcoming batch schedules
- Performance analytics

### Email Templates
- Create and edit email templates
- HTML and plain text support
- Template variable system
- Live preview functionality
- Test email sending
- Template management (CRUD operations)

### Contact Groups
- Create and manage contact groups
- Bulk email import/export
- Contact organization
- Group statistics

### Batch Management
- Create email campaigns
- Schedule batch sending
- Monitor batch progress
- Batch control (start, pause, resume, cancel)
- Real-time progress tracking

### Email Logs
- Comprehensive email tracking
- Filtering and search capabilities
- Export functionality
- Delivery status monitoring
- Failed email analysis

### Analytics
- Email performance metrics
- Daily activity charts
- Status and type distributions
- Success rate analysis
- Historical data visualization

### User Management (Super Admin)
- User account management
- Role assignment
- Tenant association
- User activity monitoring

### Tenant Management (Super Admin)
- Tenant organization management
- Tenant settings
- Multi-tenant isolation
- Tenant analytics

## API Integration

The frontend communicates with the Django backend through a comprehensive API client (`src/utils/api.js`) that includes:

- Automatic JWT token handling
- Request/response interceptors
- Error handling and user feedback
- API endpoint organization by feature

### API Endpoints Used

- **Authentication**: `/api/auth/`
- **Tenants**: `/api/tenants/`
- **Email Templates**: `/api/emails/`
- **Batches**: `/api/batches/`
- **Email Logs**: `/api/logs/`

## Styling and UI

### Tailwind CSS Classes
The app uses a consistent design system with custom Tailwind classes:

- `.btn-primary` - Primary action buttons
- `.btn-secondary` - Secondary buttons
- `.btn-danger` - Destructive actions
- `.card` - Content containers
- `.form-input` - Form inputs
- `.form-label` - Form labels
- `.badge-*` - Status indicators

### Color Scheme
- **Primary**: Blue (#3B82F6)
- **Success**: Green (#10B981)
- **Warning**: Yellow (#F59E0B)
- **Danger**: Red (#EF4444)
- **Gray**: Various gray shades for text and backgrounds

## State Management

The app uses React Context API for state management:

### AuthContext
- User authentication state
- Login/logout functionality
- Token management
- User profile data

## Routing

Protected routing system with role-based access:

- Public routes: `/login`, `/register`
- Protected routes: All other routes require authentication
- Admin routes: `/users`, `/tenants` (Super Admin only)

## Error Handling

Comprehensive error handling throughout the application:

- API error interceptors
- User-friendly error messages
- Form validation errors
- Network error handling
- Toast notifications for feedback

## Performance Optimizations

- Lazy loading of routes
- Optimized re-renders with proper state management
- Chart.js for efficient data visualization
- Responsive images and assets
- Efficient API calls with proper loading states

## Browser Support

- Chrome 88+
- Firefox 85+
- Safari 14+
- Edge 88+

## Development Guidelines

### Code Style
- Use functional components with hooks
- Follow React best practices
- Consistent naming conventions
- Proper component organization

### State Management
- Use Context API for global state
- Local state for component-specific data
- Custom hooks for reusable logic

### Styling
- Tailwind utility classes
- Custom CSS classes for reusable styles
- Responsive design principles
- Consistent spacing and typography

## Deployment

### Build for Production
```bash
npm run build
```

### Deploy to Static Host
The build folder can be deployed to any static hosting service:
- Netlify
- Vercel
- AWS S3 + CloudFront
- GitHub Pages

### Environment Variables
Set the following environment variables for production:
- `REACT_APP_API_URL` - Backend API URL

## Testing

The app includes basic testing setup with Create React App's testing utilities:

```bash
npm test
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License.