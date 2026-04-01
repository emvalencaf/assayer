---
spec: {spec-name}
created: YYYY-MM-DD
---

# Design: {Spec Name}

<!-- Create this file only when the spec has design complexity that would
     clutter spec.md: non-trivial API contracts, multi-step state machines,
     complex UI flows, or significant data transformation logic. -->

## UI Flow
<!-- User-facing flows. Use Mermaid — delegate diagram creation to @agent-docs. -->

## State Machine
<!-- Non-trivial state transitions. Delegate diagram creation to @agent-docs. -->

## API Contract

### {METHOD} /{endpoint}

**Request**
```json
{
  "field": "type"
}
```

**Response — 200 OK**
```json
{
  "id": "string"
}
```

**Response — 4xx**
```json
{
  "error": "string",
  "code": "ERROR_CODE"
}
```

## Data Transformations
<!-- Input → output mappings for complex transformations -->
