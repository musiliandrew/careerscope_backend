from django.test import TestCase
from unittest.mock import patch, MagicMock
from Oauth.models import Profile
from Jobs.models import Jobs, Company
from django.contrib.auth.models import User
from Intelligence.JobMatching.matcher import calculate_win_probability

class MatcherIntegrationTest(TestCase):
    def setUp(self):
        self.user = User.objects.create(username="testuser")
        self.profile = Profile.objects.create(user=self.user)
        self.company = Company.objects.create(name="OpenAI")
        self.job = Jobs.objects.create(
            title="Machine Learning Engineer",
            company=self.company,
            description="Looking for Python and ML experts"
        )
        
    @patch('Intelligence.JobMatching.matcher.DecisionEngineClient.evaluate_match')
    def test_calculate_win_probability_calls_sdk(self, mock_evaluate_match):
        # Setup mock SDK response
        mock_result = MagicMock()
        mock_result.overall_readiness = 88.5
        
        mock_explanation = MagicMock()
        mock_explanation.conclusion = "Strong Python skills detected."
        mock_explanation.reasoning_trace = "Computed score: 88.5"
        mock_result.explanations = [mock_explanation]
        
        # Async mock behavior
        async def mock_coro(*args, **kwargs):
            return mock_result
            
        mock_evaluate_match.side_effect = mock_coro
        
        # Execute
        result = calculate_win_probability(self.profile, self.job)
        
        # Verify
        self.assertEqual(result["overall_score"], 88)
        self.assertEqual(result["win_probability"], 88)
        self.assertEqual(result["reasons"], "Strong Python skills detected.")
        self.assertEqual(result["concerns"], "Computed score: 88.5")
        
        # Verify SDK was called
        mock_evaluate_match.assert_called_once()
        request_arg = mock_evaluate_match.call_args[0][0]
        self.assertEqual(request_arg.job_snapshot.title, "Machine Learning Engineer")
        self.assertEqual(request_arg.job_snapshot.company_name, "OpenAI")
