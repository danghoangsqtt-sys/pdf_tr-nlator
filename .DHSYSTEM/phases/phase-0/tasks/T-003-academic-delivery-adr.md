# T-003 — Chốt mô hình delivery academic mode

## Objective

Ghi Architecture Decision Record cho academic mode để loại bỏ ambiguity trước khi xây glossary resolver, Handoff v2, CLI và GUI. Chốt local Handoff export/import là implementation target; provider thương mại và OCR bị deferred.

## Paths

- `docs/adr/ADR-001-academic-delivery-model.md`
- `docs/SPEC-academic-pdf-translation.md`
- `docs/PLAN-academic-pdf-translation.md`
- `.DHSYSTEM/phases/phase-0/PHASE-STATE.md`
- `.DHSYSTEM/phases/phase-0/tasks/T-003-academic-delivery-adr.md`
- `.DHSYSTEM/TRACKER.md`
- `.DHSYSTEM/HANDOFF.json`

## File-Level Plan

- `ADR-001-academic-delivery-model.md`: options, decision, consequences, data-flow, privacy policy, release boundary and revisit triggers.
- SPEC/PLAN: thay open ADR-001 bằng quyết định có link; đồng bộ dependency để T-201/T-202/T-203 được unblock.
- State files: theo dõi task, evidence và checkpoint.

## Best-practice checklist

- Quyết định phải reversible, cụ thể và có ngày/revisit triggers.
- Academic mode không có network transport hay credential surface.
- Provider/OCR không được disguised thành optional dependency trong release hiện tại.
- Draft Google disclosure vẫn là requirement độc lập, không bị ADR này làm mờ.

## Verification

```powershell
rg -n "Status: Accepted|local Handoff|No network|Deferred|T-201|T-202|T-203" docs\adr\ADR-001-academic-delivery-model.md docs\SPEC-academic-pdf-translation.md docs\PLAN-academic-pdf-translation.md
git diff --check
```

Kỳ vọng: một quyết định Accepted có scope, consequences và trigger rõ; roadmap không còn mô tả T-003 là blocker cho Handoff local.

## Rollback / fallback

- Nếu cần provider sau release, tạo ADR mới thay vì sửa ngầm ADR-001; provider chỉ bắt đầu sau review security/privacy/cost.
- Nếu agent Handoff không sẵn sàng, academic mode export bundle và trả `partial`, không fallback im lặng sang Google.

## Implementation Notes

- 2026-08-31: task contract tạo trước khi viết ADR.
- 2026-08-31: ADR-001 accepted local Handoff; SPEC/PLAN liên kết quyết định và `git diff --check` pass. Task chờ checkpoint Git trước khi PASS.
