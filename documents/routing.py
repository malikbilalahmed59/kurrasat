# documents/routing.py
from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/documents/analyze/(?P<doc_id>\w+)/$', consumers.DocumentAnalysisConsumer.as_asgi()),
]