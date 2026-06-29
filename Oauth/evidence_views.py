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
        metadata={'status': 'pending_ingestion'}
    )
    
    # TODO: Trigger Celery task for the `data-ingestion-system` to crawl the URL,
    # extract the content, and trigger the `ai-enrichment-system` event.
    
    return Response({
        'message': 'Evidence submitted successfully. Ingestion pipeline started.',
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
