# API Documentation - RecallIQ

This document provides comprehensive API documentation for RecallIQ's RESTful API endpoints.

## 🔗 Base URL

```
Development: http://localhost:8000/api
Production: https://your-domain.com/api
```

## 🔐 Authentication

RecallIQ uses JWT (JSON Web Token) authentication.

### Login
```http
POST /auth/login/
Content-Type: application/json

{
    "username": "admin",
    "password": "admin123"
}
```

**Response:**
```json
{
    "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "user": {
        "id": 1,
        "username": "admin",
        "email": "admin@recalliq.com",
        "role": "super_admin",
        "tenant": null
    }
}
```

### Token Refresh
```http
POST /auth/refresh/
Content-Type: application/json

{
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

### Using Authentication
Include the access token in the Authorization header:
```http
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

## 👤 Authentication Endpoints

### Get User Profile
```http
GET /auth/profile/
Authorization: Bearer <access_token>
```

**Response:**
```json
{
    "id": 1,
    "username": "admin",
    "email": "admin@recalliq.com",
    "first_name": "Super",
    "last_name": "Admin",
    "role": "super_admin",
    "tenant": null,
    "is_active": true,
    "created_at": "2024-01-01T10:00:00Z"
}
```

### Get Dashboard Data
```http
GET /auth/dashboard/
Authorization: Bearer <access_token>
```

**Response:**
```json
{
    "total_emails": 1250,
    "emails_sent_today": 45,
    "active_batches": 3,
    "templates_count": 8,
    "groups_count": 12,
    "success_rate": 98.5,
    "recent_activity": [
        {
            "id": 1,
            "type": "batch_completed",
            "message": "Welcome Campaign Q1 completed",
            "time": "2 hours ago"
        }
    ]
}
```

### Get Users (Super Admin Only)
```http
GET /auth/users/
Authorization: Bearer <access_token>
```

**Response:**
```json
[
    {
        "id": 1,
        "username": "admin",
        "email": "admin@recalliq.com",
        "first_name": "Super",
        "last_name": "Admin",
        "role": "super_admin",
        "tenant": null,
        "is_active": true,
        "created_at": "2024-01-01T10:00:00Z"
    }
]
```

## 🏢 Tenant Management

### List Tenants
```http
GET /tenants/
Authorization: Bearer <access_token>
```

**Response:**
```json
{
    "count": 2,
    "results": [
        {
            "id": 1,
            "name": "Acme Corporation",
            "domain": "acme.com",
            "is_active": true,
            "plan": "professional",
            "status": "active",
            "contact_person": "John Smith",
            "contact_email": "john@acme.com",
            "monthly_email_limit": 10000,
            "emails_sent_this_month": 2500,
            "created_at": "2024-01-05T10:00:00Z"
        }
    ]
}
```

### Create Tenant
```http
POST /tenants/
Authorization: Bearer <access_token>
Content-Type: application/json

{
    "name": "New Company",
    "domain": "newcompany.com",
    "contact_person": "Jane Doe",
    "contact_email": "jane@newcompany.com",
    "plan": "basic",
    "monthly_email_limit": 5000
}
```

### Update Tenant
```http
PUT /tenants/{id}/
Authorization: Bearer <access_token>
Content-Type: application/json

{
    "name": "Updated Company Name",
    "monthly_email_limit": 15000
}
```

### Delete Tenant
```http
DELETE /tenants/{id}/
Authorization: Bearer <access_token>
```

## 👥 Contact Groups

### List Groups
```http
GET /tenants/groups/
Authorization: Bearer <access_token>
```

**Response:**
```json
{
    "count": 3,
    "results": [
        {
            "id": 1,
            "name": "VIP Customers",
            "description": "High-value customers",
            "is_active": true,
            "email_count": 15,
            "created_at": "2024-01-15T10:00:00Z"
        }
    ]
}
```

### Create Group
```http
POST /tenants/groups/
Authorization: Bearer <access_token>
Content-Type: application/json

{
    "name": "New Group",
    "description": "Description of the group",
    "is_active": true
}
```

### Bulk Add Emails to Group
```http
POST /tenants/groups/{id}/bulk_add_emails/
Authorization: Bearer <access_token>
Content-Type: application/json

{
    "emails": [
        {
            "email": "john@example.com",
            "name": "John Doe"
        },
        {
            "email": "jane@example.com",
            "name": "Jane Smith"
        }
    ]
}
```

### Upload Excel File
```http
POST /tenants/groups/{id}/upload_excel/
Authorization: Bearer <access_token>
Content-Type: multipart/form-data

file: <excel_file>
```

## 📧 Email Templates

### List Templates
```http
GET /emails/templates/
Authorization: Bearer <access_token>
```

**Response:**
```json
{
    "count": 3,
    "results": [
        {
            "id": 1,
            "name": "Welcome Email",
            "subject": "Welcome to {{company_name}}!",
            "body_html": "<h1>Welcome {{first_name}}!</h1>...",
            "body_text": "Welcome {{first_name}}!...",
            "is_active": true,
            "created_at": "2024-01-10T10:00:00Z"
        }
    ]
}
```

### Create Template
```http
POST /emails/templates/
Authorization: Bearer <access_token>
Content-Type: application/json

{
    "name": "New Template",
    "subject": "Subject with {{variable}}",
    "body_html": "<h1>HTML content</h1>",
    "body_text": "Plain text content",
    "is_active": true
}
```

