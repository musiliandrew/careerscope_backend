from django.urls import path
from .views import recommended_jobs, learning_recommendations, calculate_matches_webhook, mission_control_view, job_details_view

urlpatterns = [
    path("recommended/", recommended_jobs, name="recommended_jobs"),
    path("learning/", learning_recommendations, name="learning_recommendations"),
    path("webhooks/calculate_matches/", calculate_matches_webhook, name="calculate_matches_webhook"),
    path("mission-control/", mission_control_view, name="mission_control"),
    path("jobs/<uuid:job_id>/details/", job_details_view, name="job_details"),
]
