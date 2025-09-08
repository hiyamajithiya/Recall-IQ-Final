from django.apps import AppConfig


class BatchesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'batches'
    
    def ready(self):
        import batches.signals
        
        # Automatically ensure automation is always enabled on startup
        try:
            from django.core.management import call_command
            from django.db import connection
            from django.db.utils import OperationalError
            
            # Check if database is ready (avoid errors during migrations)
            try:
                connection.ensure_connection()
                if connection.is_usable():
                    call_command('ensure_automation')
                    print("🔄 Batch automation automatically enabled on startup")
            except OperationalError:
                # Database not ready yet (during migrations), skip
                pass
        except Exception as e:
            # Silent fail - don't break app startup
            print(f"Note: Automation will be enabled manually: {e}")
            pass