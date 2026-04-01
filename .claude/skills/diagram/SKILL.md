# Skill: Mermaid Diagram-as-Code

## Core rules

- **Only Mermaid** — never use D2, PlantUML, Graphviz, or any other tool
- **Always validate** with `mmdc` before saving — syntax errors must be
  caught and fixed before a diagram is written to disk
- **Never use binary files** — `.md` files with Mermaid code are the
  canonical source; exported SVG/PNG are build artifacts, not sources
- **One concept per diagram** — if a diagram needs more than 3 legend
  items or becomes hard to read, split it into focused diagrams

## Validation workflow (mandatory)

```bash
# Install once globally
npm install -g @mermaid-js/mermaid-cli

# Validate before saving (quiet mode — only prints on error)
mmdc -i {diagram-file} --quiet

# If validation fails: fix the syntax, re-validate, then save
# Never save a diagram that fails validation
```

## MCP preview (optional, recommended for iteration)

If `claude-mermaid` MCP is configured, use it for live preview during
diagram development. Install via:

```bash
npm install -g claude-mermaid
```

Configure in `.claude/mcp.json`:
```json
{
  "mcpServers": {
    "mermaid": { "command": "claude-mermaid" }
  }
}
```

## Diagram type selection

| Use case                         | Diagram type       |
|----------------------------------|--------------------|
| Request/response flows           | `sequenceDiagram`  |
| Decision trees, process flows    | `flowchart`        |
| Database schema                  | `erDiagram`        |
| Object/component lifecycle       | `stateDiagram-v2`  |
| Class relationships              | `classDiagram`     |
| Project phases and timelines     | `gantt`            |
| High-level system architecture   | `flowchart` (C4-style) |

When in doubt, prefer `sequenceDiagram` for interactions and
`flowchart TD` for everything else.

## File naming and location

```
.project/{prd}/diagrams/{type}-{name}.md    — PRD-scoped
docs/diagrams/{type}-{name}.md              — project-wide
```

Name prefixes: `seq-` | `flow-` | `erd-` | `state-` | `class-` | `arch-`

Examples: `seq-login-flow.md`, `erd-user-schema.md`, `arch-system.md`

## File structure

Every diagram file must follow this structure:

```markdown
# {Diagram Title}

{One sentence: what this diagram shows and why it exists.}

Related: {link to spec or PRD}
Last updated: YYYY-MM-DD

​```mermaid
{diagram code}
​```
```

## Common syntax pitfalls to avoid

- Double quotes inside node labels break the parser — use single quotes
  or omit quotes entirely for simple labels
- Arrow labels with special characters must be quoted: `-- "label" -->`
- `stateDiagram` is deprecated — always use `stateDiagram-v2`
- Avoid deeply nested subgraphs (more than 2 levels) — split the diagram
- Participant names with spaces in `sequenceDiagram` must be quoted:
  `participant "My Service" as svc`

## Examples

See the `examples/` directory for validated, ready-to-copy diagrams:

- `examples/seq-request-flow.md` — sequence diagram
- `examples/flow-decision.md` — flowchart with decision branches
- `examples/erd-basic.md` — entity relationship diagram
- `examples/state-lifecycle.md` — state machine
- `examples/arch-system.md` — system architecture (C4-style)
