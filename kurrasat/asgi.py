# asgi.py
import os
import django

# Set the settings module before any other imports
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kurrasat.settings')

# Set up Django explicitly - this is critical
django.setup()

# Import Django's default ASGI application
from django.core.asgi import get_asgi_application

# Only handle HTTP protocol
application = get_asgi_application()
