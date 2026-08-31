# T-002 — Định nghĩa baseline thuật ngữ và expected results

## Objective

Thiết lập corpus kỳ vọng tiếng Việt cho fixture CC0 và glossary seed AI/ML, gồm bản dịch bắt buộc, tên riêng giữ nguyên và các bản dịch cấm. Dữ liệu này là oracle cho terminology resolver/verifier ở các phase sau.

## Paths

- `terminology/vi-ai-ml.json`
- `tests/fixtures/academic-v1/expected-vi.json`
- `tests/fixtures/academic-v1/banned-translations.json`
- `tests/test_terminology_baseline.py`
- `.DHSYSTEM/phases/phase-0/PHASE-STATE.md`
- `.DHSYSTEM/phases/phase-0/tasks/T-002-terminology-baseline.md`
- `.DHSYSTEM/TRACKER.md`
- `.DHSYSTEM/HANDOFF.json`

## File-Level Plan

- `vi-ai-ml.json`: glossary schema v1, 20+ entries, exact/insensitive casing policy, required target text and source category.
- `expected-vi.json`: expected translations for every term in `academic-v1/manifest.json`, plus representative sentence-level expectations.
- `banned-translations.json`: known literal/mistranslated variants associated with glossary ID; only complete prohibited phrases, never broad single-word bans.
- `test_terminology_baseline.py`: validate schema, uniqueness, fixture coverage, expected target consistency, and that every ban has a known source entry.
- State files: ghi task lifecycle và checkpoint evidence.

## Best-practice checklist

- Giữ nguyên tên tổ chức/title được marker `preserve`.
- Dùng thuật ngữ toán học chuẩn "tích vô hướng", không dùng literal "sản phẩm chấm".
- Mỗi ban phải đủ cụ thể để future verifier không tạo false positive cho văn xuôi hợp lệ.
- Không cài terminology resolver trong task này; đây là data contract/quality baseline.

## Verification

```powershell
& .venv\Scripts\python.exe -m unittest tests.test_terminology_baseline -v
& .venv\Scripts\python.exe -m unittest discover -s tests -q
git diff --check
```

Kỳ vọng: glossary có ít nhất 20 entries, bao phủ toàn bộ 7 fixture terms, mọi expected/banned reference hợp lệ.

## Rollback / fallback

- Nếu reviewer phản đối một cách dịch, sửa data entry và expected fixture; không thêm special-case vào core translator.
- Nếu một ban quá rộng, xoá hoặc thu hẹp phrase thay vì hạ quality rule toàn cục.

## Implementation Notes

- 2026-08-31: task contract tạo trước khi thêm data baseline.
- 2026-08-31: thêm glossary 23 entries, 7 fixture expectations và 8 banned-translation groups. `unittest discover -s tests -q` pass 76 tests; task chờ checkpoint Git trước khi PASS.
