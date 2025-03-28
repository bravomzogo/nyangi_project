import os
import django
from django.core.asgi import get_asgi_application

# Set the default Django settings module FIRST
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ChatApp.settings')

# Initialize Django BEFORE importing dependencies that require models
django.setup()  # This populates the app registry

# Now it's safe to import other components
from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from chat import routing  # This import now happens after Django setup

# Get ASGI application after setup
django_asgi_app = get_asgi_application()

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AuthMiddlewareStack(
        URLRouter(
            routing.websocket_urlpatterns
        )
    ),
})