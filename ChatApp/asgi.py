import os
import django
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from channels.auth import AuthMiddlewareStack

# Set default settings module early
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ChatApp.settings')

# Initialize Django before any database-dependent imports
django.setup()

# Now safely import other components
from chat import routing

# Get ASGI application after setup
django_asgi_app = get_asgi_application()

# Production optimizations
def get_websocket_application():
    """Separate WSGI/ASGI apps for better middleware handling"""
    return AuthMiddlewareStack(
        AllowedHostsOriginValidator(
            URLRouter(
                routing.websocket_urlpatterns
            )
        )
    )

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": get_websocket_application(),
})