from django.shortcuts import render, redirect
from rest_framework.decorators import api_view, permission_classes
from rest_framework.request import Request
from rest_framework.response import Response
from .serializers import *
from rest_framework import status
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from django.contrib.auth import authenticate
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
import os
import secrets
import requests
from django.contrib.auth import get_user_model
from urllib.parse import urlencode
from django.conf import settings
import logging
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.utils import timezone
from agents.AIService.GeminiAI import ResumeExtractionAgent
from agents.AIService import AIManager
from agents.AIService.OpenRouterAI import generate_career_card_summary
from agents.DocReader import read_resume
from agents.models import Profile as p
from .models import Profile, UserSkills, EducationBackground, WorkExperience, Project, JobPreferences, CareerGoals
from .backblaze import blaze_client
from Personalization.utils import notify_personalization_service

User = get_user_model()

# === CONFIG ===
GITHUB_CLIENT_ID = os.getenv("GITHUB_ID")
GITHUB_CLIENT_SECRET = os.getenv("GITHUB_SECRET")
GITHUB_REDIRECT_URI = os.getenv("GITHUB_REDIRECT_URI")

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI")

FRONTEND_URL = os.getenv("FRONTEND_URL")  # Vite default
CALLBACK_PATH = "/oauth/callback"

resume_agent = ResumeExtractionAgent(open_router=True)
logger = logging.getLogger(__name__)


def _username_from_email(email: str) -> str:
    return str(email).split("@")[0]


def _unique_username(base_username: str) -> str:
    username = base_username or "user"
    candidate = username
    suffix = 1
    while User.objects.filter(username=candidate).exists():
        candidate = f"{username}{suffix}"
        suffix += 1
    return candidate


def _get_or_create_user_by_email(email: str, fallback_username: str, full_name: str = ""):
    user = User.objects.filter(email__iexact=email).first()
    if user:
        return user, False

    username = _unique_username(fallback_username or _username_from_email(email))
    user = User.objects.create_user(username=username, email=email)
    if full_name:
        parts = full_name.split(" ", 1)
        user.first_name = parts[0]
        user.last_name = parts[1] if len(parts) > 1 else ""
        user.save(update_fields=["first_name", "last_name"])
    return user, True


