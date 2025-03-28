import os
from django.core.asgi import get_asgi_application
from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from chat import routing

# Set the default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ChatApp.settings')

# Initialize Django ASGI application early to ensure AppRegistry is populated
django_asgi_app = get_asgi_application()

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AuthMiddlewareStack(
        URLRouter(
            routing.websocket_urlpatterns
        )
    ),
})