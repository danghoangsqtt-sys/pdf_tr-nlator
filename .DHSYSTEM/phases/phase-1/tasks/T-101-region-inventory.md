# T-101 — Tạo region inventory

## Objective

Chuẩn hoá các vùng không được dịch thành inventory có evidence. Tích hợp tín hiệu image/vector drawing vào layout mask để text nằm trong vector figure bị preserve ngay cả khi ONNX không nhận ra figure.

## Paths

- `pdf2zh/regions.py`
- `pdf2zh/high_level.py`
- `tests/test_regions.py`
- `CHANGELOG.md`
- `.DHSYSTEM/phases/phase-0/PHASE-STATE.md`
- `.DHSYSTEM/phases/phase-1/PHASE-STATE.md`
- `.DHSYSTEM/phases/phase-1/tasks/T-101-region-inventory.md`
- `.DHSYSTEM/TRACKER.md`
- `.DHSYSTEM/HANDOFF.json`

## File-Level Plan

- `regions.py`: định nghĩa `RegionKind`, immutable `Region`, discovery cho image blocks và vector-drawing clusters, cùng helper lock pixel mask có coordinate scaling/clamping.
- `high_level.py`: gọi inventory sau model layout, lock `FIGURE` regions vào mask; lỗi discovery chỉ log/debug, không ngăn dịch ordinary prose.
- `test_regions.py`: dùng fixture CC0 để chứng minh figure vector được phát hiện, fake image page để kiểm tra image evidence, và numpy mask để kiểm tra mapping/clamp.
- State files: P0 complete, P1/T-101 in progress trước implementation.

## Best-practice checklist

- Chỉ protect vector cluster đủ lớn; bỏ header chrome nhỏ để giảm false positive.
- `Region` dùng PDF page coordinates; mask helper chịu trách nhiệm scale sang pixmap coordinates.
- Không đưa formula heuristic vào task này; T-103 sở hữu formula fail-closed.
- Discovery failure phải fail-open ở level preflight nhưng không được làm hỏng run hiện hữu.

## Verification

```powershell
& .venv\Scripts\python.exe -m unittest tests.test_regions -v
& .venv\Scripts\python.exe -m unittest discover -s tests -q
git diff --check
```

Kỳ vọng: fixture vector bbox được đánh dấu `FIGURE`, image evidence được tạo, mask region bị zero đúng vùng và full suite pass.

## Rollback / fallback

- Nếu detector vector lock prose hợp lệ, tăng ngưỡng cluster hoặc giới hạn evidence; không tắt toàn bộ `LTFigure` protection.
- Nếu PyMuPDF API thiếu, discovery trả empty list và ONNX/LTFigure behavior hiện hữu tiếp tục chạy.

## Implementation Notes

- 2026-08-31: PyMuPDF 1.25.2 preflight: `cluster_drawings()` có sẵn; fixture page 2 trả figure rect `(72, 160, 523, 540)`.
- 2026-08-31: `discover_regions()` nhận diện image và vector-drawing clusters lớn với evidence; `protect_mask()` scale, đảo trục Y và clamp trước khi khóa layout mask.
- 2026-08-31: `tests.test_regions` pass 4/4; full suite pass 80/80; `compileall` và `git diff --check` pass. Git persistence pending.
