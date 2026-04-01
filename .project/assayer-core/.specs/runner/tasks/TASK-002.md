---
id: TASK-002
spec: runner
status: pending
depends-on: []
created: 2026-03-30
---

# TASK-002: Implement token usage extractor

## What to do
Create `assayer/runner/token_extractor.py` and implement `extract_token_usage(result, pricing_config) -> TokenUsage` as specified in `design.md`.

Extracts `input_tokens` and `output_tokens` from `result.usage_metadata` (defaults to 0 if absent). Computes `cost_usd` if `PricingConfig` is provided.

## Acceptance Criteria
- [ ] Extracts `input_tokens` and `output_tokens` from `result.usage_metadata` dict
- [ ] Defaults to 0 when `usage_metadata` is absent or missing keys
- [ ] `cost_usd = input_tokens * cost_per_input + output_tokens * cost_per_output` when `PricingConfig` provided
- [ ] `cost_usd = None` when no `PricingConfig`
- [ ] Google-style docstring and full type hints

## Dependencies
- none

## Tests
Test file:

## Implementation Notes

## Commit
Hash:
