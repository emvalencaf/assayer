# Entity Relationship Diagram — Basic Schema

Example of a validated ERD showing a common user/resource schema pattern.

Related: reference only
Last updated: 2025-01-01

```mermaid
erDiagram
    USER {
        uuid id PK
        string email UK
        string password_hash
        timestamp created_at
        timestamp updated_at
    }

    SESSION {
        uuid id PK
        uuid user_id FK
        string token UK
        timestamp expires_at
        timestamp created_at
    }

    RESOURCE {
        uuid id PK
        uuid owner_id FK
        string title
        text content
        string status
        timestamp created_at
        timestamp updated_at
    }

    USER ||--o{ SESSION : "has"
    USER ||--o{ RESOURCE : "owns"
```

## Notes on this example

- `PK` marks primary keys, `FK` foreign keys, `UK` unique constraints
- Relationship syntax: `||--o{` means "one to zero-or-many"
- Common cardinality markers:
  - `||` exactly one
  - `o|` zero or one
  - `||--o{` one to zero-or-many
  - `}|--|{` one-or-many to one-or-many
- Keep column types generic: `string`, `uuid`, `text`, `timestamp`, `int`
