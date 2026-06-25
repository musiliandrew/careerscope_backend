from rest_framework import generics
from rest_framework.permissions import AllowAny
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q

from News.models import NewsArticles
from .serializers import NewsArticleSerializer


class Pagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class NewsListView(generics.ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = NewsArticleSerializer
    pagination_class = Pagination

    def get_queryset(self):
        qs = NewsArticles.objects.all().order_by('-published_at')
        q = self.request.query_params.get('q')
        source = self.request.query_params.get('source')
        if q:
            qs = qs.filter(
                Q(title__icontains=q)
                | Q(summary__icontains=q)
                | Q(content__icontains=q)
            )
        if source:
            qs = qs.filter(source__iexact=source)
        return qs
