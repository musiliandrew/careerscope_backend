"""
mission_control.py - The Dashboard Aggregation Service

This service owns the Dashboard View Model.
It orchestrates data from:
- Digital Twin
- Market Intelligence
- Recommendation Engine
and produces a single immutable Mission Control response.
"""
from typing import Dict, Any
from shared.digital_twin.builder import DigitalTwinBuilder

class MissionControlService:
    
    @classmethod
    def build(cls, user_id: str) -> Dict[str, Any]:
        """
        Builds the unified Mission Control payload for the frontend.
        """
        # 1. Load the Digital Twin
        twin = DigitalTwinBuilder.build(user_id)
        if "error" in twin:
            return {"error": twin["error"]}
            
        snapshot = twin.get("snapshot", {})
        
        # 2. Query Market Intelligence (Not fully implemented yet)
        # As per instructions, return empty arrays instead of fake data
        market_changes = []
        
        # 3. Query Recommendation Outputs
        # E.g., Top Opportunity (Using mock placeholder structure as requested by UI contract, 
        # but empty/null if no real data is available in backend yet)
        top_opportunity = None
        
        # 4. Construct Dashboard View Model
        # This matches the structure requested by the UI exactly
        response = {
            "career_readiness": {
                "overall_score": snapshot.get("overall_readiness_score", 0),
                "verified_strengths": snapshot.get("verified_strengths", []),
            },
            "career_snapshot": snapshot,
            "top_opportunity": top_opportunity,
            "recommended_action": {
                "bottlenecks": snapshot.get("primary_obstacles", []),
                "action": snapshot.get("recommended_next_action", "")
            },
            "market_changes": market_changes,
            "timeline_preview": [],
            "notifications": []
        }
        
        return response
