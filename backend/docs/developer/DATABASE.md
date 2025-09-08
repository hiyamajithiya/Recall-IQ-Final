# Database Schema - RecallIQ

This document describes the database structure and relationships for RecallIQ.

## 🗃️ Database Overview

RecallIQ uses a PostgreSQL database (SQLite for development) with a multi-tenant architecture. Data is logically separated by tenant while sharing the same database schema.

## 📊 Entity Relationship Diagram

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│      Users      │    │     Tenants     │    │   TenantEmails  │
├─────────────────┤    ├─────────────────┤    ├─────────────────┤
│ id (PK)         │    │ id (PK)         │    │ id (PK)         │
│ username        │    │ name            │    │ tenant_id (FK)  │
│ email           │    │ domain          │    │ email           │
│ password        │    │ is_active       │    │ name            │
│ first_name      │    │ plan            │    │ is_active       │
│ last_name       │    │ status          │    │ created_at      │
│ role            │    │ contact_person  │    └─────────────────┘
│ tenant_id (FK)  │    │ contact_email   │           │
│ is_active       │    │ billing_email   │           │
│ created_at      │    │ company_address │           │
└─────────────────┘    │ monthly_email_  │           │
         │              │   _limit        │           │
         │              │ emails_sent_    │           │
         │              │   _this_month   │           │
         │              │ created_at      │           │
         │              └─────────────────┘           │
         │                       │                    │
         └───────────────────────┼────────────────────┘
                                 │
    ┌─────────────────┐         │         ┌─────────────────┐
    │     Groups      │         │         │ EmailTemplates  │
    ├─────────────────┤         │         ├─────────────────┤
    │ id (PK)         │         │         │ id (PK)         │
    │ tenant_id (FK)  │─────────┘         │ tenant_id (FK)  │
    │ name            │                   │ name            │
    │ description     │                   │ subject         │
    │ is_active       │                   │ body_html       │
    │ created_at      │                   │ body_text       │
    └─────────────────┘                   │ is_active       │
             │                            │ created_at      │
             │                            └─────────────────┘
             │                                     │
    ┌─────────────────┐                          │
    │   GroupEmails   │                          │
    ├─────────────────┤                          │
    │ id (PK)         │                          │
    │ group_id (FK)   │──────────────────────────┘
    │ email           │                          │
    │ name            │                          │
    │ is_active       │                          │
    │ created_at      │                          │
    └─────────────────┘                          │
             │                            ┌─────────────────┐
             │                            │     Batches     │
             │                            ├─────────────────┤
             │                            │ id (PK)         │
             │                            │ tenant_id (FK)  │
             │                            │ template_id(FK) │
             │                            │ name            │
             │                            │ status          │
             │                            │ scheduled_at    │
             │                            │ sent_count      │
             │                            │ failed_count    │
             │                            │ variables       │
             │                            │ created_at      │
             │                            └─────────────────┘
             │                                     │
             │                                     │
    ┌─────────────────┐                          │
    │  BatchGroups    │                          │
    ├─────────────────┤                          │
    │ id (PK)         │                          │
    │ batch_id (FK)   │──────────────────────────┘
    │ group_id (FK)   │──────────────────────────┐
    └─────────────────┘                          │
                                                 │
    ┌─────────────────┐                          │
    │   EmailLogs     │                          │
    ├─────────────────┤                          │
    │ id (PK)         │                          │
    │ batch_id (FK)   │──────────────────────────┘
    │ recipient_email │
    │ status          │
    │ sent_at         │
    │ error_message   │
    │ created_at      │
    └─────────────────┘
```

## 📋 Table Definitions

### Core Tables

#### Users
Stores all user accounts across tenants.

```sql
CREATE TABLE core_user (
    id SERIAL PRIMARY KEY,
    username VARCHAR(150) UNIQUE NOT NULL,
    email VARCHAR(254) UNIQUE NOT NULL,
    password VARCHAR(128) NOT NULL,
    first_name VARCHAR(150),
    last_name VARCHAR(150),
    role VARCHAR(20) NOT NULL DEFAULT 'user',
    tenant_id INTEGER REFERENCES tenants_tenant(id),
    is_active BOOLEAN DEFAULT TRUE,
    is_staff BOOLEAN DEFAULT FALSE,
    is_superuser BOOLEAN DEFAULT FALSE,
    date_joined TIMESTAMP DEFAULT NOW(),
    last_login TIMESTAMP
);

