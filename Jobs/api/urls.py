from django.urls import path
from .views import JobsListView, JobAgentApplyView

urlpatterns = [
    path('', JobsListView.as_view(), name='jobs-list'),
    path('<uuid:pk>/agent-apply/', JobAgentApplyView.as_view(), name='job-agent-apply'),
]
