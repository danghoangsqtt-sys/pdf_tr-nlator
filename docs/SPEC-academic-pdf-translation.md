# SYSTEM SPEC — Dịch PDF học thuật có kiểm soát chất lượng

**Trạng thái:** Baseline for implementation
**Ngày cập nhật:** 2026-08-28
**Phạm vi phát hành:** phiên bản kế tiếp của `dh-pdf-trans`

## 1. Vấn đề và mục tiêu

Pipeline hiện tại tái dựng bố cục PDF rồi gửi từng đoạn văn rời rạc tới Google Translate. Điều này không có ngữ cảnh tài liệu, glossary, cơ chế giữ tên riêng, hay cổng kiểm tra hậu dịch. Vì thế các thuật ngữ như *ensemble*, *constituency parsing*, *dot product* và *label smoothing* có thể bị dịch theo nghĩa phổ thông.

PDF không phải dữ liệu văn bản tuần tự đáng tin cậy: thứ tự glyph nội bộ có thể khác thứ tự nhìn thấy. Tài liệu PyMuPDF cũng nêu rõ thứ tự trích xuất phụ thuộc vào cách PDF được tạo; `rawdict` cung cấp ký tự và bounding box để kiểm tra chi tiết. Vì vậy không được đưa chữ trong hình vector hoặc nội dung toán học chưa nhận diện chắc chắn vào translator.

Mục tiêu:

1. Có luồng dịch “Học thuật / Kỹ thuật” bảo toàn thuật ngữ và tên riêng theo glossary.
2. Không làm hỏng công thức hoặc text trong hình: khi không chắc chắn, giữ nguyên và báo `partial`, thay vì tự dịch/tái dựng sai.
3. Cung cấp báo cáo kiểm định có thể hành động trước khi giao PDF.
4. Có corpus regression chứa các corner case Transformer/AI.

## 2. Phạm vi và không thuộc phạm vi

### In scope

- Glossary theo dự án/ngôn ngữ, ưu tiên thuật ngữ AI/ML tiếng Anh → tiếng Việt.
- Handoff theo segment có ngữ cảnh, cùng kiểm tra glossary, placeholder và tên riêng.
- Phân vùng bảo vệ dự phòng cho bitmap, vector graphics, Form XObject, table và formula.
- Quality report theo trang/region; kết quả `done`, `partial`, hoặc `failed`.
- Regression corpus và kiểm thử text/visual có thể tự động chạy.

### Out of scope của release này

- OCR hoặc dịch text nằm bên trong biểu đồ/ảnh. Nội dung đó được giữ nguyên, không bị làm hỏng.
- Chứng minh đúng đắn toán học bằng hiểu biết ngữ nghĩa.
- Hứa hẹn bản dịch xuất bản được mà không có review chuyên gia.
- Tích hợp sẵn API LLM thương mại vào desktop app trước khi có quyết định về provider, chi phí, lưu khóa và chính sách dữ liệu.

## 3. Các quyết định kiến trúc

### 3.1 Hai chế độ chất lượng

| Chế độ | Mục đích | Translator | Cam kết |
|---|---|---|---|
| `draft` | đọc nhanh, không chuyên ngành | Google hiện hữu | chỉ best effort |
| `academic` | tài liệu cần đúng thuật ngữ | Handoff + glossary + verifier | không tự phát hành nếu phát hiện rủi ro |

`draft` thay thế cách gọi ngầm là chế độ mặc định “đủ tốt”. `academic` ban đầu phải chạy được từ CLI bằng export/import JSONL. GUI trong mốc đầu chỉ được phép hỗ trợ export, import và hiển thị trạng thái; không được giả vờ là có dịch AI học thuật nếu chưa cấu hình provider.

### 3.2 Pipeline academic

```text
PDF nguồn
  → preflight / phân vùng
  → segment an toàn + context + placeholder
  → Handoff JSONL + glossary
  → import bản dịch
  → verifier (formula, protected region, terminology, text coverage)
  → dựng PDF
  → render / kiểm tra trực quan có mục tiêu
  → PDF + quality-report.json / partial
```

