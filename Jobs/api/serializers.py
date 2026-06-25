from rest_framework import serializers

from Jobs.models import Jobs


class JobListSerializer(serializers.ModelSerializer):
    company_name = serializers.SerializerMethodField()
    location_text = serializers.SerializerMethodField()
    salary_formatted = serializers.SerializerMethodField()
    source_name = serializers.SerializerMethodField()

    class Meta:
        model = Jobs
        fields = [
            "id",
            "title",
            "company_name",
            "location_text",
            "work_type",
            "salary_formatted",
            "posted_at",
            "skills",
            "description",
            "source_name",
            "external_url",
            "jobMatch",
            "match_reasons",
            "match_concerns",
        ]

    jobMatch = serializers.SerializerMethodField()
    match_reasons = serializers.SerializerMethodField()
    match_concerns = serializers.SerializerMethodField()


    def _get_profile(self):
        if not hasattr(self, '_cached_profile'):
            request = self.context.get('request')
            if not request or not request.user.is_authenticated:
                self._cached_profile = None
            else:
                from Oauth.models import Profile
                self._cached_profile = Profile.objects.filter(user=request.user).first()
        return self._cached_profile

    def _get_match_data(self, obj):
        # Cache both profile and match results for this specific instance
        if not hasattr(self, '_cached_match_results'):
            self._cached_match_results = {}
        
        job_id = str(obj.id)
        if job_id not in self._cached_match_results:
            profile = self._get_profile()
            if not profile:
                return {"win_probability": 45, "reasons": None, "concerns": None}
            
            from Intelligence.JobMatching.matcher import calculate_win_probability
            try:
                # One call instead of three
                self._cached_match_results[job_id] = calculate_win_probability(profile, obj, deep_analysis=False)
            except:
                self._cached_match_results[job_id] = {"win_probability": 65, "reasons": "Matching logic unavailable", "concerns": None}
        
        return self._cached_match_results[job_id]

    def get_jobMatch(self, obj):
        data = self._get_match_data(obj)
        res = data.get("win_probability") or data.get("overall_score") or 65
        return int(res)

    def get_match_reasons(self, obj):
        data = self._get_match_data(obj)
        return data.get("reasons")

    def get_match_concerns(self, obj):
        data = self._get_match_data(obj)
        return data.get("concerns")

    def get_company_name(self, obj: Jobs):
        try:
            return obj.company.name
        except Exception:
            return None

    def get_location_text(self, obj: Jobs):
        try:
            # Prefer city, fallback to country
            city = getattr(obj.location, "city", None)
            country = getattr(obj.location, "country", None)
            if city and country:
                return f"{city}, {country}"
            return city or country or "Remote"
        except Exception:
            return None

    def get_salary_formatted(self, obj: Jobs):
        try:
            pm = obj.parsed_metadata or {}
            return pm.get("salary_formatted") or "Not specified"
        except Exception:
            return "Not specified"

    def get_source_name(self, obj: Jobs):
        try:
            return obj.source.name
        except Exception:
            return None
