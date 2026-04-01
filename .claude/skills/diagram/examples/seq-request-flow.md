# Sequence Diagram — Request Flow

Example of a validated sequence diagram showing an authenticated API request.

Related: reference only
Last updated: 2025-01-01

```mermaid
sequenceDiagram
    actor User
    participant Client
    participant API
    participant Auth
    participant DB

    User->>Client: submits form
    Client->>API: POST /resource (Bearer token)
    API->>Auth: validate token
    Auth-->>API: token valid, user-id: 123

    API->>DB: INSERT INTO resources ...
    DB-->>API: row created, id: 456

    API-->>Client: 201 Created { id: 456 }
    Client-->>User: shows success message
```

## Notes on this example

- `actor` renders a person icon — use for end users
- `participant` renders a box — use for systems and services
- `-->>` denotes a response (dashed line)
- `->>` denotes a request (solid line)
- Avoid more than 6–7 participants — split into two diagrams if needed
