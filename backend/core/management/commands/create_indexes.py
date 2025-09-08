"""
Management command to create performance indexes for 1000+ tenant scalability
"""
from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = 'Create performance indexes for RecallIQ V2 SUPERPOWER system'

    def handle(self, *args, **options):
        with connection.cursor() as cursor:
            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_batch_status_starttime ON batches (status, start_time);",
                "CREATE INDEX IF NOT EXISTS idx_batch_tenant_status ON batches (tenant_id, status);", 
                "CREATE INDEX IF NOT EXISTS idx_batch_starttime ON batches (start_time);",
                "CREATE INDEX IF NOT EXISTS idx_batchrecipient_batch ON batch_recipients (batch_id);",
                "CREATE INDEX IF NOT EXISTS idx_batchrecipient_status ON batch_recipients (status);",
                "CREATE INDEX IF NOT EXISTS idx_emaillog_batch ON email_logs (batch_id);",
                "CREATE INDEX IF NOT EXISTS idx_emaillog_created ON email_logs (created_at);",
            ]
            
            self.stdout.write("🚀 Creating SUPERPOWER performance indexes...")
            
            for sql in indexes:
                try:
                    cursor.execute(sql)
                    index_name = sql.split("idx_")[1].split(" ")[0]
                    self.stdout.write(f"✅ Created index: {index_name}")
                except Exception as e:
                    self.stdout.write(f"❌ Failed to create index: {e}")
            
            self.stdout.write("\n🔥 Performance indexes created for 1000+ tenant scalability!")
            self.stdout.write("🎯 Your RecallIQ V2 is now SUPERPOWER optimized!")
