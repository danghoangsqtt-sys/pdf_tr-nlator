# PLAN — Thực thi dịch PDF học thuật có kiểm soát

**Liên kết đặc tả:** [SPEC-academic-pdf-translation.md](SPEC-academic-pdf-translation.md)  
**Trạng thái:** Ready for implementation sau khi có fixtures hợp lệ

## Thứ tự triển khai

| Phase | Mục tiêu | Phụ thuộc | Kết quả |
|---|---|---|---|
| P0 | Khoá baseline và corpus | — | fixture + acceptance baseline |
| P1 | Phân vùng bảo vệ fail-closed | P0 | figure/formula không bị dịch nhầm |
| P2 | Handoff có ngữ cảnh + glossary | P0 | bản dịch academic kiểm soát thuật ngữ |
| P3 | Verifier + quality report | P1, P2 | quyết định done/partial có chứng cứ |
| P4 | CLI/GUI UX | P2, P3 | người dùng chọn đúng mode, không hiểu nhầm |
| P5 | Regression, hiệu năng, tài liệu phát hành | P1–P4 | release candidate |

## P0 — Corpus, baseline và quyết định sản phẩm

### T-001 — Thu thập fixture có quyền sử dụng

- **Owner:** QA / Product
- **Đầu ra:** `tests/fixtures/transformer/` (hoặc fixture redacted), manifest source/license/page map.
- **Bao phủ bắt buộc:** title, Google Research, §3.2.1, Hình 3–5, §5.4; ít nhất một figure vector và một formula inline/display.
- **Nghiệm thu:** test mở được fixture, page count/hash source ghi vào manifest; không commit tài liệu không được phép phân phối.

### T-002 — Định nghĩa baseline và lỗi mong đợi

- **Owner:** QA + domain reviewer AI/ML
- **Đầu ra:** `expected-vi.json`, glossary seed, danh sách banned translations.
- **Nghiệm thu:** ít nhất 20 assertion thuật ngữ; có expected cho ensemble, scaled dot-product attention, constituency parsing, sequence transduction, label smoothing và Google Research.

### T-003 — Quyết định delivery academic mode

- **Owner:** Product + Security
- **Quyết định cần chốt:** chỉ Handoff local/export-import hay provider có cấu hình; chính sách dữ liệu, API key và chi phí nếu có provider.
- **Nghiệm thu:** ADR ngắn được duyệt. Nếu chưa chốt, scope P4 giới hạn ở Handoff bundle, không tích hợp key.

## P1 — Bảo vệ figure, scan và formula

### T-101 — Tạo mô hình region inventory

- **Owner:** Core PDF
- **Files dự kiến:** `pdf2zh/regions.py` (mới), `pdf2zh/high_level.py`.
- **Thực hiện:** chuẩn hoá `Region(kind, bbox, confidence, evidence)`; thu image blocks, XObjects, vector drawings, model layout và formula signals.
- **Nghiệm thu:** unit tests chứng minh coordinate conversion chuẩn và evidence không mất khi các detector trùng nhau.

### T-102 — Bảo toàn text trong LTFigure và vùng figure

- **Owner:** Core PDF
- **Files dự kiến:** `pdf2zh/converter.py`, `pdf2zh/pdfinterp.py`, test fixture.
- **Thực hiện:** truyền figure context vào converter; không dispatch text intersect `FIGURE` vào translator kể cả khi ONNX không nhận ra box.
- **Nghiệm thu:** mock translator không thấy string từ figure; visual regression crop figure không có ký tự vỡ.

### T-103 — Formula classifier fail-closed

- **Owner:** Core PDF
- **Files dự kiến:** `pdf2zh/rules.py`, `pdf2zh/regions.py`, `pdf2zh/converter.py`.
- **Thực hiện:** hợp nhất font, Unicode math, layout class, geometry (baseline/size) và conflicting signals; `UNKNOWN` là protected.
- **Nghiệm thu:** các phân số/căn fixture không xuất hiện trong request dịch; formula có confidence thấp làm output `partial` hoặc giữ nguyên.

### T-104 — Kiểm định structural preservation

- **Owner:** QA
- **Files dự kiến:** `tests/test_protected_regions.py`, render helper.
- **Thực hiện:** snapshot region inventory; đối chiếu protected glyph/token và rendered crop.
- **Nghiệm thu:** AC-03/AC-04 pass; threshold visual được ghi rõ theo fixture.

## P2 — Academic translation và terminology

### T-201 — Glossary schema và resolver

- **Owner:** Translation core
- **Files dự kiến:** `pdf2zh/terminology.py` (mới), `terminology/vi-ai-ml.json`, tests.
- **Thực hiện:** load/validate JSON, match phrase có boundary, rule giữ nguyên/dịch cố định, phát hiện conflict.
- **Nghiệm thu:** term lookup không match nhầm substring; test seed glossary pass 100%.

### T-202 — Mở rộng Handoff bundle bằng context