Chỉ vùng `PROSE_SAFE` mới được dịch. Các vùng `FORMULA`, `FIGURE`, `TABLE`, `SCAN`, `UNKNOWN` được giữ nguyên. `UNKNOWN` là quyết định bảo thủ, không phải lỗi im lặng.

### 3.3 Phân vùng bảo vệ

Nguồn tín hiệu, theo thứ tự ưu tiên:

1. Cấu trúc PDF: `LTFigure`, image blocks, Form XObject, font và glyph từ pdfminer.
2. PyMuPDF: `get_text("rawdict")` để lấy ký tự/tọa độ; `get_drawings()` hoặc `cluster_drawings()` cho vector graphics; image/xobject bounding boxes.
3. Model layout ONNX hiện có.
4. Heuristic dự phòng: ký tự toán học, font Math/TeX/Mono, superscript/subscript, baseline không đồng nhất, hoặc text chồng vùng vector.

Một vùng bị bất kỳ nguồn tin cậy cao nào đánh dấu là figure/formula phải bị khóa. Nếu các nguồn mâu thuẫn, chọn khóa vùng và ghi lý do vào report.

### 3.4 Contract dữ liệu

`segments.jsonl` trong academic mode được mở rộng nhưng vẫn tương thích ngược:

```json
{
  "id": "p03-b07-s02",
  "src": "Scaled Dot-Product Attention <b0></b0>",
  "dst": "Cơ chế Attention tích vô hướng có tỷ lệ <b0></b0>",
  "page": 3,
  "bbox": [72.1, 120.0, 483.0, 144.0],
  "context_before": "…",
  "context_after": "…",
  "glossary_ids": ["ml.scaled_dot_product_attention"],
  "protected_placeholders": ["<b0>", "</b0>"]
}
```

- `src` và cặp placeholder phải khớp tuyệt đối như contract hiện hữu.
- `dst` chỉ được nhận nếu verifier pass.
- `id` là ổn định trong cùng một lần trích xuất; lookup vẫn dùng `src` để duy trì dữ liệu JSONL cũ.

Glossary là JSON versioned, ví dụ `terminology/vi-ai-ml.json`:

```json
{
  "schema_version": 1,
  "source": "en",
  "target": "vi",
  "entries": [
    {"id": "ml.ensemble", "source": "ensemble model", "target": "mô hình tổ hợp", "case_sensitive": false},
    {"id": "ml.dot_product", "source": "dot product", "target": "tích vô hướng", "case_sensitive": false},
    {"id": "nlp.constituency_parsing", "source": "constituency parsing", "target": "phân tích cú pháp thành phần", "case_sensitive": false},
    {"id": "org.google_research", "source": "Google Research", "target": "Google Research", "case_sensitive": true}
  ]
}
```

## 4. Functional requirements

### FR-01 — Phân loại và bảo toàn

- Hệ thống phải tạo inventory vùng cho mọi trang trước khi dịch.
- Mọi text trong `LTFigure` hoặc intersect vùng vector/bitmap được phân loại `FIGURE` trừ khi người dùng chọn chức năng dịch hình trong tương lai.
- Formula từ layout model, font, ký tự hoặc geometry phải được phân loại `FORMULA`.
- Vùng không đủ tự tin phải là `UNKNOWN` và không gửi cho engine dịch.

### FR-02 — Dịch theo thuật ngữ

- Academic mode phải load glossary tuỳ chọn; nếu không có, phải cảnh báo rõ rằng kiểm định thuật ngữ bị giới hạn.
- Glossary có thể yêu cầu dịch cố định hoặc giữ nguyên tên riêng.
- Handoff bundle phải mang context trang lân cận và glossary IDs liên quan.
- `draft` không được gắn nhãn “chính xác học thuật”.

### FR-03 — Verifier và trạng thái

- Placeholder phải có cùng thứ tự, số lượng và ID giữa `src`/`dst`.
- Verifier phải phát hiện term cấm/missing theo glossary và vùng protected bị thay đổi.
- Nếu phát hiện nghiêm trọng, không tạo output “done”; tạo `partial` kèm report.
- Report phải có page, bbox, rule ID, severity, nguồn chứng cứ và hướng xử lý.