### Preview Template
```http
POST /emails/templates/{id}/preview/
Authorization: Bearer <access_token>
Content-Type: application/json

{
    "variables": {
        "first_name": "John",
        "company_name": "Acme Corp"
    }
}
```

**Response:**
```json
{
    "subject": "Welcome to Acme Corp!",
    "body_html": "<h1>Welcome John!</h1>...",
    "body_text": "Welcome John!..."
}
```

### Send Test Email
```http
POST /emails/templates/{id}/send_test/
Authorization: Bearer <access_token>
Content-Type: application/json

{
    "test_email": "test@example.com",
    "variables": {
        "first_name": "Test User",
        "company_name": "Test Company"
    }
}
```

## 📬 Email Batches

### List Batches
```http
GET /batches/
Authorization: Bearer <access_token>
```

**Response:**
```json
{
    "count": 2,
    "results": [
        {
            "id": 1,
            "name": "Welcome Campaign Q1",
            "template": {
                "id": 1,
                "name": "Welcome Email"
            },
            "groups": [
                {
                    "id": 1,
                    "name": "VIP Customers"
                }
            ],
            "status": "completed",
            "scheduled_at": "2024-01-20T10:00:00Z",
            "sent_count": 15,
            "failed_count": 0,
            "created_at": "2024-01-19T15:30:00Z"
        }
    ]
}
```

### Create Batch
```http
POST /batches/
Authorization: Bearer <access_token>
Content-Type: application/json

{
    "name": "New Campaign",
    "template_id": 1,
    "group_ids": [1, 2],
    "scheduled_at": "2024-01-25T10:00:00Z",
    "variables": {
        "company_name": "Your Company"
    }
}
```

### Execute Batch Action
```http
POST /batches/{id}/execute_action/
Authorization: Bearer <access_token>
Content-Type: application/json

{
    "action": "start"  // "start", "pause", "resume", "cancel"
}
```

### Get Batch Statistics
```http
GET /batches/{id}/statistics/
Authorization: Bearer <access_token>
```

**Response:**
```json
{
    "total_recipients": 100,
    "sent_count": 95,
    "failed_count": 3,
    "pending_count": 2,
    "success_rate": 95.0,
    "status_breakdown": {
        "sent": 95,
        "failed": 3,
        "pending": 2
    }
}
```

## 📊 Logs and Analytics

### Get Email Logs
```http
GET /logs/emails/
Authorization: Bearer <access_token>
```

**Query Parameters:**
- `batch_id`: Filter by batch
- `status`: Filter by status (sent, failed, pending)
- `date_from`: Start date (YYYY-MM-DD)
- `date_to`: End date (YYYY-MM-DD)

**Response:**
```json
{
    "count": 100,
    "results": [
        {
            "id": 1,
            "batch": {
                "id": 1,
                "name": "Welcome Campaign Q1"
            },
            "recipient_email": "john@example.com",
            "status": "sent",
            "sent_at": "2024-01-20T10:05:00Z",
            "error_message": null
        }
    ]
}
```

### Get Email Log Statistics
```http
GET /logs/emails/statistics/
Authorization: Bearer <access_token>
```

**Response:**
```json
{
    "total_emails": 1000,
    "sent_emails": 950,
    "failed_emails": 50,
    "pending_emails": 0,
    "success_rate": 95.0,
    "by_status": {
        "sent": 950,
        "failed": 50,
        "pending": 0
    },
    "recent_activity": [
        {
            "date": "2024-01-20",
            "sent": 100,
            "failed": 5
        }
    ]
}
```

## ❌ Error Responses

### Standard Error Format
```json
{
    "error": "Error type",
    "message": "Human readable error message",
    "details": {
        "field_name": ["Field specific error message"]
    }
}
```

### Common HTTP Status Codes

| Code | Meaning | Description |
|------|---------|-------------|
| 200 | OK | Request successful |
| 201 | Created | Resource created successfully |
| 400 | Bad Request | Invalid request data |
| 401 | Unauthorized | Authentication required |
| 403 | Forbidden | Permission denied |
| 404 | Not Found | Resource not found |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server error |

### Example Error Responses

**Validation Error (400):**
```json
{
    "error": "Validation Error",
    "message": "Invalid data provided",
    "details": {
        "email": ["Enter a valid email address."],
        "name": ["This field is required."]
    }
}
```

**Authentication Error (401):**
```json
{
    "error": "Authentication Error",
    "message": "Invalid credentials provided"
}
```

**Permission Error (403):**
```json
{
    "error": "Permission Denied",
    "message": "You don't have permission to access this resource"
}
```

## 🔄 Rate Limiting

The API implements rate limiting to prevent abuse:

- **Anonymous users**: 100 requests per hour
- **Authenticated users**: 1000 requests per hour
- **Bulk operations**: 10 requests per minute

Rate limit headers are included in responses:
```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1640995200
```

## 📡 Webhooks (Coming Soon)

Webhook endpoints for real-time notifications:

- Batch completion
- Email delivery status
- Template updates
- User actions

## 🧪 Testing API

### Using cURL

```bash
# Login
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'

# Get profile
curl -X GET http://localhost:8000/api/auth/profile/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Using Postman

1. Import the API collection
2. Set up environment variables
3. Configure authentication
4. Test endpoints

### API Testing Tools

- **Postman**: GUI-based testing
- **Insomnia**: Alternative to Postman
- **HTTPie**: Command-line HTTP client
- **curl**: Built-in command-line tool

---

For more detailed examples and integration guides, see the [Developer Guide](./README.md).