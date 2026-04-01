# State Diagram — Resource Lifecycle

Example of a validated state machine showing a resource moving through
a review and publish workflow.

Related: reference only
Last updated: 2025-01-01

```mermaid
stateDiagram-v2
    [*] --> Draft : created

    Draft --> InReview : submit()
    Draft --> Deleted : delete()

    InReview --> Draft : request_changes()
    InReview --> Published : approve()
    InReview --> Rejected : reject()

    Published --> Archived : archive()
    Published --> Draft : unpublish()

    Rejected --> Draft : revise()

    Archived --> [*]
    Deleted --> [*]

    note right of InReview
        Reviewer must be different
        from the original author
    end note
```

## Notes on this example

- Always use `stateDiagram-v2` — `stateDiagram` is deprecated
- `[*]` represents the start and end states
- Transition labels use the format `event()` or plain text
- Use `note` blocks sparingly — only for constraints not obvious from
  the diagram structure
- Avoid more than 8–10 states — split into sub-state diagrams if needed
