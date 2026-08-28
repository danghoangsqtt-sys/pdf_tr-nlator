# T-102 — Bảo toàn text trong `LTFigure` và vùng figure

## Objective

Ngăn ký tự nằm trong PDF Form XObject / `LTFigure` bị gửi đến translator khi layout model không nhận diện được figure. Text này phải được tái dựng bằng glyph gốc.

## Paths

- `pdf2zh/converter.py`
- `tests/test_figure_protection.py`
- `CHANGELOG.md`
- `.DHSYSTEM/phases/phase-1/tasks/T-102-figure-protection.md`
- `.DHSYSTEM/phases/phase-1/PHASE-STATE.md`
- `.DHSYSTEM/TRACKER.md`
- `.DHSYSTEM/HANDOFF.json`

## File-Level Plan

- `pdf2zh/converter.py`: truyền cờ `force_protected` khi đóng một `LTFigure`; cờ này làm mọi glyph trong figure đi theo nhánh bảo toàn, độc lập với kết quả ONNX layout.
- `tests/test_figure_protection.py`: dùng converter ghi nhận để xác nhận `end_figure` khôi phục page cha và gọi `receive_layout(..., force_protected=True)`.
- `CHANGELOG.md`: ghi nhận hành vi bảo toàn mới ở mục Unreleased.
- Tài liệu trạng thái: ghi task và giới hạn Git persistence đúng thực tế.

## Best-practice checklist

- Giữ API thay đổi ở mức nội bộ và dùng keyword-only flag để tránh gọi nhầm vị trí.
- Không thay đổi logic dịch prose ngoài `LTFigure`.
- Không làm giảm bảo toàn formula/table hiện có.
- Thêm regression test cho hành vi xảy ra khi detector layout bỏ sót figure.

## Verification

```powershell
& .venv\Scripts\python.exe -m unittest discover -s tests -v
```

Kỳ vọng: tất cả test, gồm regression figure mới, pass.

## Implementation Notes

- 2026-08-28: task contract được tạo trước khi sửa mã. Workspace ban đầu không có Git repository/upstream; checkpoint được hoàn tất sau khi remote GitHub được cung cấp.
- 2026-08-28: đã thêm `force_protected` keyword-only flag và regression test. `unittest discover -s tests -v` pass 68 tests.
- 2026-08-28: Git persistence hoàn tất trên `origin/main`; task PASS.