- **Owner:** Translation core
- **Files dự kiến:** `pdf2zh/translator.py`, `scripts/translate_pdf.py`, tests.
- **Thực hiện:** emit schema v2 có `id`, page/bbox/context/glossary IDs; importer vẫn nhận JSONL v1.
- **Nghiệm thu:** v1 rebuild không vỡ; v2 round-trip giữ placeholder; source không bị cache khi miss.

### T-203 — Academic CLI contract

- **Owner:** CLI
- **Files dự kiến:** `scripts/translate_pdf.py`, `README.md`, tests.
- **Thực hiện:** thêm `--quality`, `--glossary`, `--quality-report`; chặn `academic + google` trừ khi có adapter được phê duyệt.
- **Nghiệm thu:** lời gọi sai trả lỗi rõ; Handoff export/import hoạt động end-to-end trên fixture.

## P3 — Verifier và báo cáo

### T-301 — Translation verifier

- **Owner:** Translation core
- **Files dự kiến:** `pdf2zh/quality.py` (mới), tests.
- **Thực hiện:** kiểm placeholder, term bắt buộc/cấm, tên riêng giữ nguyên, coverage và protected-region inventory.
- **Nghiệm thu:** từng rule có unit test `pass`, `warning`, `error`; lỗi critical chặn trạng thái `done`.

### T-302 — Quality report và trạng thái partial

- **Owner:** CLI + Core PDF
- **Files dự kiến:** `scripts/translate_pdf.py`, `app/gui.py`, tests.
- **Thực hiện:** xuất JSON schema versioned; kết hợp failure network với quality findings; link report từ output.
- **Nghiệm thu:** report luôn có file/page/bbox/rule/severity; app không báo thành công hoàn toàn khi report critical.

### T-303 — Render QA có mục tiêu

- **Owner:** QA
- **Files dự kiến:** `tests/visual/`, helper render.
- **Thực hiện:** chỉ render trang warning/protected, check blank/missing glyph/overlap và fixture crop diff.
- **Nghiệm thu:** một injected corruption bị phát hiện; các fixture hợp lệ pass ổn định trên CI Windows.

## P4 — Trải nghiệm người dùng

### T-401 — GUI mode và handoff lifecycle

- **Owner:** Desktop app
- **Files dự kiến:** `app/gui.py` và assets/docs liên quan.
- **Thực hiện:** chọn `Bản nháp (Google)` / `Học thuật (Handoff)`, glossary picker, export/import bundle, badges partial/report.
- **Nghiệm thu:** GUI không gọi Google khi academic; người dùng thấy rõ yêu cầu import bản dịch trước khi rebuild.

### T-402 — Cảnh báo dữ liệu và copy UX

- **Owner:** Product/UX
- **Thực hiện:** cảnh báo trước lúc gửi Google; mô tả giới hạn OCR/figure; phân biệt done vs partial.
- **Nghiệm thu:** test GUI hoặc review checklist xác nhận không còn tuyên bố ngầm “dịch chuẩn học thuật”.

## P5 — Hoàn thiện release

### T-501 — CI và regression matrix

- **Owner:** QA/DevOps
- **Thực hiện:** unit + fixture e2e + visual checks trên Windows/Python 3.11 và 3.12; lưu report khi fail.
- **Nghiệm thu:** 100% existing tests + test mới pass; lỗi reference có regression test.

### T-502 — Hiệu năng và fallback

- **Owner:** Core PDF
- **Thực hiện:** benchmark draft baseline; giới hạn render QA; kiểm memory tài liệu dài; test when detector/model unavailable.
- **Nghiệm thu:** draft không chậm quá 15%; academic fail-safe không tạo PDF hỏng khi preflight lỗi.

### T-503 — Tài liệu và release hygiene

- **Owner:** Maintainer
- **Thực hiện:** sửa README encoding/link `your-username`, cập nhật SKILL và preservation contract, release note/migration guide.
- **Nghiệm thu:** không còn placeholder public; docs phân biệt draft/academic/OCR; link cập nhật có repository thật.

## Cổng chất lượng giữa các phase

1. Không bắt đầu P1 nếu chưa có fixture hoặc fixture redacted tương đương.
2. Không bắt đầu P4 provider integration khi T-003 chưa được duyệt.
3. Không phát hành nếu AC-01 đến AC-06 chưa pass.
4. Bất kỳ region không chắc chắn nào phải giữ nguyên và xuất hiện trong quality report; không được tự dịch để “tăng coverage”.

## Phân rã đề xuất cho lượt thực thi đầu tiên

Lượt đầu nên chỉ thực hiện **T-001, T-002, T-101 và T-102**. Đây là lát cắt nhỏ nhất để tái hiện và ngăn lỗi chữ vỡ trong hình mà chưa cần chọn provider dịch. Sau khi crop figure pass, tiếp tục **T-103 → T-104 → T-201 → T-202**.

