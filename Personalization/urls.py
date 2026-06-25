from django.urls import path
from .views import recommended_jobs, learning_recommendations, calculate_matches_webhook

urlpatterns = [
    path("recommended/", recommended_jobs, name="recommended_jobs"),
    path("learning/", learning_recommendations, name="learning_recommendations"),
    path("webhooks/calculate_matches/", calculate_matches_webhook, name="calculate_matches_webhook"),
]
