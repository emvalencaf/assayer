---
id: TASK-002
spec: runner
status: done
depends-on: []
created: 2026-03-30
---

# TASK-002: Implement token usage extractor

## What to do
Create `assayer/runner/token_extractor.py` and implement `extract_token_usage(result, pricing_config) -> TokenUsage` as specified in `design.md`.

Extracts `input_tokens` and `output_tokens` from `result.usage_metadata` (defaults to 0 if absent). Computes `cost_usd` if `PricingConfig` is provided.

## Acceptance Criteria
- [x] Extracts `input_tokens` and `output_tokens` from `result.usage_metadata` dict
- [x] Defaults to 0 when `usage_metadata` is absent or missing keys
- [x] `cost_usd = input_tokens * cost_per_input + output_tokens * cost_per_output` when `PricingConfig` provided
- [x] `cost_usd = None` when no `PricingConfig`
- [x] Google-style docstring and full type hints

## Dependencies
- none

## Tests
Test file: `/home/emvalenca/personal_projects/assayer/tests/runner/test_token_extractor.py`

Comprehensive tests covering:
- Extraction of input_tokens and output_tokens from result.usage_metadata dict
- Defaults to 0 when usage_metadata is absent, None, or missing required keys
- Cost calculation using formula: input_tokens * cost_per_input_token + output_tokens * cost_per_output_token
- cost_usd set to None when no PricingConfig provided
- Handling of edge cases like string/float token values, zero values, and partial metadata
- Verification that function returns TokenUsage instance

All tests currently fail with ModuleNotFoundError (expected), confirming red state before implementation.

## Implementation Notes

Successfully implemented `extract_token_usage` function in `assayer/runner/token_extractor.py`:

- Used `getattr(result, "usage_metadata", None) or {}` pattern to safely handle missing attribute or None values
- Applied `int()` conversion to handle string/float token values as required by tests
- Implemented cost calculation formula exactly as specified: `input_tokens * cost_per_input_token + output_tokens * cost_per_output_token`
- Set `cost_usd = None` when no pricing config provided
- Added comprehensive Google-style docstring with Args and Returns sections
- All 13 test cases pass, including edge cases for missing metadata, partial metadata, type conversions, and cost calculations

## Commit
Hash:
