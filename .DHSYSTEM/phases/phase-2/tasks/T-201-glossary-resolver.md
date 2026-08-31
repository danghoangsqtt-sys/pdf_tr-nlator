# T-201 — Glossary schema và resolver

## Objective

Cung cấp resolver glossary cục bộ, typed và deterministic cho thuật ngữ AI/ML.
Resolver phải match cụm theo word boundary, ưu tiên source dài nhất, áp dụng
policy `translate`/`preserve`, và từ chối entry hoặc conflict không hợp lệ.

## Paths

- `pdf2zh/terminology.py`
- `tests/test_terminology.py`
- `.DHSYSTEM/phases/phase-2/PHASE-STATE.md`
- `.DHSYSTEM/phases/phase-2/tasks/T-201-glossary-resolver.md`
- `.DHSYSTEM/TRACKER.md`
- `.DHSYSTEM/HANDOFF.json`
- `CHANGELOG.md`

## Verification

```powershell
& .venv\Scripts\python.exe -m unittest tests.test_terminology -v
& .venv\Scripts\python.exe -m unittest discover -s tests -q
git diff --check
```

## Definition of Done

- Fixture glossary resolve chính xác, boundary/case/conflict có regression test.
- Không network/OCR/provider; checkpoint push/tag upstream.

## Implementation Notes

- 2026-08-31: `GlossaryResolver` validate schema/ids/policy/conflict, match phrase theo word boundary và ưu tiên source dài hơn để không che entry cụ thể.
- 2026-08-31: regression cover fixture terms, substring boundary, case-sensitive preserve và conflicting entry. Full suite pass 89/89; `compileall` và `git diff --check` pass. Git persistence pending.