@api_view(["POST"])
def register_user(request):
    serialized = RegSerializer(data=request.data)
    if serialized.is_valid():
        user = User.objects.create_user(
            username=serialized.data["username"],
            email=serialized.data["email"],
            password=serialized.data["password"],
        )
        tokens = RefreshToken.for_user(user=user)
        return Response(
            {
                "info": "User Created",
                "access": str(tokens.access_token),
                "refresh": str(tokens),
            },
            status=status.HTTP_201_CREATED,
        )
    else:
        return Response(
            {"info": "The data is not valid", "errors": serialized.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )


# An endpoint to exchange tokens with Social Auth for the user
@api_view(["POST"])
def exchange_tokens(request: Request):
    data = ExchangeSerializer(data=request.data)
    if data.is_valid():
        email = data.data["email"]
        username = data.data["username"]
        if not username:
            username = str(email).split("@")[0]
        user, created = _get_or_create_user_by_email(email, username)
        Profile.objects.update_or_create(
            user=user,
            defaults={"last_login_at": timezone.now()},
        )
        token = RefreshToken.for_user(user)
        return Response(
            {
                "info": "User Authenticated",
                "access": str(token.access_token),
                "refresh": str(token),
            },
            status=status.HTTP_200_OK,
        )
    else:
        return Response(
            {"info": "Invalid data format", "errors": data.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )


def _set_refresh_cookie(response, refresh_token: str):
    # 30 days
    max_age = 30 * 24 * 60 * 60
    # In dev, secure can be False (http). In prod, set Secure=True.
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        max_age=max_age,
        httponly=True,
        samesite="Lax",
        secure=False,
        path="/api/auth/",
    )
    return response


@api_view(["POST"])
def login_user(request: Request):
    serialized = LoginSerializer(data=request.data)
    if serialized.is_valid():
        user = authenticate(
            request=request,
            username=serialized.data["username"],
            password=serialized.data["password"],
        )
        if user is None:
            return Response(
                {"info": "User not found"}, status=status.HTTP_404_NOT_FOUND
            )

        token = RefreshToken().for_user(user)
        resp = Response(
            {
                "info": "User Logged In",
                "access": str(token.access_token),
                "refresh": str(token),
            }
        )
        _set_refresh_cookie(resp, str(token))
        return resp
    else:
        return Response(
            {"info": "Invalid data", "error": serialized.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )


@api_view(["POST"])
def logout_user(request: Request):
    try:
        refresh_token = request.data.get("refresh_token")
        token = RefreshToken(refresh_token)
        token.blacklist()
        return Response(
            {
                "info": "User Logged Out Successfully"
            },
            status=status.HTTP_200_OK
        )
    except Exception:
        return Response(
            {
                "info": "An error Occured",
            },
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(["GET"])
def github_login(request: Request):
    """
    Returns a GitHub authorization URL. Frontend should redirect the user to that URL.
    """
    if not GITHUB_CLIENT_ID:
        return Response(
            {"detail": "GITHUB_ID not configured"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    redirect_uri = GITHUB_REDIRECT_URI or request.build_absolute_uri(
        "/auth/github/callback/"
    )
    state = secrets.token_urlsafe(16)
    # optional: store state in session to verify it in callback
    request.session["github_oauth_state"] = state

    params = {
        "client_id": GITHUB_CLIENT_ID,
        "redirect_uri": redirect_uri,
        "scope": "user:email",
        "state": state,
        "allow_signup": "true",
    }
    auth_url = "https://github.com/login/oauth/authorize?" + "&".join(
        f"{k}={requests.utils.requote_uri(str(v))}" for k, v in params.items()
    )

    return Response({"auth_url": auth_url})


@api_view(["GET"])
def github_callback(request: Request):
    code = request.query_params.get("code")
    state = request.query_params.get("state")

    if not code:
        return redirect(f"{FRONTEND_URL}{CALLBACK_PATH}?error=missing_code")

    # Exchange code for token
    token_resp = requests.post(
        "https://github.com/login/oauth/access_token",
        headers={"Accept": "application/json"},
        data={
            "client_id": GITHUB_CLIENT_ID,
            "client_secret": GITHUB_CLIENT_SECRET,
            "code": code,
            "redirect_uri": GITHUB_REDIRECT_URI
                            or request.build_absolute_uri("/auth/github/callback/"),
        },
        timeout=10,
    )
    token_data = token_resp.json()
    access_token = token_data.get("access_token")
    if not access_token:
        return redirect(f"{FRONTEND_URL}{CALLBACK_PATH}?error=token_failed")

    # Get user
    user_resp = requests.get(
        "https://api.github.com/user",
        headers={"Authorization": f"token {access_token}"},
        timeout=10,
    )
    user_json = user_resp.json()
    email = user_json.get("email")

    if not email:
        emails_resp = requests.get(
            "https://api.github.com/user/emails",
            headers={"Authorization": f"token {access_token}"},
            timeout=10,
        )
        emails = emails_resp.json()
        primary = next(
            (e for e in emails if e.get("primary") and e.get("verified")), None
        )
        email = primary.get("email") if primary else None

    base_username = user_json.get("login") or (
        email.split("@")[0] if email else "github_user"
    )
    username = base_username

    if not email:
        return redirect(f"{FRONTEND_URL}{CALLBACK_PATH}?error=email_missing")

    user, created = _get_or_create_user_by_email(email, username)
    Profile.objects.update_or_create(
        user=user,
        defaults={
            "github_id": str(user_json.get("id") or ""),
            "email_verified": True,
            "last_login_at": timezone.now(),
        },
    )

    refresh = RefreshToken.for_user(user)
    access_token_jwt = str(refresh.access_token)
    refresh_token_jwt = str(refresh)

    # Redirect to frontend with tokens and set HttpOnly refresh cookie
    resp = redirect(f"{FRONTEND_URL}{CALLBACK_PATH}?access={access_token_jwt}")
    _set_refresh_cookie(resp, refresh_token_jwt)
    return resp


@api_view(["GET"])
def google_login(request: Request):
    """
    Return Google authorization URL (frontend should redirect user there).
    """
    if not GOOGLE_CLIENT_ID:
        return Response(
            {"detail": "GOOGLE_CLIENT_ID not configured"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    redirect_uri = GOOGLE_REDIRECT_URI or request.build_absolute_uri(
        "/auth/google/callback/"
    )
    state = secrets.token_urlsafe(16)
    request.session["google_oauth_state"] = state

    params = {
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
        "access_type": "offline",
        "prompt": "select_account",
    }
    auth_url = "https://accounts.google.com/o/oauth2/v2/auth?" + urlencode(params)
    return Response({"auth_url": auth_url})


@api_view(["GET"])
def google_callback(request: Request):
    code = request.GET.get("code")
    state = request.GET.get("state")
    # saved_state = request.session.get("google_oauth_state")

    if not code:
        return redirect(f"{FRONTEND_URL}{CALLBACK_PATH}?error=missing_code")
    # if saved_state and state != saved_state:
    #     return redirect(f"{FRONTEND_URL}{CALLBACK_PATH}?error=invalid_state")

    redirect_uri = GOOGLE_REDIRECT_URI or request.build_absolute_uri(
        "/auth/google/callback/"
    )
    token_resp = requests.post(
        "https://oauth2.googleapis.com/token",
        data={
            "code": code,
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code",
        },
        headers={"Accept": "application/json"},
        timeout=10,
    )
    token_data = token_resp.json()
    access_token = token_data.get("access_token")
    if not access_token:
        return redirect(f"{FRONTEND_URL}{CALLBACK_PATH}?error=token_failed")

    userinfo_resp = requests.get(
        "https://www.googleapis.com/oauth2/v2/userinfo",
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=10,
    )
    userinfo = userinfo_resp.json()
    email = userinfo.get("email")
    name = userinfo.get("name", email.split("@")[0] if email else "google_user")
    base_username = name.replace(" ", "_").lower()
    username = base_username

    if not email:
        return redirect(f"{FRONTEND_URL}{CALLBACK_PATH}?error=email_missing")

    user, created = _get_or_create_user_by_email(email, username, full_name=name)
    Profile.objects.update_or_create(
        user=user,
        defaults={
            "full_name": name,
            "google_id": str(userinfo.get("id") or ""),
            "email_verified": bool(userinfo.get("verified_email", True)),
            "last_login_at": timezone.now(),
        },
    )

    refresh = RefreshToken.for_user(user)
    access_token_jwt = str(refresh.access_token)
    refresh_token_jwt = str(refresh)
    resp = redirect(f"{FRONTEND_URL}{CALLBACK_PATH}?access={access_token_jwt}")
    _set_refresh_cookie(resp, refresh_token_jwt)
    return resp


@api_view(["POST"])
def token_refresh_cookie(request: Request):
    """Refresh access token using HttpOnly refresh cookie."""
    refresh_token = request.COOKIES.get("refresh_token")
    if not refresh_token:
        return Response({"detail": "No refresh cookie"}, status=status.HTTP_401_UNAUTHORIZED)
    serializer = TokenRefreshSerializer(data={"refresh": refresh_token})
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data
    # Optionally re-set cookie to maintain sliding session (same token)
    resp = Response({"access": data.get("access")}, status=status.HTTP_200_OK)
    _set_refresh_cookie(resp, refresh_token)
    return resp


# ==========================================
# PROFILE CREATION AND UPDATE ENDPOINTS
# ==========================================

steps = {
    1: ProfileSerializer1,
    2: EducationSerializer,
    3: SkillSerializer,
    4: PreferenceSerializer,
    5: CareerGoalSerializer,
}


@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def update_profile(request: Request, step: int) -> Response:
    """
    The step value determines the serializer to be used for the call based on the
    steps dictionary

    """
    profile, created = Profile.objects.get_or_create(user=request.user)
    print(f"DEBUG: update_profile step={step} user={request.user.email}")
    try:
        if step == 4:
            print(f"DEBUG: Step 4 (Preferences). Data: {request.data}")
            prefs = JobPreferences.objects.filter(profile=profile).first()
            if not prefs:
                print("DEBUG: Creating new JobPreferences object")
                prefs = JobPreferences.objects.create(profile=profile)
            serializer = steps[step](instance=prefs, data=request.data, partial=True)
        elif step == 5:
            print(f"DEBUG: Step 5 (Goals). Data: {request.data}")
            goals = CareerGoals.objects.filter(profile=profile).first()
            if not goals:
                print("DEBUG: Creating new CareerGoals object")
                goals = CareerGoals.objects.create(profile=profile)
            serializer = steps[step](instance=goals, data=request.data, partial=True)
        else:
            serializer = steps[step](instance=profile, data=request.data, partial=True)
    except KeyError:
        return Response({"info": "Step unknown"}, status=status.HTTP_404_NOT_FOUND)

    if not serializer.is_valid():
        print(f"DEBUG: Serializer Invalid: {serializer.errors}")
        return Response({"info": "Invalid Format", "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    with transaction.atomic():
        saved_obj = serializer.save()
        if step == 1:
            notify_personalization_service("profile_updated", "Profile", profile.id)
        elif step == 4:
            notify_personalization_service("preferences_updated", "JobPreferences", saved_obj.id)
        elif step == 5:
            notify_personalization_service("goals_updated", "CareerGoals", saved_obj.id)
        print("DEBUG: Saved serializer successfully")
        # TODO: Update the progress

    return Response({"info": "Profile Updated"}, status=status.HTTP_200_OK)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_profile(request: Request):
    profile, created = Profile.objects.get_or_create(user=request.user)
    response = (
        {"info": "Profile Just created, Please Update"}
        if created
        else FullProfileSerializer(profile).data
    )
    return Response(response, status=status.HTTP_200_OK)


# Avatar Upload Endpoint


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def upload_avatar(request: Request):
    file_obj = request.FILES.get("avatar")
    if not file_obj:
        return Response(
            {"info": "File not received, Try Again"}, status=status.HTTP_400_BAD_REQUEST
        )

    # Upload file to backblaze
    avatar_id = blaze_client.upload_file(file=file_obj, path=f"avatars/{file_obj.name}")
    profile = Profile.objects.get(user=request.user)
    profile.avatar_id = avatar_id
    profile.save(update_fields=["avatar_id"])
    return Response(
        {
            "info": "avatar Updated",
            "avatar_id": avatar_id,
            "avatar_url": blaze_client.get_url(avatar_id) if avatar_id else "",
        },
        status=status.HTTP_201_CREATED,
    )


from markitdown import MarkItDown

md = MarkItDown()


# CV Upload endpoint
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def upload_cv(request: Request):
    """
    The Request should Contain a query param save; This determines
    whether the cv is scanned and information returned to the user for validation
    or the request data is serialized and saved to update the user profile

    """
    save_param = request.query_params.get("save", "false")
    save = str(save_param).lower() in ("true", "1", "yes")
    
    if not save:
        # EXTRACTION MODE: Upload CV and return AI-extracted data
        resume: InMemoryUploadedFile = request.FILES.get("cv")
        if not resume:
            return Response(
                {
                    "info": "Upload resume First",
                    "detail": "Expected a file field named 'cv' in multipart/form-data.",
                    "received_keys": list(getattr(request.FILES, "keys", lambda: [])()),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Basic validation: non-empty file
        try:
            size = getattr(resume, "size", None)
            if size is not None and int(size) <= 0:
                return Response({"info": "Uploaded file is empty"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception:
            pass

        # Upload to storage with clear diagnostics
        try:
            cv_id = blaze_client.upload_file(file=resume, path=f"cv/{resume.name}")
            user_profile = Profile.objects.get(user=request.user)
            user_profile.resume_url = blaze_client.get_url(cv_id) if cv_id else None
            user_profile.save(update_fields=["resume_url"])
        except Exception as e:
            print(f"Storage Upload Error: {e}")
            return Response(
                {
                    "info": "Upload to storage failed",
                    "detail": str(e)[:500],
                    "hint": "Ensure BACKBLAZE_KEYID, BACKBLAZE_APPLICATIONKEY, and BUCKET are set and valid.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            # Save to temp file to ensure markitdown detects extension correctly
            import tempfile
            import shutil
            
            suffix = os.path.splitext(resume.name)[1]
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                for chunk in resume.chunks():
                    tmp.write(chunk)
                tmp_path = tmp.name
                
            print(f" Saved temp file to: {tmp_path}")
            
            try:
                # Convert using file path
                markup_result = md.convert(tmp_path)
                markdown_text = markup_result.text_content if hasattr(markup_result, 'text_content') else str(markup_result)
            finally:
                # Cleanup
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)
                    
            print(f"--- EXTRACTED MARKDOWN PREVIEW ---\n{markdown_text[:500]}\n----------------------------------")
            
            if not markdown_text or len(markdown_text.strip()) < 50:
                print("WARNING: Extracted text is very short/empty! Is markitdown[pdf] installed/working?")
        
            response: p = resume_agent(markdown=markdown_text)
            print(f"AI RESPONSE: {response}")
            return Response(
                response.model_dump_json(),
                status=status.HTTP_200_OK
            )
        except Exception as e:
            print(f"Extraction processing error: {e}")
            import traceback
            traceback.print_exc()
            return Response({"info": "Extraction failed", "detail": str(e)}, status=500)

    else:
        # SAVE MODE: Save extracted data to database
        print(f"DEBUG: Save Mode Triggered. Data keys: {request.data.keys()}")
        profile, _ = Profile.objects.get_or_create(user=request.user)
        data = request.data
        
        # Save validation results / extraction to resume_data field
        profile.resume_data = data
        profile.save(update_fields=["resume_data"])
        
        # Auto-populate WorkExperience
        experiences = data.get("experiences", [])
        exp_added = 0
        if experiences and isinstance(experiences, list):
            for exp in experiences:
                # Basic check to avoid duplicates by title/company
                title = exp.get("role") or exp.get("title") or ""
                company = exp.get("company", "")
                if title and company:
                    _, created = WorkExperience.objects.get_or_create(
                        profile=profile,
                        title=title[:100],
                        company=company[:100],
                        defaults={
                            "description": exp.get("description", ""),
                            "location": exp.get("location", "")[:100]
                        }
                    )
                    if created:
                        exp_added += 1

        # Auto-populate EducationBackground
        education_list = data.get("education_background", [])
        edu_added = 0
        if education_list and isinstance(education_list, list):
            for edu in education_list:
                degree = edu.get("degree") or edu.get("certification") or ""
                institution = edu.get("institution", "")
                if degree and institution:
                    _, created = EducationBackground.objects.get_or_create(
                        profile=profile,
                        certification=degree[:50],
                        institution=institution[:100],
                        defaults={
                            "field_of_learning": edu.get("field", "")[:100]
                        }
                    )
                    if created:
                        edu_added += 1
                        
        print(f"DEBUG: Saved extracted data. Added {exp_added} jobs, {edu_added} degrees.")

        return Response({
            "info": "Profile Updated Successfully",
            "details": {
                "profile": "No changes (Manual mode)",
                "skills_added": 0,
                "education_added": edu_added,
                "experience_added": exp_added,
                "resume_data_saved": True
            }
        }, status=status.HTTP_200_OK)


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def career_card_summary(request: Request):
    """
    Returns the overall trajectory and intelligence snapshot from the Decision Engine SDK.
    Replaces legacy OpenRouter call.
    """
    profile = Profile.objects.get(user=request.user)
    pref = profile.preferences.first()
    target_role = pref.target_role if pref and pref.target_role else getattr(profile, "target_role", "Software Engineer")
    if not target_role:
        target_role = "Software Engineer"
        
    # Extract skills
    skills_qs = list(profile.skills.all().values_list("skill_name", flat=True))
    if not skills_qs and profile.resume_data and profile.resume_data.get("extractedData", {}).get("skills"):
        skills_qs = profile.resume_data["extractedData"]["skills"]
    if not skills_qs:
        skills_qs = ["Python", "JavaScript"]

    from shared.contracts.requests.evaluate_match import EvaluateMatchRequest, JobRequirementSnapshot
    from shared.contracts.responses.mission import IntelligenceSnapshot
    from shared.domain.capability import Capability
    from shared.sdk.decision_client import DecisionEngineClient
    from asgiref.sync import async_to_sync
    import os

    capabilities = [Capability(name=s, capability_score=85.0) for s in skills_qs]

    profile_snapshot = IntelligenceSnapshot(
        version=1,
        target_role=target_role,
        capabilities=capabilities
    )
    
    job_snapshot = JobRequirementSnapshot(
        title=target_role,
        company_name="Target Company",
        required_skills=["Python", "React", "Docker"],
        nice_to_have_skills=[],
        description="General requirements for " + target_role
    )
    
    eval_req = EvaluateMatchRequest(
        profile_snapshot=profile_snapshot,
        job_snapshot=job_snapshot,
        relevant_evidence=[]
    )
    
    client = DecisionEngineClient(base_url=os.getenv("DECISION_ENGINE_URL", "http://localhost:8000"))
    try:
        result = async_to_sync(client.evaluate_match)(eval_req)
        data = result.model_dump(mode="json")
    except Exception as e:
        print(f"Decision Engine SDK Error in career_card_summary: {e}")
        # Fallback to DecisionResult shape for UI safety
        data = {
            "overall_readiness": 72,
            "missing_capabilities": ["Docker"],
            "strengths": skills_qs,
            "updated_capabilities": [
                {"name": "Python", "verification_score": 96, "depth_score": 68, "freshness_score": 100, "capability_score": 88},
                {"name": "React", "verification_score": 85, "depth_score": 70, "freshness_score": 90, "capability_score": 82}
            ],
            "recommended_actions": [
                {"step": 1, "title": "Deploy ML service", "impact": "+11%", "status": "pending"}
            ],
            "explanations": [{"conclusion": "Strong match", "reasoning_trace": "High alignment", "confidence": 0.9}]
        }
        
    return Response(data, status=status.HTTP_200_OK)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def toggle_integration(request: Request, integration_type: str):
    """
    Toggle synchronization for a specific integration type
    """
    profile = Profile.objects.get(user=request.user)
    
    if integration_type == "email":
        profile.gmail_sync_enabled = not profile.gmail_sync_enabled
        profile.save(update_fields=["gmail_sync_enabled"])
    elif integration_type == "calendar":
        profile.calendar_sync_enabled = not profile.calendar_sync_enabled
        profile.save(update_fields=["calendar_sync_enabled"])
    else:
        return Response({"error": "Integration type not supported"}, status=status.HTTP_400_BAD_REQUEST)
        
    return Response({
        "status": "success", 
        "connected": profile.gmail_sync_enabled if integration_type == "email" else profile.calendar_sync_enabled
    })
