from rest_framework import serializers
from News.models import NewsArticles


class NewsArticleSerializer(serializers.ModelSerializer):
    publishedAt = serializers.DateTimeField(source='published_at')
    sentimentScore = serializers.DecimalField(max_digits=4, decimal_places=3, source='sentiment_score', required=False)

    class Meta:
        model = NewsArticles
        fields = [
            'id',
            'title',
            'summary',
            'url',
            'publishedAt',
            'source',
            'sentimentScore',
            'tags',
            'topics',
        ]
