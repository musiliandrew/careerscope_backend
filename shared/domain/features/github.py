from datetime import datetime
from typing import List
from uuid import UUID
from shared.domain.features.base import Feature

class GitHubFeatureExtractor:
    """
    Computes deterministic metrics from raw GitHub evidence.
    """
    
    @staticmethod
    def extract_commits_last_year(raw_github_data: dict, evidence_id: UUID) -> Feature[int]:
        # Implementation would parse the raw data to compute this
        commits = raw_github_data.get("total_commits_last_year", 0)
        
        return Feature(
            id="feat_github_commits_last_12m",
            version=1,
            value=commits,
            evidence_ids=[evidence_id]
        )
        
    @staticmethod
    def extract_languages_used(raw_github_data: dict, evidence_id: UUID) -> Feature[List[str]]:
        # e.g., mapping to Ontology IDs
        languages = raw_github_data.get("languages", [])
        
        return Feature(
            id="feat_github_languages_used",
            version=1,
            value=languages,
            evidence_ids=[evidence_id]
        )
