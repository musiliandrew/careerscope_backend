# Scenario: Senior Engineer applying for Core ML Role

**Context:** The candidate has extremely high verification scores in Python and PyTorch. 
**Expected Behavior:** 
1. The `EvidenceCoverage` algorithm should yield near 100% for Python and PyTorch.
2. The `GapAnalysis` algorithm MUST identify "Transformers" as missing because it's an explicit requirement.
3. The resulting `ReadinessScore` algorithm should be mathematically bounded around 88.5% (2/3 core requirements strongly met).
4. The LLM Explainer should generate coaching text focusing heavily on learning Transformers.
