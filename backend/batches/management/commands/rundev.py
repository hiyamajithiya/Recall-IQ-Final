import os
import sys
import signal
import subprocess
import threading
import time
from django.core.management.base import BaseCommand
from django.core.management import execute_from_command_line


class Command(BaseCommand):
    help = 'Start Django development server with Celery worker and Celery beat'
    
    def __init__(self):
        super().__init__()
        self.processes = []
        self.running = False
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--host',
            default='127.0.0.1',
            help='Host to run Django server on (default: 127.0.0.1)'
        )
        parser.add_argument(
            '--port',
            default='8000',
            help='Port to run Django server on (default: 8000)'
        )
        parser.add_argument(
            '--no-celery',
            action='store_true',
            help='Start only Django server without Celery'
        )
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        self.stdout.write(self.style.WARNING('\n🛑 Shutting down services...'))
        self.running = False
        self.cleanup_processes()
        sys.exit(0)
    
    def cleanup_processes(self):
        """Terminate all running processes"""
        for process in self.processes:
            if process.poll() is None:  # Process is still running
                try:
                    process.terminate()
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'Error terminating process: {e}')
                    )
    
    def start_process(self, command, name, cwd=None):
        """Start a subprocess and add it to the processes list"""
        try:
            self.stdout.write(f'🚀 Starting {name}...')
            process = subprocess.Popen(
                command,
                shell=True,
                cwd=cwd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1
            )
            self.processes.append(process)
            
            # Start a thread to monitor process output
            thread = threading.Thread(
                target=self.monitor_process,
                args=(process, name),
                daemon=True
            )
            thread.start()
            
            return process
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Failed to start {name}: {e}')
            )
            return None
    
    def monitor_process(self, process, name):
        """Monitor process output and display it"""
        while self.running and process.poll() is None:
            try:
                output = process.stdout.readline()
                if output:
                    # Color code output based on service
                    if 'celery worker' in name.lower():
                        prefix = '🔧 [WORKER]'
                        style = self.style.HTTP_INFO
                    elif 'celery beat' in name.lower():
                        prefix = '⏰ [BEAT]'
                        style = self.style.WARNING
                    else:
                        prefix = '🌐 [DJANGO]'
                        style = self.style.SUCCESS
                    
                    self.stdout.write(f'{prefix} {output.strip()}')
            except Exception:
                break
    
    def handle(self, *args, **options):
        self.running = True
        
        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        host = options['host']
        port = options['port']
        no_celery = options['no_celery']
        
        self.stdout.write(
            self.style.SUCCESS('🎯 Starting RecallIQ Development Environment\n')
        )
        
        # Start Celery services (if not disabled)
        if not no_celery:
            # Start Celery worker
            worker_command = f'python -m celery -A recalliq worker --loglevel=info --concurrency=2'
            self.start_process(worker_command, 'Celery Worker')
            
            # Give worker time to start
            time.sleep(2)
            
            # Start Celery beat
            beat_command = f'python -m celery -A recalliq beat --loglevel=info'
            self.start_process(beat_command, 'Celery Beat')
            
            # Give beat time to start
            time.sleep(2)
        
        # Start Django development server
        django_command = f'python manage.py runserver {host}:{port} --noreload'
        django_process = self.start_process(django_command, 'Django Server')
        
        if django_process is None:
            self.cleanup_processes()
            return
        
        # Display startup summary
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('✅ All services started successfully!'))
        self.stdout.write('='*60)
        self.stdout.write(f'🌐 Django Server: http://{host}:{port}/')
        
        if not no_celery:
            self.stdout.write('🔧 Celery Worker: Running with 2 concurrent workers')
            self.stdout.write('⏰ Celery Beat: Running scheduled tasks')
            self.stdout.write('\n📋 Scheduled Tasks:')
            self.stdout.write('   • Batch status updates: Every 30 seconds')
            self.stdout.write('   • Recurring batches: Every 60 seconds') 
            self.stdout.write('   • Cleanup old logs: Daily')
        
        self.stdout.write('\n💡 Press Ctrl+C to stop all services')
        self.stdout.write('='*60 + '\n')
        
        # Keep the main thread alive and monitor processes
        try:
            while self.running:
                # Check if any critical process has died
                if django_process.poll() is not None:
                    self.stdout.write(
                        self.style.ERROR('❌ Django server has stopped!')
                    )
                    break
                
                # Check for dead processes
                dead_processes = [p for p in self.processes if p.poll() is not None]
                if dead_processes and self.running:
                    for process in dead_processes:
                        self.stdout.write(
                            self.style.WARNING('⚠️  A service process has died')
                        )
                
                time.sleep(1)
                
        except KeyboardInterrupt:
            pass
        finally:
            self.cleanup_processes()
