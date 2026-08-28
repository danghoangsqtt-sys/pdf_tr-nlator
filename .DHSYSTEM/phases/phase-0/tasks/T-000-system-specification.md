# T-000 — Hoàn thiện system specification và development plan

## Objective

Chuẩn hoá đặc tả hệ thống và kế hoạch phát triển thành baseline có thể thực thi: xác định module boundaries, hợp đồng dữ liệu, mode vận hành, quyết định fail-safe, dependency, task order, gates và Definition of Done.

## Paths

- `docs/SPEC-academic-pdf-translation.md`
- `docs/PLAN-academic-pdf-translation.md`
- `.DHSYSTEM/ROADMAP.md`
- `.DHSYSTEM/TRACKER.md`
- `.DHSYSTEM/HANDOFF.json`
- `.DHSYSTEM/phases/phase-0/PHASE-STATE.md`
- `.DHSYSTEM/phases/phase-0/tasks/T-000-system-specification.md`

## File-Level Plan

- `docs/SPEC-academic-pdf-translation.md`: mở rộng từ feature spec thành system specification: actor, module, lifecycle, contracts, state machine, security/privacy, observability, compatibility, acceptance và decision log.
- `docs/PLAN-academic-pdf-translation.md`: bổ sung WBS thực thi, dependency graph, task-level Definition of Done, release gates, ownership và trình tự khả thi.
- `.DHSYSTEM/*`: đồng bộ trạng thái để P0 là prerequisite đang chạy; P1 chỉ tiếp tục với T-103/T-104 sau P0. Ghi T-102 là emergency hardening đã hoàn tất.

## Best-practice checklist

- Mọi requirement phải có acceptance criterion có thể kiểm thử.
- Không biến assumption về OCR/provider thành cam kết shipping.
- Phân biệt rõ `draft`, `academic`, `partial`, `failed` và source-preservation invariant.
- Task phải có dependency, file ownership, verification và rollback/fallback rõ ràng.

## Verification

```powershell
rg -n "FR-|NFR-|AC-|T-[0-9]{3}|Definition of Done|Release gate" docs\SPEC-academic-pdf-translation.md docs\PLAN-academic-pdf-translation.md
git diff --check
```

Kỳ vọng: mọi requirement và task có ID; không có whitespace error.

## Implementation Notes

- 2026-08-28: task contract và P0 state được tạo trước khi cập nhật đặc tả/plan.
- 2026-08-28: SPEC/PLAN đã bổ sung module boundaries, data contracts, state machine, error taxonomy, privacy, gates, traceability, WBS, milestones, Definition of Done và rollback controls. `git diff --check` pass. Git persistence hoàn tất trên `origin/main`; task PASS.
