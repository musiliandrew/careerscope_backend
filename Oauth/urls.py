from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import *
from .skills_views import (
    get_user_skills,
    add_technical_skill,
    update_technical_skill,
    add_soft_skill,
    add_learning_goal,
    delete_skill,
)


urlpatterns = [
    path("register/", register_user, name="registration"),
    path("login/", login_user, name="login"),
    path("logout/", logout_user, name="logout"),
    # Cookie-based refresh (preferred)
    path("token/refresh/", token_refresh_cookie, name="refresh_token_cookie"),
    # Legacy body-based refresh (kept for compatibility)
    path("token/refresh", TokenRefreshView.as_view(), name="refresh_token"),
    path("github/login/", github_login, name="github_login"),
    path("callback/github/", github_callback, name="github_callback"),
    path("google/login/", google_login, name="google_login"),
    path("callback/google/", google_callback, name="google_callback"),
    #     PROFILE ENDPOINTS
    path("profile/<int:step>/", update_profile, name="profile_update"),
    path("profile/me/", get_profile, name="my_profile"),
    path("profile/avatar/", upload_avatar, name="avatar_upload"),
    path("profile/cv_upload/", upload_cv, name="cv_upload"),
    path("profile/card/summary/", career_card_summary, name="career_card_summary"),
    #     SKILLS ENDPOINTS
    path("skills/", get_user_skills, name="get_skills"),
    path("skills/technical/", add_technical_skill, name="add_technical_skill"),
    path("skills/technical/<uuid:skill_id>/", update_technical_skill, name="update_technical_skill"),
    path("skills/soft/", add_soft_skill, name="add_soft_skill"),
    path("skills/learning/", add_learning_goal, name="add_learning_goal"),
    path("skills/<uuid:skill_id>/", delete_skill, name="delete_skill"),
    path("integrations/<str:integration_type>/toggle/", toggle_integration, name="toggle_integration"),
]
