# ADR-001: Local Handoff is the academic delivery model

- **Status:** Accepted
- **Date:** 2026-08-31
- **Deciders:** dh-pdf-trans maintainers
- **Scope:** `academic` quality mode only

## Context

The existing Google mode has no domain glossary enforcement, document context, or safe handling for sensitive material. A direct LLM/provider integration would add unresolved decisions about credentials, cost, retention, consent, retries, and failure semantics. OCR and image-text translation are separate products with different rendering and quality risks.

## Decision

`academic` mode is implemented as a local Handoff lifecycle:

```text
safe segments + glossary/context → JSONL export → human/agent translation → JSONL import → local verification/rebuild
```

- Handoff export/import does not make a network request.
- A missing translation remains source text and produces `partial`; it must never silently fall back to Google.
- `draft` remains the only mode allowed to use Google Translate and must disclose that segment content leaves the machine.
- The desktop GUI initially exposes local bundle export/import and report status only. It does not collect, store, or transmit API keys.
- OCR and text translation inside figures are deferred. Protected figures remain source-language content unless a future, explicitly selected image-translation workflow is approved.

## Options considered

| Option | Decision | Rationale |
|---|---|---|
| Local Handoff export/import | Accepted | Preserves privacy, supports expert terminology review, and reuses the existing engine contract. |
| Direct commercial provider | Deferred | Requires a security/privacy/cost ADR, secret storage and user consent UX. |
| Silent Google fallback | Rejected | Violates academic quality and data-disclosure requirements. |
| OCR plus figure translation | Deferred | Requires OCR confidence, redaction/re-render, terminology and visual QA capabilities not in this release. |

## Consequences

### Positive

- T-201 glossary resolver, T-202 contextual JSONL and T-203 academic CLI can proceed without external credentials.
- Academic content remains local until the user deliberately hands the bundle to a translator.
- Failure behavior is explicit and reviewable through `partial` and quality reports.

### Costs

- The first academic workflow is not one-click translation in the desktop app.
- Users need a human or agent capable of filling the Handoff bundle.
- End-to-end throughput is lower than draft mode.

## Guardrails

1. Never label Google output as academic mode.
2. Never include API keys in JSONL, cache, report, logs, settings or support bundles.
3. Preserve every unclassified/unsafe region; do not translate it to improve coverage.
4. Keep JSONL v1 compatibility while adding context fields in v2.

## Revisit triggers

Create a successor ADR before changing this decision if any of the following is proposed:

- direct provider or local model integration;
- credential collection/storage;
- sending academic document content over the network;
- OCR or image-text translation;
- changing `partial` fallback semantics.
