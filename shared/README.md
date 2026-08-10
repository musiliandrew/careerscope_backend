# careerscope-shared

The foundational library and SDK for the **CareerScoper** microservices architecture. It acts as the single source of truth for contracts (schemas), AI prompt registries, centralized settings, and observability tracing tools.

---

## 🚀 Purpose & Architecture

In a distributed microservice system, maintaining type safety and consistent prompt formatting across various engines is a challenge. `careerscope-shared` resolves this by packaging:
* **Contracts**: Pydantic models enforcing boundaries between microservices.
* **AI Observability**: Context utilities tracking token consumption, costs, and request latency.
* **Prompt Registry**: Version-controlled and template-driven prompts loaded dynamically.
* **Centralized Configuration**: Settings models driven by `pydantic-settings`.

---

## 📦 Installation

To install `careerscope-shared` in your local development environment:

```bash
# From the CareerScoper root workspace:
pip install -e ./shared
```

This installs the package in **editable mode** (`-e`), meaning any changes you make within the `shared/` directory will immediately propagate to all importing services (e.g. `backend`, `decision-engine`) without reinstalling.

---

## 🛠️ Usage & Examples

### 1. Data Contracts & Schemas (`shared.contracts`)
Ensure microservices adhere to identical request/response payloads.

```python
from shared.contracts.requests.evaluate_match import EvaluateMatchRequest, JobRequirementSnapshot
from shared.contracts.responses.mission import IntelligenceSnapshot

# Construct stateless payload
request_payload = EvaluateMatchRequest(
    profile_snapshot=IntelligenceSnapshot(...),
    job_snapshot=JobRequirementSnapshot(
        title="Senior Python Engineer",
        company_name="Innovate Corp",
        required_skills=["Python", "FastAPI", "Docker"],
        nice_to_have_skills=["Kubernetes"],
        description="Looking for an experienced Backend Engineer..."
    ),
    relevant_evidence=[]
)

# Convert to JSON for HTTP transmission
json_data = request_payload.model_dump_json()
```

### 2. Prompt Registry (`shared.ai.prompts`)
Load and format version-controlled prompts dynamically from the file system.

```python
from shared.ai.prompts.registry import PromptRegistry

# Load the matching score prompt bundle
prompt_bundle = PromptRegistry.load("reasoning.match_score")

print(f"System Prompt:\n{prompt_bundle.system_prompt}")
print(f"User Template:\n{prompt_bundle.user_template}")
```

### 3. Execution Context & Observability (`shared.ai.observability`)
Trace execution times and LLM metadata for reliable logging.

```python
from shared.ai.observability import ExecutionContext
import time

# Create a trace context
context = ExecutionContext(
    provider="gemini",
    model="gemini-2.0-flash",
    prompt_version="reasoning.match_score.v1",
    temperature=0.2
)

# Simulate LLM call
start_time = time.time()
context.started_at = start_time

# ... performing call ...

context.finished_at = time.time()
context.prompt_tokens = 450
context.completion_tokens = 120
context.calculate_duration()

print(f"Call finished in {context.latency_ms} ms")
```

### 4. Settings Configuration (`shared.config`)
Define environment variables clearly with type checking and prefix loaders.

```python
from shared.config.decision import DecisionSettings

# Automatically loads DECISION_GEMINI_API_KEY, DECISION_ENVIRONMENT, etc., from .env
settings = DecisionSettings()

print(f"Environment: {settings.environment}")
print(f"Primary AI Engine: {settings.ai_primary}")
```

---

## 📂 Project Directory Structure

```text
shared/
├── ai/
│   ├── prompts/          # System and user prompts (YAML and Markdown templates)
│   ├── providers/        # LLM integration clients (Gemini, Tavily)
│   └── observability.py  # Latency, token trace, and context management
├── config/               # Settings loading (fastapi, db, decision, etc.)
├── contracts/            # Pydantic schema models for requests & responses
├── digital_twin/         # Domain structures for builder and twin emulation
├── domain/               # Domain-specific structures (e.g. beliefs, features)
├── setup.py              # Packaging installation script
└── tests/                # Standard test suites
```
