from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .models import Profile, WorkExperience, EducationBackground
from .serializers import WorkExperienceSerializer, EducationSerializer
from Personalization.utils import notify_personalization_service

# ==========================================
# WORK EXPERIENCE ENDPOINTS
# ==========================================

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def manage_experience(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)
    
    if request.method == 'GET':
        experiences = WorkExperience.objects.filter(profile=profile).order_by('-start_date')
        serializer = WorkExperienceSerializer(experiences, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
        
    elif request.method == 'POST':
        # Add profile to data
        data = request.data.copy()
        data['profile'] = profile.id
        serializer = WorkExperienceSerializer(data=data)
        
        if serializer.is_valid():
            exp = serializer.save()
            notify_personalization_service("profile_updated", "Profile", profile.id)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def experience_detail(request, exp_id):
    profile, _ = Profile.objects.get_or_create(user=request.user)
    
    try:
        exp = WorkExperience.objects.get(id=exp_id, profile=profile)
    except WorkExperience.DoesNotExist:
        return Response({"error": "Experience not found"}, status=status.HTTP_404_NOT_FOUND)
        
    if request.method == 'PATCH':
        serializer = WorkExperienceSerializer(exp, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            notify_personalization_service("profile_updated", "Profile", profile.id)
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
    elif request.method == 'DELETE':
        exp.delete()
        notify_personalization_service("profile_updated", "Profile", profile.id)
        return Response({"message": "Experience deleted successfully"}, status=status.HTTP_200_OK)


# ==========================================
# EDUCATION ENDPOINTS
# ==========================================

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def manage_education(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)
    
    if request.method == 'GET':
        education = EducationBackground.objects.filter(profile=profile).order_by('-joined')
        serializer = EducationSerializer(education, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
        
    elif request.method == 'POST':
        data = request.data.copy()
        data['profile'] = profile.id
        serializer = EducationSerializer(data=data)
        
        if serializer.is_valid():
            edu = serializer.save()
            notify_personalization_service("profile_updated", "Profile", profile.id)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def education_detail(request, edu_id):
    profile, _ = Profile.objects.get_or_create(user=request.user)
    
    try:
        edu = EducationBackground.objects.get(id=edu_id, profile=profile)
    except EducationBackground.DoesNotExist:
        return Response({"error": "Education not found"}, status=status.HTTP_404_NOT_FOUND)
        
    if request.method == 'PATCH':
        serializer = EducationSerializer(edu, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            notify_personalization_service("profile_updated", "Profile", profile.id)
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
    elif request.method == 'DELETE':
        edu.delete()
        notify_personalization_service("profile_updated", "Profile", profile.id)
        return Response({"message": "Education deleted successfully"}, status=status.HTTP_200_OK)