### FR-04 — Kiểm tra đầu ra

- So sánh page count và tính tồn tại của source/output như hiện tại.
- Render các trang có region protected hoặc warning; phát hiện blank page, missing glyph, clipping và overlap.
- Figure/formula source và output phải qua kiểm tra visual hoặc structural equivalence đã định nghĩa cho fixture.

### FR-05 — UI/CLI

- CLI bổ sung `--quality draft|academic`, `--glossary`, `--quality-report`.
- Giữ `--engine handoff` tương thích; `--quality academic` ngầm đòi Handoff hoặc adapter đã được cấu hình.
- GUI phải hiển thị mode, glossary đang dùng, số region giữ nguyên và kết quả partial; không đưa API key vào file log.

## 5. Non-functional requirements

- Source PDF bất biến; output và report đặt ở thư mục đích.
- Không gửi nội dung ra ngoài trong academic Handoff export/import.
- Quyết định bảo toàn có tính xác định cho cùng input/model/config.
- Không làm chậm draft quá 15% trên corpus baseline; academic có thể chậm hơn do preflight/render/verifier.
- Không ghi cache kết quả `UNKNOWN`, `partial`, hoặc handoff miss thành bản dịch hợp lệ.

## 6. Tiêu chí nghiệm thu

| Mã | Tiêu chí |
|---|---|
| AC-01 | Corpus Transformer có ít nhất 20 term AI/ML; academic mode đạt 100% term glossary bắt buộc. |
| AC-02 | `Attention Is All You Need`, `Google Research` và thuật ngữ được đánh dấu giữ nguyên không bị dịch literal. |
| AC-03 | 100% formula region đã nhận diện giữ nguyên token/glyph theo structural test; sai khác phải tạo `partial`. |
| AC-04 | Text trong vector figures của fixtures không bị gửi tới translator; crop figure đạt ngưỡng visual regression đã chốt. |
| AC-05 | Đầu ra có cảnh báo phải có `quality-report.json` chứa rule, page và bbox. |
| AC-06 | Toàn bộ test hiện hữu và bộ regression mới pass trong CI. |

## 7. Khả thi, rủi ro và quyết định mở

| Hạng mục | Khả thi | Lý do / giới hạn |
|---|---|---|
| Glossary + verifier | Cao | Pipeline Handoff, JSONL và placeholder đã tồn tại; cần mở rộng schema và test. |
| Export/import academic qua CLI | Cao | `HandoffTranslator` hiện đã export missing segments; cần thêm context/report. |
| Chặn text trong vector figure | Trung bình-cao | Có `LTFigure`, bbox images và PyMuPDF vector drawing APIs; cần fixtures vì figure có nhiều dạng PDF. |
| Bảo toàn formula tốt hơn | Trung bình | Cần hợp nhất font/layout/geometry; có thể bảo toàn an toàn nhưng không thể hiểu toàn bộ công thức lỗi font. |
| Visual QA tự động | Trung bình | Render/diff tốt để bắt hồi quy nhưng cần mask/threshold tránh false positive do reflow. |
| Academic mode end-to-end trong GUI | Trung bình | Cần quyết định provider/agent credential; mốc đầu chỉ làm handoff bundle là khả thi và an toàn. |
| OCR/dịch chữ trong hình | Thấp cho release này | Cần engine OCR, language model, redaction/re-render và QA riêng; không nên gộp vào sửa lỗi hiện tại. |

Rủi ro lớn nhất là không có hai PDF gốc/đích làm fixture tái hiện. Trước khi merge bất kỳ thay đổi nào, phải có bản được phép lưu trong test (hoặc trang đã redacted nhưng giữ nguyên cấu trúc glyph/hình/công thức).

## 8. Nguồn kỹ thuật đã đối chiếu

