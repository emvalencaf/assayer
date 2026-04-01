# Architecture Diagram — System Overview

Example of a validated system architecture diagram using flowchart
in a C4-inspired style (Context + Container level).

Related: reference only
Last updated: 2025-01-01

```mermaid
flowchart TD
    User(["👤 User\n[Browser]"])
    Mobile(["📱 Mobile App\n[React Native]"])

    subgraph System ["Our System"]
        Gateway["API Gateway\n[Node.js / Express]"]
        AuthSvc["Auth Service\n[Node.js]"]
        AppSvc["App Service\n[Node.js]"]
        Worker["Background Worker\n[BullMQ]"]
    end

    subgraph Storage ["Storage"]
        DB[("Primary DB\n[PostgreSQL]")]
        Cache[("Cache\n[Redis]")]
        Queue[("Job Queue\n[Redis]")]
    end

    subgraph External ["External Services"]
        Email["Email\n[Resend]"]
        Storage2["Object Storage\n[S3]"]
    end

    User -->|HTTPS| Gateway
    Mobile -->|HTTPS| Gateway

    Gateway --> AuthSvc
    Gateway --> AppSvc

    AuthSvc --> DB
    AuthSvc --> Cache

    AppSvc --> DB
    AppSvc --> Cache
    AppSvc --> Queue

    Worker --> Queue
    Worker --> Email
    Worker --> Storage2
```

## Notes on this example

- Use `subgraph` to group related components visually
- Label nodes with name + technology in two lines using `\n`
- Use `(["text"])` for external actors (people, external systems)
- Use `[("text")]` for data stores (cylinder shape)
- Label arrows with the protocol or data being exchanged
- Keep to container/service level — do not show internal implementation
