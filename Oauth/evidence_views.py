from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Profile, EvidenceNode

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def submit_evidence_url(request):
    """
    Accepts a public URL (GitHub, Portfolio, Blog, etc.) as evidence.
    Creates an EvidenceNode and queues it for the Data Ingestion pipeline.
    """
    user = request.user
    url = request.data.get('url')
    source = request.data.get('source', 'user_submission')
    node_type = request.data.get('node_type', 'url')
    
    if not url:
        return Response({'error': 'URL is required.'}, status=status.HTTP_400_BAD_REQUEST)
        
    try:
        profile = Profile.objects.get(user=user)
    except Profile.DoesNotExist:
        return Response({'error': 'Profile not found.'}, status=status.HTTP_404_NOT_FOUND)
        
    # Create the raw EvidenceNode
    evidence_node = EvidenceNode.objects.create(
        profile=profile,
        url=url,
        source=source,
        node_type=node_type,
        metadata={'status': 'completed'}
    )
    
    try:
        from Personalization.utils import notify_personalization_service
        notify_personalization_service("evidence_added", "EvidenceNode", evidence_node.id)
    except Exception as notify_err:
        print(f"Personalization notification warning: {notify_err}")
    
    # Auto-extract skills from submitted link (GitHub or Web Portfolio)
    try:
        import requests
        from .models import UserSkills
        
        if "github.com/" in url.lower():
            parts = url.rstrip('/').split('github.com/')[-1].split('/')
            if len(parts) >= 1 and parts[0]:
                owner = parts[0]
                user_gh_link = f"https://github.com/{owner}/"
                profile.github_url = user_gh_link
                profile.save(update_fields=["github_url"])
                print(f"Auto-prefilled profile.github_url = {user_gh_link}")

            if len(parts) >= 2:
                owner, repo = parts[0], parts[1]
                lang_url = f"https://api.github.com/repos/{owner}/{repo}/languages"
                resp = requests.get(lang_url, timeout=5, headers={"User-Agent": "CareerScoper-Bot/1.0"})
                if resp.ok:
                    languages = list(resp.json().keys())
                    for lang in languages:
                        UserSkills.objects.get_or_create(
                            profile=profile,
                            skill_name=lang,
                            defaults={"verification_source": f"GitHub Repository ({repo})"}
                        )
        else:
            # Scrape web portfolio/site for tech keywords
            try:
                resp = requests.get(url, timeout=5, headers={"User-Agent": "CareerScoper-Bot/1.0"})
                if resp.ok:
                    page_text = resp.text.lower()
                    tech_keywords = [
                        "React", "Next.js", "Vue", "Angular", "TypeScript", "JavaScript",
                        "Node.js", "Python", "Django", "FastAPI", "Tailwind CSS", "Bootstrap",
                        "Docker", "AWS", "PostgreSQL", "MongoDB", "GraphQL", "REST API", "Vercel"
                    ]
                    for tech in tech_keywords:
                        if tech.lower() in page_text:
                            UserSkills.objects.get_or_create(
                                profile=profile,
                                skill_name=tech,
                                defaults={"verification_source": f"Portfolio Website ({url})"}
                            )
            except Exception as web_err:
                print(f"Web portfolio scrape warning: {web_err}")

    except Exception as scan_err:
        print(f"Evidence link extraction error: {scan_err}")

    return Response({
        'message': 'Evidence submitted successfully. Skills extracted and added to user memory.',
        'evidence_id': str(evidence_node.id)
    }, status=status.HTTP_202_ACCEPTED)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_evidence_nodes(request):
    """
    Returns all evidence nodes for the user's Evidence Graph.
    """
    user = request.user
    try:
        profile = Profile.objects.get(user=user)
    except Profile.DoesNotExist:
        return Response({'error': 'Profile not found.'}, status=status.HTTP_404_NOT_FOUND)
        
    nodes = EvidenceNode.objects.filter(profile=profile).values(
        'id', 'node_type', 'source', 'url', 'title', 'metadata', 'created_at'
    )
    
    return Response({'evidence_nodes': list(nodes)})