-- Indexes
CREATE INDEX idx_user_tenant ON core_user(tenant_id);
CREATE INDEX idx_user_role ON core_user(role);
CREATE INDEX idx_user_email ON core_user(email);
```

**Fields:**
- `id`: Primary key
- `username`: Unique username
- `email`: Unique email address
- `password`: Hashed password
- `first_name`, `last_name`: User's name
- `role`: User role (super_admin, tenant_admin, staff, user)
- `tenant_id`: Foreign key to tenant (null for super admins)
- `is_active`: Account status
- `date_joined`: Account creation timestamp

#### Tenants
Stores tenant/organization information.

```sql
CREATE TABLE tenants_tenant (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    domain VARCHAR(100) UNIQUE NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    plan VARCHAR(50) DEFAULT 'basic',
    status VARCHAR(20) DEFAULT 'active',
    contact_person VARCHAR(200),
    contact_email VARCHAR(254),
    billing_email VARCHAR(254),
    company_address TEXT,
    phone_number VARCHAR(20),
    monthly_email_limit INTEGER DEFAULT 1000,
    emails_sent_this_month INTEGER DEFAULT 0,
    settings JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_tenant_domain ON tenants_tenant(domain);
CREATE INDEX idx_tenant_status ON tenants_tenant(status);
CREATE INDEX idx_tenant_plan ON tenants_tenant(plan);
```

**Fields:**
- `id`: Primary key
- `name`: Tenant organization name
- `domain`: Unique domain identifier
- `is_active`: Tenant status
- `plan`: Subscription plan (basic, professional, enterprise)
- `status`: Account status (active, suspended, trial)
- `contact_person`: Primary contact name
- `contact_email`: Primary contact email
- `monthly_email_limit`: Email sending limit
- `emails_sent_this_month`: Current month usage
- `settings`: JSON configuration

### Email Management Tables

#### EmailTemplates
Stores email templates for each tenant.

```sql
CREATE TABLE emails_emailtemplate (
    id SERIAL PRIMARY KEY,
    tenant_id INTEGER NOT NULL REFERENCES tenants_tenant(id),
    name VARCHAR(200) NOT NULL,
    subject VARCHAR(500) NOT NULL,
    body_html TEXT,
    body_text TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    variables JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_template_tenant ON emails_emailtemplate(tenant_id);
CREATE INDEX idx_template_active ON emails_emailtemplate(is_active);
```

**Fields:**
- `id`: Primary key
- `tenant_id`: Foreign key to tenant
- `name`: Template name
- `subject`: Email subject with variables
- `body_html`: HTML email content
- `body_text`: Plain text email content
- `is_active`: Template status
- `variables`: Available template variables

#### Groups
Stores contact groups for each tenant.

```sql
CREATE TABLE tenants_group (
    id SERIAL PRIMARY KEY,
    tenant_id INTEGER NOT NULL REFERENCES tenants_tenant(id),
    name VARCHAR(200) NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_group_tenant ON tenants_group(tenant_id);
CREATE INDEX idx_group_active ON tenants_group(is_active);
```

#### GroupEmails
Stores email addresses within each group.

```sql
CREATE TABLE tenants_groupemail (
    id SERIAL PRIMARY KEY,
    group_id INTEGER NOT NULL REFERENCES tenants_group(id),
    email VARCHAR(254) NOT NULL,
    name VARCHAR(200),
    is_active BOOLEAN DEFAULT TRUE,
    variables JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_groupemail_group ON tenants_groupemail(group_id);
CREATE INDEX idx_groupemail_email ON tenants_groupemail(email);
CREATE INDEX idx_groupemail_active ON tenants_groupemail(is_active);

-- Unique constraint
ALTER TABLE tenants_groupemail 
ADD CONSTRAINT unique_group_email 
UNIQUE (group_id, email);
```

### Campaign Management Tables

#### Batches
Stores email campaign batches.

```sql
CREATE TABLE batches_batch (
    id SERIAL PRIMARY KEY,
    tenant_id INTEGER NOT NULL REFERENCES tenants_tenant(id),
    template_id INTEGER NOT NULL REFERENCES emails_emailtemplate(id),
    name VARCHAR(200) NOT NULL,
    status VARCHAR(20) DEFAULT 'draft',
    scheduled_at TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    sent_count INTEGER DEFAULT 0,
    failed_count INTEGER DEFAULT 0,
    variables JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_batch_tenant ON batches_batch(tenant_id);
CREATE INDEX idx_batch_template ON batches_batch(template_id);
CREATE INDEX idx_batch_status ON batches_batch(status);
CREATE INDEX idx_batch_scheduled ON batches_batch(scheduled_at);
```

**Status Values:**
- `draft`: Being created
- `scheduled`: Scheduled for future
- `running`: Currently sending
- `paused`: Temporarily stopped
- `completed`: Finished successfully
- `failed`: Failed to complete
- `cancelled`: Manually stopped

#### BatchGroups
Many-to-many relationship between batches and groups.

```sql
CREATE TABLE batches_batchgroup (
    id SERIAL PRIMARY KEY,
    batch_id INTEGER NOT NULL REFERENCES batches_batch(id),
    group_id INTEGER NOT NULL REFERENCES tenants_group(id),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_batchgroup_batch ON batches_batchgroup(batch_id);
CREATE INDEX idx_batchgroup_group ON batches_batchgroup(group_id);

-- Unique constraint
ALTER TABLE batches_batchgroup 
ADD CONSTRAINT unique_batch_group 
UNIQUE (batch_id, group_id);
```

### Logging Tables

#### EmailLogs
Stores individual email sending logs.

```sql
CREATE TABLE logs_emaillog (
    id SERIAL PRIMARY KEY,
    batch_id INTEGER NOT NULL REFERENCES batches_batch(id),
    recipient_email VARCHAR(254) NOT NULL,
    recipient_name VARCHAR(200),
    status VARCHAR(20) NOT NULL,
    sent_at TIMESTAMP,
    error_message TEXT,
    smtp_response TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_emaillog_batch ON logs_emaillog(batch_id);
CREATE INDEX idx_emaillog_recipient ON logs_emaillog(recipient_email);
CREATE INDEX idx_emaillog_status ON logs_emaillog(status);
CREATE INDEX idx_emaillog_sent_at ON logs_emaillog(sent_at);
```

**Status Values:**
- `pending`: Queued for sending
- `sending`: Currently being sent
- `sent`: Successfully delivered
- `failed`: Failed to send
- `bounced`: Email bounced back
- `rejected`: Rejected by recipient server

#### BatchExecutionLogs
Stores batch-level execution logs.

```sql
CREATE TABLE logs_batchexecutionlog (
    id SERIAL PRIMARY KEY,
    batch_id INTEGER NOT NULL REFERENCES batches_batch(id),
    action VARCHAR(50) NOT NULL,
    message TEXT,
    details JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_batchlog_batch ON logs_batchexecutionlog(batch_id);
CREATE INDEX idx_batchlog_action ON logs_batchexecutionlog(action);
CREATE INDEX idx_batchlog_created ON logs_batchexecutionlog(created_at);
```

## 🔍 Common Queries

### Get Tenant Statistics
```sql
SELECT 
    t.name,
    t.monthly_email_limit,
    t.emails_sent_this_month,
    COUNT(DISTINCT u.id) as user_count,
    COUNT(DISTINCT g.id) as group_count,
    COUNT(DISTINCT et.id) as template_count,
    COUNT(DISTINCT b.id) as batch_count
FROM tenants_tenant t
LEFT JOIN core_user u ON t.id = u.tenant_id
LEFT JOIN tenants_group g ON t.id = g.tenant_id
LEFT JOIN emails_emailtemplate et ON t.id = et.tenant_id  
LEFT JOIN batches_batch b ON t.id = b.tenant_id
WHERE t.is_active = TRUE
GROUP BY t.id, t.name, t.monthly_email_limit, t.emails_sent_this_month;
```

### Get Batch Performance
```sql
SELECT 
    b.name,
    b.status,
    b.sent_count,
    b.failed_count,
    ROUND(
        (b.sent_count::FLOAT / NULLIF(b.sent_count + b.failed_count, 0)) * 100, 
        2
    ) as success_rate,
    b.scheduled_at,
    b.completed_at,
    EXTRACT(EPOCH FROM (b.completed_at - b.started_at))/60 as duration_minutes
FROM batches_batch b
WHERE b.tenant_id = :tenant_id
ORDER BY b.created_at DESC;
```

### Get Email Activity by Date
```sql
SELECT 
    DATE(el.sent_at) as date,
    COUNT(*) as total_emails,
    COUNT(CASE WHEN el.status = 'sent' THEN 1 END) as sent_emails,
    COUNT(CASE WHEN el.status = 'failed' THEN 1 END) as failed_emails,
    ROUND(
        (COUNT(CASE WHEN el.status = 'sent' THEN 1 END)::FLOAT / COUNT(*)) * 100,
        2
    ) as success_rate
FROM logs_emaillog el
JOIN batches_batch b ON el.batch_id = b.id
WHERE b.tenant_id = :tenant_id
    AND el.sent_at >= :date_from
    AND el.sent_at <= :date_to
GROUP BY DATE(el.sent_at)
ORDER BY date DESC;
```

### Get Group Email Counts
```sql
SELECT 
    g.name,
    g.description,
    COUNT(ge.id) as email_count,
    COUNT(CASE WHEN ge.is_active = TRUE THEN 1 END) as active_emails
FROM tenants_group g
LEFT JOIN tenants_groupemail ge ON g.id = ge.group_id
WHERE g.tenant_id = :tenant_id AND g.is_active = TRUE
GROUP BY g.id, g.name, g.description
ORDER BY email_count DESC;
```

## 🔧 Database Maintenance

### Regular Maintenance Tasks

#### Clean Old Logs
```sql
-- Delete email logs older than 90 days
DELETE FROM logs_emaillog 
WHERE created_at < NOW() - INTERVAL '90 days';

-- Delete batch execution logs older than 30 days
DELETE FROM logs_batchexecutionlog 
WHERE created_at < NOW() - INTERVAL '30 days';
```

#### Update Email Usage Counters
```sql
-- Reset monthly counters (run monthly)
UPDATE tenants_tenant 
SET emails_sent_this_month = 0 
WHERE date_trunc('month', created_at) != date_trunc('month', NOW());

-- Update current month usage
UPDATE tenants_tenant t
SET emails_sent_this_month = (
    SELECT COALESCE(SUM(b.sent_count), 0)
    FROM batches_batch b
    WHERE b.tenant_id = t.id
    AND date_trunc('month', b.completed_at) = date_trunc('month', NOW())
);
```

### Performance Optimization

#### Useful Indexes
```sql
-- Composite indexes for common queries
CREATE INDEX idx_emaillog_batch_status ON logs_emaillog(batch_id, status);
CREATE INDEX idx_emaillog_tenant_date ON logs_emaillog(batch_id, sent_at) 
    WHERE sent_at IS NOT NULL;

-- Partial indexes for active records
CREATE INDEX idx_user_active_tenant ON core_user(tenant_id) 
    WHERE is_active = TRUE;
CREATE INDEX idx_group_active_tenant ON tenants_group(tenant_id) 
    WHERE is_active = TRUE;
```

#### Query Optimization Tips
1. Always include tenant_id in WHERE clauses for tenant-specific queries
2. Use LIMIT for large result sets
3. Index frequently searched columns
4. Use partial indexes for boolean filters
5. Consider partitioning large tables by date

## 🛡️ Security Considerations

### Data Isolation
- All tenant data is logically separated by tenant_id
- Row-level security policies can be implemented
- No cross-tenant data access allowed

### Sensitive Data
- Passwords are hashed using Django's PBKDF2
- Email content may contain PII - ensure proper encryption at rest
- SMTP credentials should be encrypted
- Audit logs for data access

### Backup Strategy
- Daily full backups
- Point-in-time recovery capability
- Test restore procedures regularly
- Separate backup encryption keys

---

For more information about the database implementation, see the [Developer Guide](./README.md).