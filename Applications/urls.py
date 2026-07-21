from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ApplicationViewSet, PendingInterviewViewSet, status_insight_webhook, pubsub_event_webhook

router = DefaultRouter()
router.register(r'applications', ApplicationViewSet, basename='applications')
router.register(r'interviews', PendingInterviewViewSet, basename='interviews')

urlpatterns = [
    path('', include(router.urls)),
    path('webhooks/status_insight/', status_insight_webhook, name='status_insight_webhook'),
    path('webhooks/pubsub/', pubsub_event_webhook, name='pubsub_event_webhook'),
]
