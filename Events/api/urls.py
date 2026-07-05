from django.urls import path
from .views import EventsListView
from ..consumers import PubSubJobConsumerView, PubSubApplicationEventConsumerView

urlpatterns = [
    path('', EventsListView.as_view(), name='events-list'),
    path('webhooks/pubsub/jobs/', PubSubJobConsumerView.as_view(), name='pubsub_jobs_webhook'),
    path('webhooks/pubsub/applications/', PubSubApplicationEventConsumerView.as_view(), name='pubsub_applications_webhook'),
]
