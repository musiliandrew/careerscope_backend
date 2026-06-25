from django.contrib import admin
from django.urls import path, include


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/", include("Oauth.urls")),
    path("api/companies/", include("Companies.urls")),
    path("api/jobs/", include("Jobs.api.urls")),
    path("api/news/", include("News.api.urls")),
    path("api/events/", include("Events.api.urls")),
    path("api/interests/", include("Jobs.api.interests.urls")),
    path("api/applications/", include("Applications.urls")),
    path("api/personalization/", include("Personalization.urls")),
]
