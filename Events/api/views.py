from rest_framework import generics
from rest_framework.permissions import AllowAny
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q
from django.utils import timezone

from Events.models import Event
from .serializers import EventSerializer


class Pagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class EventsListView(generics.ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = EventSerializer
    pagination_class = Pagination

    def get_queryset(self):
        qs = Event.objects.all().order_by('-start_date')
        q = self.request.query_params.get('search')
        etype = self.request.query_params.get('type')  # hackathon, conference, etc.
        location = self.request.query_params.get('location')
        category = self.request.query_params.get('category')
        status = self.request.query_params.get('status')
        if q:
            qs = qs.filter(Q(title__icontains=q) | Q(description__icontains=q) | Q(tags__icontains=q))
        if etype:
            qs = qs.filter(event_type__iexact=etype)
        if location:
            qs = qs.filter(location__icontains=location)
        if category:
            qs = qs.filter(category__iexact=category)
        if status:
            qs = qs.filter(status__iexact=status)
        return qs

    def list(self, request, *args, **kwargs):
        """
        Extend the default ListAPIView response to add metadata expected by the frontend.
        - If paginated, keep DRF envelope {count,next,previous,results} and append sources/totalFetched/timestamp/filters.
        - If not paginated, wrap into a custom object with events and metadata.
        """
        response = super().list(request, *args, **kwargs)
        data = response.data
        meta_sources = []  # Populate with real source stats if available
        meta_filters = request.query_params.dict()
        meta_timestamp = timezone.now().isoformat()

        if isinstance(data, dict) and 'results' in data:
            # Paginated shape — append metadata
            results = data.get('results') or []
            data['sources'] = meta_sources
            data['totalFetched'] = len(results)
            data['timestamp'] = meta_timestamp
            data['filters'] = meta_filters
            response.data = data
        else:
            # Non-paginated shape — wrap in custom object
            events_list = data if isinstance(data, list) else []
            response.data = {
                'events': events_list,
                'total': len(events_list),
                'totalFetched': len(events_list),
                'sources': meta_sources,
                'filters': meta_filters,
                'timestamp': meta_timestamp,
            }
        return response
