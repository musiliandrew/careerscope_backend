"""
Skills management API endpoints
Allows users to add, update, and delete technical skills, soft skills, and learning goals
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction
from .models import Profile, UserSkills
from .serializers import SkillSerializer
from Personalization.utils import notify_personalization_service


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_skills(request):
    """
    Get all skills for the authenticated user
    Returns: {
        "technicalSkills": [...],
        "softSkills": [...],
        "wantToLearn": [...]
    }
    """
    profile, _ = Profile.objects.get_or_create(user=request.user)
    
    # Technical skills (not want_to_learn and not soft skills)
    technical_skills = profile.skills.filter(
        want_to_learn=False
    ).exclude(
        skill_category__iexact='soft'
    ).values(
        'id', 'skill_name', 'skill_category', 
        'proficiency_level', 'years_of_experience'
    )
    
    # Soft skills
    soft_skills = profile.skills.filter(
        skill_category__iexact='soft',
        want_to_learn=False
    ).values('id', 'skill_name')
    
    # Want to learn
    want_to_learn = profile.skills.filter(
        want_to_learn=True
    ).values('id', 'skill_name', 'skill_category')
    
    return Response({
        "technicalSkills": [
            {
                "id": str(skill['id']),
                "name": skill['skill_name'],
                "category": skill['skill_category'] or 'General',
                "level": int(skill['proficiency_level']) if skill['proficiency_level'] and str(skill['proficiency_level']).isdigit() else 3,
                "yearsExp": float(skill['years_of_experience']) if skill['years_of_experience'] else 0
            }
            for skill in technical_skills
        ],
        "softSkills": [skill['skill_name'] for skill in soft_skills],
        "wantToLearn": [skill['skill_name'] for skill in want_to_learn]
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_technical_skill(request):
    """
    Add a new technical skill
    Body: {
        "name": "Python",
        "category": "Programming Language",
        "level": 4,  // 1-5 stars
        "yearsExp": 3
    }
    """
    profile, _ = Profile.objects.get_or_create(user=request.user)
    
    skill_name = request.data.get('name', '').strip()
    if not skill_name:
        return Response(
            {"error": "Skill name is required"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Check if skill already exists
    existing = UserSkills.objects.filter(
        profile=profile, 
        skill_name__iexact=skill_name
    ).first()
    
    if existing:
        # If it was a learning goal, graduate it to a technical skill
        if existing.want_to_learn:
            existing.want_to_learn = False
            existing.skill_category = request.data.get('category', existing.skill_category)
            existing.proficiency_level = str(request.data.get('level', 3))
            existing.years_of_experience = request.data.get('yearsExp', 0)
            existing.save()
            notify_personalization_service("skill_updated", "UserSkills", existing.id)
            return Response({
                "id": str(existing.id),
                "name": existing.skill_name,
                "category": existing.skill_category,
                "level": int(existing.proficiency_level),
                "yearsExp": float(existing.years_of_experience),
                "info": "Graduated from learning goal"
            }, status=status.HTTP_200_OK)
        
        return Response(
            {"error": f"Skill '{skill_name}' already exists in your technical skills"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    skill = UserSkills.objects.create(
        profile=profile,
        skill_name=skill_name,
        skill_category=request.data.get('category', 'General'),
        proficiency_level=str(request.data.get('level', 3)),
        years_of_experience=request.data.get('yearsExp', 0),
        want_to_learn=False
    )
    notify_personalization_service("skill_updated", "UserSkills", skill.id)
    
    return Response({
        "id": str(skill.id),
        "name": skill.skill_name,
        "category": skill.skill_category,
        "level": int(skill.proficiency_level),
        "yearsExp": float(skill.years_of_experience) if skill.years_of_experience else 0
    }, status=status.HTTP_201_CREATED)


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def update_technical_skill(request, skill_id):
    """
    Update a technical skill's proficiency level or years of experience
    Body: {
        "level": 5,
        "yearsExp": 4
    }
    """
    profile, _ = Profile.objects.get_or_create(user=request.user)
    
    try:
        skill = UserSkills.objects.get(id=skill_id, profile=profile)
    except UserSkills.DoesNotExist:
        return Response(
            {"error": "Skill not found"},
            status=status.HTTP_404_NOT_FOUND
        )
    
    if 'level' in request.data:
        level = request.data['level']
        if level < 1 or level > 5:
            return Response(
                {"error": "Level must be between 1 and 5"},
                status=status.HTTP_400_BAD_REQUEST
            )
        skill.proficiency_level = str(level)
    
    if 'yearsExp' in request.data:
        skill.years_of_experience = request.data['yearsExp']
    
    if 'category' in request.data:
        skill.skill_category = request.data['category']
    
    skill.save()
    notify_personalization_service("skill_updated", "UserSkills", skill.id)
    
    return Response({
        "id": str(skill.id),
        "name": skill.skill_name,
        "category": skill.skill_category,
        "level": int(skill.proficiency_level),
        "yearsExp": float(skill.years_of_experience) if skill.years_of_experience else 0
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_soft_skill(request):
    """
    Add a soft skill
    Body: {
        "name": "Communication"
    }
    """
    profile, _ = Profile.objects.get_or_create(user=request.user)
    
    skill_name = request.data.get('name', '').strip()
    if not skill_name:
        return Response(
            {"error": "Skill name is required"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Check if skill already exists
    existing = UserSkills.objects.filter(
        profile=profile,
        skill_name__iexact=skill_name
    ).first()
    
    if existing:
        return Response(
            {"error": f"Skill '{skill_name}' already exists in your profile"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    skill = UserSkills.objects.create(
        profile=profile,
        skill_name=skill_name,
        skill_category='soft',
        want_to_learn=False
    )
    notify_personalization_service("skill_updated", "UserSkills", skill.id)
    
    return Response({
        "id": str(skill.id),
        "name": skill.skill_name
    }, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_learning_goal(request):
    """
    Add a skill to the "want to learn" list
    Body: {
        "name": "Rust",
        "category": "Programming Language"  // optional
    }
    """
    profile, _ = Profile.objects.get_or_create(user=request.user)
    
    skill_name = request.data.get('name', '').strip()
    if not skill_name:
        return Response(
            {"error": "Skill name is required"},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Check if already exists (as any skill type)
    existing = UserSkills.objects.filter(
        profile=profile,
        skill_name__iexact=skill_name
    ).first()
    
    if existing:
        msg = f"'{skill_name}' is already in your "
        msg += "learning list" if existing.want_to_learn else "skills list"
        return Response(
            {"error": msg},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    skill = UserSkills.objects.create(
        profile=profile,
        skill_name=skill_name,
        skill_category=request.data.get('category', 'General'),
        want_to_learn=True
    )
    notify_personalization_service("skill_updated", "UserSkills", skill.id)
    
    return Response({
        "id": str(skill.id),
        "name": skill.skill_name
    }, status=status.HTTP_201_CREATED)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_skill(request, skill_id):
    """
    Delete any skill (technical, soft, or learning goal)
    """
    profile, _ = Profile.objects.get_or_create(user=request.user)
    
    try:
        skill = UserSkills.objects.get(id=skill_id, profile=profile)
        skill_name = skill.skill_name
        notify_personalization_service("skill_deleted", "UserSkills", skill.id)
        skill.delete()
        
        return Response({
            "message": f"Skill '{skill_name}' deleted successfully"
        }, status=status.HTTP_200_OK)
    except UserSkills.DoesNotExist:
        return Response(
            {"error": "Skill not found"},
            status=status.HTTP_404_NOT_FOUND
        )
