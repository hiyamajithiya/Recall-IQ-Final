# Migration helper for adding retry_count field to EmailLog model
# This file documents the required database changes

MIGRATION_NOTES = """
To complete the email batch fixes, the following database migration is needed:

1. Add 'retry_count' field to logs.EmailLog model:
   - Field: retry_count = models.IntegerField(default=0)
   - This tracks how many times an email has been retried

2. Add indexes for performance:
   - Index on (tenant, created_at) for rate limiting queries
   - Index on (batch, status) for batch processing queries

3. Optional: Add 'correlation_id' field for better logging:
   - Field: correlation_id = models.CharField(max_length=32, blank=True, null=True)

Example Django migration:

```python
from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('logs', 'XXXX_previous_migration'),
    ]

    operations = [
        migrations.AddField(
            model_name='emaillog',
            name='retry_count',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='emaillog',
            name='correlation_id',
            field=models.CharField(max_length=32, blank=True, null=True),
        ),
        migrations.AddIndex(
            model_name='emaillog',
            index=models.Index(fields=['tenant', 'created_at'], name='emaillog_tenant_created_idx'),
        ),
        migrations.AddIndex(
            model_name='emaillog',
            index=models.Index(fields=['batch', 'status'], name='emaillog_batch_status_idx'),
        ),
    ]
```
"""

print(MIGRATION_NOTES)