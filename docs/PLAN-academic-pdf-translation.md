# DEVELOPMENT PLAN — Thực thi dịch PDF học thuật có kiểm soát

**Liên kết đặc tả:** [SPEC-academic-pdf-translation.md](SPEC-academic-pdf-translation.md)  
**Trạng thái:** Baseline execution plan; P0 in progress

## Thứ tự triển khai

| Phase | Mục tiêu | Phụ thuộc | Kết quả |
|---|---|---|---|
| P0 | Khoá baseline và corpus | — | fixture + acceptance baseline |
| P1 | Phân vùng bảo vệ fail-closed | P0 | figure/formula không bị dịch nhầm |
| P2 | Handoff có ngữ cảnh + glossary | P0 | bản dịch academic kiểm soát thuật ngữ |
| P3 | Verifier + quality report | P1, P2 | quyết định done/partial có chứng cứ |
| P4 | CLI/GUI UX | P2, P3 | người dùng chọn đúng mode, không hiểu nhầm |
| P5 | Regression, hiệu năng, tài liệu phát hành | P1–P4 | release candidate |

## Nguyên tắc điều hành

1. **Dependency trước tốc độ:** không triển khai T-103 trở đi trước khi P0 có fixture/expected baseline; T-102 là emergency hardening đã hoàn tất và không thay đổi quy tắc này.
2. **Một task, một contract:** mỗi task phải có `Paths`, file-level plan, verification, rollback/fallback và Definition of Done trong `.DHSYSTEM/phases/.../tasks/` trước khi sửa shipping code.
3. **Fail closed:** unsure region/term/formula dẫn đến preserve + `partial`, không dẫn đến tự dịch.
4. **Durable evidence:** task PASS yêu cầu test pass, working tree sạch, commit đã push `origin/main`, tag checkpoint đã push.

## Dependency graph và milestones

```text
M0 T-000 system baseline
 ├─ M1 T-001 fixture ─ T-002 terminology baseline
 │                    └─ T-101 regions ─ T-103 formula ─ T-104 protection QA
 └─ T-003 delivery ADR ─ T-201 glossary ─ T-202 Handoff v2 ─ T-203 CLI
                                              └─ T-301 verifier ─ T-302 report ─ T-303 render QA
                                                                            └─ M5 T-401/T-402 UX
                                                                                 └─ M6 T-501/T-502/T-503 release
```

| Milestone | Exit criterion | Cannot proceed without |
|---|---|---|
| M0 — System baseline | T-000 PASS; spec/plan traceable | clean Git checkpoint |
| M1 — Corpus baseline | T-001/T-002 PASS | permitted fixture + reviewer expected results |
| M2 — Preservation safety | T-101/T-103/T-104 PASS | structural + visual protection proof |
| M3 — Academic pipeline | T-003/T-201…T-203 PASS | approved delivery policy |
| M4 — Decisionable quality | T-301…T-303 PASS | stable quality report and injected-failure test |
| M5 — User-facing mode | T-401/T-402 PASS | no misleading quality/privacy UX |
| M6 — Release candidate | T-501…T-503 PASS | full matrix + docs/release hygiene |

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
- **Quyết định:** accepted trong [ADR-001](adr/ADR-001-academic-delivery-model.md): local Handoff export/import, không provider, không credential, không OCR cho release này.
- **Nghiệm thu:** T-201/T-202/T-203 có thể triển khai mà không thêm network transport hoặc key handling.

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

## Definition of Done theo loại task

| Loại task | Bằng chứng bắt buộc |
|---|---|
| Core PDF | Unit test cho signal positive/negative; fixture e2e khi có PDF; không làm source PDF thay đổi. |
| Glossary/translator | JSON schema test, placeholder compatibility v1/v2, case/boundary/conflict test. |
| Verifier/report | Test cho `pass`, `warning`, `error`; report schema versioned; critical không thể trả `done`. |
| GUI/CLI | Contract test cho flags/states; copy privacy/quality được review; không lộ secret. |
| Visual QA | Snapshot có manifest, engine/version/threshold ghi nhận, injected corruption bị fail. |
| Documentation/release | Không còn placeholder public, links kiểm tra được, changelog và migration notes cập nhật. |

Mọi task chỉ PASS khi evidence trên đã được chạy, commit vào `main`, push upstream và tag checkpoint đã được push.

## Hàng đợi thực thi chính xác

| Thứ tự | Task | Dependency | Deliverable có thể review |
|---:|---|---|---|
| 0 | T-000 System spec + plan | — | SPEC/PLAN, roadmap state, traceability |
| 1 | T-001 Fixture licensing | T-000 | manifest + redacted/original fixture hợp lệ |
| 2 | T-002 Expected baseline | T-001 | glossary seed + expected/banned assertions |
| 3 | T-003 Delivery ADR | T-000 | policy Handoff/provider/security được duyệt |
| 4 | T-101 Region inventory | T-001 | model + inventory unit tests |
| 5 | T-103 Formula fail-closed | T-101 | formula signals + preserve behavior |
| 6 | T-104 Protection QA | T-101, T-103 | structural/visual regression harness |
| 7 | T-201 Glossary resolver | T-002, T-003 | terminology module/schema |
| 8 | T-202 Handoff v2 | T-201 | contextual JSONL round-trip |
| 9 | T-203 Academic CLI | T-202 | quality flags + safe mode contract |
| 10 | T-301 Verifier | T-104, T-202 | findings/status engine |
| 11 | T-302 Quality report | T-301, T-203 | versioned JSON report + partial status |
| 12 | T-303 Render QA | T-302 | render/diff gate |
| 13 | T-401 GUI lifecycle | T-203, T-302 | Handoff export/import UX |
| 14 | T-402 Consent/copy UX | T-401 | draft/academic disclosure |
| 15 | T-501 CI matrix | T-104, T-303 | Windows Python 3.11/3.12 jobs |
| 16 | T-502 Performance/fallback | T-303 | benchmark + degradation contract |
| 17 | T-503 Release hygiene | T-401, T-402, T-501, T-502 | docs/release candidate |

## Rollback và scope control

- Nếu protected-region code làm mất hình hoặc glyph: revert riêng checkpoint task đó; giữ source/output artifacts và regression fixture để tái hiện.
- Nếu glossary/verifier tạo false positive: hạ finding xuống warning chỉ khi có test chứng minh; không vô hiệu hoá global rule để “qua CI”.
- Nếu provider chưa được duyệt: delivery dừng ở local Handoff; không merge UI/API credential work.
- Nếu fixture không được phép phân phối: chỉ commit generator/manifest/public redacted equivalent, còn original dùng local acceptance run.

## Phân rã đề xuất cho lượt thực thi đầu tiên

T-000 là baseline bắt buộc trước mọi task mới. Lượt kỹ thuật đầu tiên sau đó là **T-001 → T-002 → T-101 → T-103 → T-104**; T-102 đã hoàn tất như emergency hardening. Sau khi M2 pass, tiếp tục **T-003 → T-201 → T-202 → T-203**.
