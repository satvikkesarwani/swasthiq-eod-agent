# Final Architecture

## System Context

```mermaid
flowchart LR
    User["Clinic operator"] --> FE["React app on Vercel"]
    FE --> API["FastAPI backend on Railway"]
    API --> DB["SQLite on persistent volume"]
    API --> LLM["NVIDIA ChatNVIDIA API (optional)"]
    API --> Fallback["Deterministic fallback"]
```

## Import Flow

```mermaid
flowchart TD
    A["Upload JSON"] --> B["Browser shape checks"]
    B --> C["PUT clinic-day"]
    C --> D["Backend row validation"]
    D --> E["Deterministic report"]
    E --> F["Atomic SQLite replace"]
    F --> G["Reconciliation / Analytics / Narrative routes"]
```

## Deterministic Report Flow

```mermaid
flowchart TD
    Rows["Accepted rows"] --> Reconcile["Reconciliation service"]
    Rows --> Analytics["Analytics service"]
    Rows --> Quality["Data-quality warnings"]
    Reconcile --> Report["Canonical deterministic report"]
    Analytics --> Report
    Quality --> Report
```

## Narrative Flow

```mermaid
flowchart TD
    Report["Canonical report"] --> Facts["Approved fact catalogue"]
    Facts --> Provider["ChatNVIDIA structured draft"]
    Provider --> Validate["Grounding validator"]
    Validate -->|valid| Persist["Persist summary and traces"]
    Validate -->|invalid| Repair["One repair attempt"]
    Repair --> Validate
    Provider -->|provider unavailable| Fallback["Deterministic fallback"]
    Repair -->|failed| Fallback
    Fallback --> Validate
```

## Cache Flow

```mermaid
flowchart TD
    GetNarrative["GET narrative"] --> Exists{"Stored narrative exists?"}
    Exists -->|no| NotGenerated["404 not generated"]
    Exists -->|yes| Hash{"Report hash matches?"}
    Hash -->|yes| Current["Return current narrative"]
    Hash -->|no| Stale["409 stale"]
```

## Deployment Topology

- Frontend: Vercel static Vite build with SPA rewrites.
- Backend: Railway Docker deployment.
- Database: SQLite file under a Railway persistent volume path configured through `DATABASE_URL`.
- AI provider: NVIDIA API from backend only.
