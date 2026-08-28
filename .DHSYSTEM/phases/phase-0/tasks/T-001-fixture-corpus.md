# T-001 — Thu thập fixture có quyền sử dụng

## Objective

Tạo PDF fixture học thuật tự tạo, có thể phân phối công khai, để tái hiện các kiểu nội dung gây lỗi: terminology AI/ML, formula inline/display và vector figure có text. Ghi manifest gồm license, page map và SHA-256.

## Paths

- `tests/fixtures/academic-v1/build_fixture.py`
- `tests/fixtures/academic-v1/academic-ml-source.pdf`
- `tests/fixtures/academic-v1/manifest.json`
- `tests/fixtures/academic-v1/README.md`
- `tests/test_academic_fixture.py`
- `.DHSYSTEM/phases/phase-0/PHASE-STATE.md`
- `.DHSYSTEM/phases/phase-0/tasks/T-001-fixture-corpus.md`
- `.DHSYSTEM/TRACKER.md`
- `.DHSYSTEM/HANDOFF.json`

## File-Level Plan

- `build_fixture.py`: tạo deterministic PDF bằng dependency runtime PyMuPDF; một trang chứa prose/term/formula, một trang chứa vector attention visualisation có label English.
- `academic-ml-source.pdf`: artifact generated được commit làm source regression.
- `manifest.json`: schema version, creator, CC0 declaration, page map, expected regions và SHA-256.
- `README.md`: mục đích, quyền sử dụng, cách regenerate/verify và các giới hạn của fixture tổng hợp.
- `test_academic_fixture.py`: kiểm tra manifest, SHA-256, page count, term coverage, formula font và vector drawing signal từ artifact đã commit.
- State files: theo dõi task và checkpoint sau khi verified/pushed.

## Best-practice checklist

- Không sao chép text, figure hoặc công thức từ paper có bản quyền.
- Chỉ dùng ASCII hyphen trong PDF labels; không nhúng secret hay dữ liệu cá nhân.
- Fixture cần deterministic để SHA-256 có thể kiểm chứng sau cùng một môi trường; nếu metadata PDF làm hash không ổn định, manifest ghi rõ generator/version và structural checks.
- Kiểm tra trực quan bằng render PNG, không chỉ dựa vào text extraction.

## Verification

```powershell
& .venv\Scripts\python.exe tests\fixtures\academic-v1\build_fixture.py
& .venv\Scripts\python.exe -c "import hashlib; from pathlib import Path; print(hashlib.sha256(Path('tests/fixtures/academic-v1/academic-ml-source.pdf').read_bytes()).hexdigest())"
pdfinfo tests\fixtures\academic-v1\academic-ml-source.pdf
pdftoppm -png -r 144 tests\fixtures\academic-v1\academic-ml-source.pdf tmp\fixture-preview
```

Kỳ vọng: PDF 2 trang, SHA-256 khớp manifest và hai PNG dễ đọc, không clip/chồng chữ.

## Implementation Notes

- 2026-08-28: task contract tạo trước artifact authoring.
- 2026-08-28: tạo fixture CC0 hai trang bằng PyMuPDF, manifest SHA-256 `d638e6ab0684ed773abfeb00b98e5687686b76e7a36e10ecff6f146d96031c6f`, và 4 integrity tests. Render PyMuPDF đã được kiểm tra trực quan; Poppler không có trong environment.
- 2026-08-28: `unittest discover -s tests -q` pass 72 tests; task đang chờ checkpoint Git trước khi được đánh dấu PASS.
