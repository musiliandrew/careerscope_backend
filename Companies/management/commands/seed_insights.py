import uuid
from django.core.management.base import BaseCommand
from django.utils import timezone
from Companies.models import MarketInsights, IndustryTrends

class Command(BaseCommand):
    help = 'Seeds initial market insights and industry trends'

    def handle(self, *args, **kwargs):
        self.stdout.write("Seeding market insights...")
        
        # 1. Market Insights
        insights = [
            {
                "id": uuid.uuid4(),
                "insight_type": "Hiring Trend",
                "title": "Rise of AI Engineering",
                "description": "Demand for dedicated AI Engineers has grown by 45% in the last 6 months across FAANG and top unicorns.",
                "metric_value": 45,
                "metric_unit": "%",
                "industry": "Software Engineering",
                "calculation_date": timezone.now()
            },
            {
                "id": uuid.uuid4(),
                "insight_type": "Salary Insight",
                "title": "Remote Premium Shrinkage",
                "description": "Salary gaps between local and remote roles are closing as companies standardize global pay scales.",
                "metric_value": 12,
                "metric_unit": "%",
                "industry": "Tech",
                "calculation_date": timezone.now()
            }
        ]
        
        for i in insights:
            MarketInsights.objects.get_or_create(title=i["title"], defaults=i)

        # 2. Industry Trends
        trends = [
            {
                "id": uuid.uuid4(),
                "industry": "FinTech",
                "trend_type": "Market Size",
                "metric_name": "Digital Payments Volume",
                "current_value": 1200000000.00,
                "change_percentage": 15.5,
                "period_start": timezone.now().date(),
                "period_end": timezone.now().date(),
                "calculation_date": timezone.now()
            },
            {
                "id": uuid.uuid4(),
                "industry": "HealthTech",
                "trend_type": "Investment",
                "metric_name": "VC Funding",
                "current_value": 450000000.00,
                "change_percentage": -5.2,
                "period_start": timezone.now().date(),
                "period_end": timezone.now().date(),
                "calculation_date": timezone.now()
            }
        ]
        
        for t in trends:
            IndustryTrends.objects.get_or_create(
                industry=t["industry"], 
                metric_name=t["metric_name"], 
                defaults=t
            )

        self.stdout.write(self.style.SUCCESS('Successfully seeded insights data'))
