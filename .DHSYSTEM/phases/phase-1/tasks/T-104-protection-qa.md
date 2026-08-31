# T-104 — Kiểm định structural preservation

## Objective

Đóng M2 bằng regression harness có evidence cho inventory và layout mask: mọi
glyph nằm trong figure/formula protected region của academic fixture phải rơi
vào pixel mask bằng 0. Render crop phải còn content rõ ràng để fixture không
trở thành baseline rỗng hoặc lỗi layout.

## Paths

- `tests/fixtures/academic-v1/protected-regions.json`
- `tests/test_protected_regions.py`
- `.DHSYSTEM/phases/phase-1/PHASE-STATE.md`
- `.DHSYSTEM/phases/phase-1/tasks/T-104-protection-qa.md`
- `.DHSYSTEM/TRACKER.md`
- `.DHSYSTEM/HANDOFF.json`
- `CHANGELOG.md`

## File-Level Plan

- `protected-regions.json`: snapshot versioned của kind/bbox/evidence cho hai
  trang fixture; tọa độ làm tròn 0.1pt để không phụ thuộc float noise.
- `test_protected_regions.py`: reconstruct layout mask 1:1 với page render,
  assert snapshot, assert protected glyph center không còn route vào prose,
  và assert rendered crop formula/figure có ink hợp lệ.
- State/changelog: ghi visual/structural evidence và checkpoint upstream.

## Best-practice checklist

- Không chạy dịch network hay tạo output PDF giả trong QA.
- Dùng source fixture hash đã bị khóa; snapshot phát hiện thay đổi semantic của
  detector, còn crop ink check phát hiện fixture/render baseline rỗng.
- Assertion glyph phải dùng coordinate conversion giống production
  `protect_mask`, không sao chép một phép biến đổi thứ hai.
- Test chỉ khẳng định preservation, không đánh giá chất lượng bản dịch.

## Verification

```powershell
& .venv\Scripts\python.exe -m unittest tests.test_protected_regions -v
& .venv\Scripts\python.exe -m unittest discover -s tests -q
git diff --check
```

Kỳ vọng: snapshot đủ 5 regions; mọi glyph ở formula/vector regions bị mask;
hai crop render có ink và full suite pass.

## Rollback / fallback

- Nếu snapshot thay đổi do detector được cải thiện có chủ đích, review bbox và
  evidence trước khi update snapshot; không regenerate im lặng.
- Nếu renderer khác biệt nhỏ, chỉ dùng pixel test để phát hiện crop trắng/rỗng,
  không dùng threshold diff nhạy với anti-aliasing.

## Definition of Done

- Structural proof và render baseline tests pass cho formula/figure fixture.
- M2/P1 state cập nhật đúng; checkpoint được push và tag upstream.

## Implementation Notes

- 2026-08-31: snapshot v1 ghi 5 regions reviewed: 2 vector `FIGURE` và 3 `FORMULA` từ fixture hai trang.
- 2026-08-31: structural test chứng minh mọi glyph có tâm nằm trong region bảo vệ map vào layout mask value 0; render crop formula/figure có ink ratio vượt ngưỡng 1%.
- 2026-08-31: visual review trực tiếp xác nhận formula, labels Query/Key/Value, annotation và trục biểu đồ rõ ràng. Full suite pass 86/86; `compileall` và `git diff --check` pass. Implementation pushed to `origin/main` at `b0dd19d`.
