# Flowchart — Decision Branch

Example of a validated flowchart with decision branches and error handling.

Related: reference only
Last updated: 2025-01-01

```mermaid
flowchart TD
    A([Start]) --> B[Receive request]
    B --> C{Authenticated?}

    C -- No --> D[Return 401 Unauthorized]
    C -- Yes --> E{Has permission?}

    E -- No --> F[Return 403 Forbidden]
    E -- Yes --> G[Process request]

    G --> H{Validation passes?}
    H -- No --> I[Return 400 Bad Request]
    H -- Yes --> J[Persist to database]

    J --> K([Return 201 Created])

    style D fill:#f88,stroke:#c00
    style F fill:#f88,stroke:#c00
    style I fill:#f88,stroke:#c00
    style K fill:#8f8,stroke:#080
```

## Notes on this example

- `([text])` renders a rounded pill — use for start/end nodes
- `{text}` renders a diamond — use for decisions
- `[text]` renders a rectangle — use for actions
- `TD` means top-down; use `LR` for left-to-right layouts
- Style error paths in red and success in green for readability
- Keep decision labels short: "Yes/No" or the condition being checked
