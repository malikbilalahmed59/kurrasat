# asgi.py
import os
import django

# Set the settings module before any other imports
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kurrasat.settings')

# Set up Django explicitly - this is critical
django.setup()

# Now import other components after Django is configured
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import documents.routing

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(
            documents.routing.websocket_urlpatterns
        )
    ),
})