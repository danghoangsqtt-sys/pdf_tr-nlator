# Tracker

## Current state

- Current phase: P1 — Bảo vệ figure, scan và formula
- Current task: T-103 — Formula/scan classifier fail-closed
- Status: T-101 completed and pushed; next T-103
- Git persistence: `origin/main` configured and pushed.

## Latest verification

- T-102: `python -m unittest discover -s tests -v` passed 68 tests on 2026-08-28.
- T-102 passed after GitHub remote was configured and its commits pushed.
- T-102 là emergency hardening độc lập. Các task P1 tiếp theo chỉ bắt đầu sau P0.
- T-000: SPEC/PLAN baseline complete; task checkpoint pushed to `origin/main`.
- T-001: CC0 academic-v1 fixture, manifest and integrity tests complete; task checkpoint pushed to `origin/main`.
- T-002: terminology baseline in progress.
- T-002: glossary, expected targets and prohibited literal translations complete; task checkpoint pushed to `origin/main`.
- T-003: local academic Handoff ADR in progress.
- T-003: ADR-001 accepted; task checkpoint pushed to `origin/main`.
- P0 completed on 2026-08-31; T-101 region inventory in progress.
- T-101: direct image/vector region inventory and mask protection verified locally (80 tests); implementation pushed to `origin/main` at `2f07dc1`.
