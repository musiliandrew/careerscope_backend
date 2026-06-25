from django.urls import path
from .views import InterestsListView, TrackInterestView, ConvertInterestView, ConversionRemindersView

urlpatterns = [
    # List
    path('', InterestsListView.as_view(), name='interests-list'),
    # Actions (support both with and without trailing slash)
    path('track', TrackInterestView.as_view(), name='interests-track'),
    path('track/', TrackInterestView.as_view(), name='interests-track-slash'),
    path('convert', ConvertInterestView.as_view(), name='interests-convert'),
    path('convert/', ConvertInterestView.as_view(), name='interests-convert-slash'),
    path('reminders', ConversionRemindersView.as_view(), name='interests-reminders'),
    path('reminders/', ConversionRemindersView.as_view(), name='interests-reminders-slash'),
]