- [PyMuPDF: text extraction và rawdict](https://pymupdf.readthedocs.io/en/latest/app1.html) — cấu trúc block/line/span và ký tự theo toạ độ.
- [PyMuPDF: Page API](https://pymupdf.readthedocs.io/en/latest/page.html) — `get_drawings`, `cluster_drawings`, image/XObject metadata.
- [PyMuPDF FAQ](https://pymupdf.readthedocs.io/en/latest/faq/index.html) — thứ tự text có thể không theo thứ tự hiển thị; không thể tin plain extraction cho figure phức tạp.

## 9. Bối cảnh hệ thống và actors

| Actor | Mục tiêu | Quyền / giới hạn |
|---|---|---|
| Người dùng desktop | Dịch PDF và lấy output an toàn | Chọn `draft` hoặc export/import academic; không sửa source PDF. |
| Chuyên gia / agent dịch | Dịch Handoff bundle theo context và glossary | Chỉ điền `dst`; không thay `src`, ID hoặc placeholder. |
| Core PDF | Phân vùng, dịch/rebuild và bảo toàn layout | Không tự dịch protected/unknown region. |
| Quality verifier | Quyết định `done`, `partial`, `failed` bằng rule xác định | Không tự “sửa” bản dịch có lỗi nghĩa. |
| Maintainer | Cập nhật glossary, fixture và release | Chỉ merge khi release gate pass. |

### System boundary

```text
Local PDF ──► preflight ──► segmenter ──► draft translator OR handoff bundle
    ▲             │              │                       │
    │             ▼              ▼                       ▼
 output + report ◄── rebuilder ◄── verifier ◄──── imported translations
```

Source PDF, glossary và Handoff JSONL là dữ liệu local. Theo [ADR-001](adr/ADR-001-academic-delivery-model.md), `academic` dùng local Handoff export/import và không gửi nội dung ra mạng. Chỉ `draft` được phép gọi Google Translate.

## 10. Module boundaries và interface

| Module | Trách nhiệm | Input | Output | Invariant |
|---|---|---|---|---|
| `scripts/translate_pdf.py` | CLI contract, path safety, orchestration | PDF + options | PDF/result/report | Không overwrite khi chưa có uỷ quyền. |
| `pdf2zh.high_level` | Render/layout pass và PDF stream patch | PDF bytes + model | translated streams | Giữ page count/canvas. |
| `pdf2zh.converter` | Segment prose, tái dựng glyph/protected region | layout + LT objects | PDF operators | Không dispatch protected glyph cho translator. |
| `pdf2zh.rules` / region inventory | Phân loại formula/figure/table/unknown | font, glyph, bbox, model signals | region decision + evidence | Khi conflict, chọn bảo toàn. |
| `pdf2zh.translator` | Draft/Handoff lookup, placeholder safety | safe segment | translated segment hoặc original | Handoff miss không được cache là bản dịch. |
| terminology resolver (P2) | Ánh xạ glossary và named-entity rule | source segment + glossary | term constraints/findings | Không match substring sai boundary. |
| quality verifier (P3) | Validate và tạo quality report | source/output inventory + translations | findings + final status | Critical finding không thể là `done`. |
| `app.gui` | UX, consent, lifecycle file | user action + result | UI status/log link | Không tuyên bố academic nếu chỉ dùng Google. |

## 11. Lifecycle, state machine và failure handling

### 11.1 Document state

```text
queued → preflight → translating → verifying → done
                    │                ├──────→ partial
                    └────────────────┴──────→ failed
```

- `done`: mọi hard rule pass; output và report (nếu có) được ghi thành công.
- `partial`: output an toàn tồn tại nhưng có region giữ nguyên, segment miss, hoặc quality warning/error cần review.
- `failed`: không thể đọc/dựng/xác minh output; không được đưa path output như một kết quả thành công.

### 11.2 Error taxonomy

| Code family | Ví dụ | Final state | Hành động người dùng |
|---|---|---|---|
| `INPUT_*` | PDF hỏng, password, path không hợp lệ | failed | Chọn PDF hợp lệ hoặc mở khoá trước. |
| `LAYOUT_*` | model unavailable, coordinate conflict | partial/failed | Giữ vùng nghi ngờ; gửi diagnostic. |
| `PROTECTED_*` | figure/formula bị thay đổi | partial | Review report/page/bbox; không tự export published copy. |
| `TERM_*` | glossary required term missing | partial | Sửa JSONL hoặc glossary rồi rebuild. |
| `TRANSLATION_*` | network/provider/Handoff miss | partial | Retry hoặc hoàn thiện bundle. |
| `OUTPUT_*` | write/render/subset font error | failed | Giữ source, kiểm tra quyền ghi/font/log. |

Mọi finding phải có `rule_id`, `severity`, `page` (nếu biết), `bbox` (nếu biết), `evidence`, `suggested_action` và `source_version`.

## 12. Data contracts và compatibility

### 12.1 Region inventory (P1)

```json
{
  "schema_version": 1,
  "page": 3,
  "regions": [
    {
      "kind": "FIGURE",
      "bbox": [72.0, 96.0, 522.0, 406.0],
      "confidence": "high",
      "evidence": ["ltfigure", "vector-drawing"],
      "dispatch": "preserve"
    }
  ]
}
```

`kind ∈ {PROSE_SAFE, FORMULA, FIGURE, TABLE, SCAN, UNKNOWN}`. `dispatch` chỉ có `translate` với `PROSE_SAFE`; tất cả kind còn lại mặc định `preserve`.

### 12.2 Quality report (P3)

```json
{
  "schema_version": 1,
  "status": "partial",
  "source": "paper.pdf",
  "output": "paper-vi.pdf",
  "summary": {"critical": 0, "error": 1, "warning": 3},
  "findings": []
}
```

- JSONL v1 `{"src", "dst"}` phải tiếp tục rebuild được.
- Schema v2 chỉ thêm field; parser phải bỏ qua field chưa biết để tương thích forward.
- Không log API key, nội dung PDF, hoặc full `dst` trong diagnostic mặc định.

## 13. Security, privacy và vận hành

- `draft`: trước khi request đầu tiên, UI/CLI phải nói rõ nội dung segment được gửi tới Google.
- `academic` Handoff: không network, không persistent cache cho miss/unknown; bundle nằm trong output directory do người dùng chọn.
- Provider tương lai: token chỉ đọc từ OS secret store hoặc biến môi trường ở runtime; cấm ghi vào config, JSONL, report hay `pdf-translate.log`.
- Diagnostic mặc định chỉ chứa fingerprint/source basename/page/bbox/rule. Full segment chỉ bật bằng explicit debug option.
- Dữ liệu temporary phải bị xoá khi success/fail, trừ artifacts Handoff/report mà người dùng yêu cầu giữ.

## 14. Observability và quality gates

Mỗi run cần log có cấu trúc tối thiểu: `run_id`, engine/quality mode, source hash, page count, protected-region counts, safe-segment count, misses, final status và elapsed time.

| Gate | Khi chạy | Pass condition |
|---|---|---|
| G1 input/preflight | trước translator | source hợp lệ, model/config sẵn sàng, region inventory hoàn chỉnh hoặc degraded có report. |
| G2 translation contract | import Handoff | placeholder/JSON schema hợp lệ, glossary mandatory terms pass. |
| G3 rebuild integrity | sau rebuild | source/output page count bằng nhau, output mở/render được. |
| G4 protected integrity | sau rebuild | protected finding không có critical; fixture visual/structural checks pass. |
| G5 release | CI/release candidate | AC-01…AC-06 pass trên matrix đã định nghĩa. |

## 15. Requirement traceability và quyết định mở

| Requirement | Delivery task | Verification |
|---|---|---|
| FR-01 protected region | T-101…T-104 | region + visual regression tests |
| FR-02 terminology | T-201…T-203 | glossary resolver/Handoff e2e |
| FR-03 verifier/report | T-301…T-302 | unit schema/rule tests |
| FR-04 render check | T-303 | injected-corruption visual test |
| FR-05 UX/CLI | T-203, T-401, T-402 | CLI/GUI contract tests |
| NFR privacy/performance | T-003, T-502 | security checklist + benchmark |

Open decisions are explicit blockers, not implementation assumptions:

1. **ADR-001 / T-003:** accepted - local Handoff is the current academic delivery model; any provider/OCR proposal needs a successor ADR.
2. **ADR-002 / T-001:** resolved - `academic-v1` is a self-authored CC0 fixture; future third-party fixtures still need redistribution review.
3. **ADR-003 / T-303:** rendering engine, visual threshold and CI artifact retention.
