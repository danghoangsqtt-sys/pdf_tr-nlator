# T-103 — Formula/scan classifier fail-closed

## Objective

Phân loại các vùng formula và scan từ dữ liệu PDF gốc trước khi converter gửi
glyph vào translator. Tín hiệu formula không chắc chắn phải được preserve như
`UNKNOWN`; một ảnh phủ phần lớn trang được phân loại `SCAN` và giữ nguyên vùng
ảnh/OCR layer thay vì cố dịch.

## Paths

- `pdf2zh/regions.py`
- `pdf2zh/high_level.py`
- `tests/test_regions.py`
- `.DHSYSTEM/phases/phase-1/PHASE-STATE.md`
- `.DHSYSTEM/phases/phase-1/tasks/T-103-formula-scan-classifier.md`
- `.DHSYSTEM/TRACKER.md`
- `.DHSYSTEM/HANDOFF.json`
- `CHANGELOG.md`

## File-Level Plan

- `regions.py`: thêm formula signals từ font, Unicode toán học, syntax và geometry line; phân loại `FORMULA` khi bằng chứng mạnh, `UNKNOWN` khi chỉ có syntax/geometry. Tạo `SCAN` khi image phủ quá nửa page và đưa mọi kind bảo vệ vào mask mặc định.
- `high_level.py`: tiếp tục dùng inventory làm single source of truth; log rõ formula/scan regions bị khóa.
- `test_regions.py`: dùng academic fixture chứng minh hai dòng Courier không còn là prose; kiểm Unicode math, unknown fail-closed, scan và mask protection.
- State/changelog: ghi evidence, verification và checkpoint sau khi pass.

## Best-practice checklist

- Không dùng OCR hoặc thêm network/provider trong task này.
- Không suy đoán formula bằng một ký tự thường đơn lẻ; `UNKNOWN` chỉ sinh khi syntax/geometry vượt ngưỡng, sau đó vẫn phải preserve.
- Tọa độ remain in PyMuPDF page space cho đến `protect_mask`.
- Không thay đổi source PDF; mọi region discovery lỗi phải trả danh sách an toàn và giữ behavior hiện có.

## Verification

```powershell
& .venv\Scripts\python.exe -m unittest tests.test_regions -v
& .venv\Scripts\python.exe -m unittest discover -s tests -q
git diff --check
```

Kỳ vọng: formula fixture nhận `FORMULA`; formula không đủ bằng chứng nhận `UNKNOWN` và mask vẫn bị khoá; scan image nhận `SCAN`; full suite pass.

## Rollback / fallback

- Nếu heuristic bảo vệ prose hợp lệ, siết syntax/geometry threshold thay vì bỏ `UNKNOWN` fail-closed.
- Nếu PyMuPDF text metadata thiếu hoặc lỗi, không tạo formula region và để các cơ chế `vflag`/layout existing tiếp tục bảo vệ; không tự dịch một vùng scan.

## Definition of Done

- Formula/scan/unknown regions có evidence, unit tests positive và negative.
- Formula/unknown/scan được khóa trong layout mask.
- Tests, syntax, diff check pass; checkpoint được push và tag upstream.

## Implementation Notes

- 2026-08-31: `discover_regions()` bổ sung `FORMULA` từ formula font/Unicode math, `UNKNOWN` cho syntax+geometry mơ hồ, và `SCAN` cho image coverage lớn hơn 50% page.
- 2026-08-31: `protect_mask()` mặc định khóa `FIGURE`, `FORMULA`, `SCAN` và `UNKNOWN`; không có OCR/provider/network mới.
- 2026-08-31: `tests.test_regions` pass 7/7; full suite pass 83/83; `compileall` và `git diff --check` pass. Git persistence pending.
