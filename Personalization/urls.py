from django.urls import path
from .views import recommended_jobs, learning_recommendations

urlpatterns = [
    path("recommended/", recommended_jobs, name="recommended_jobs"),
    path("learning/", learning_recommendations, name="learning_recommendations"),
]
