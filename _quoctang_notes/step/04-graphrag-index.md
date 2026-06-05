# Lệnh `uv run poe index` (graphrag index)

## Tóm tắt
`uv run poe index` = `python -m graphrag index` (pyproject.toml).
Đọc tài liệu trong `input/` → trích xuất tri thức bằng LLM → dựng **knowledge graph** +
tóm tắt community → ghi ra các bảng parquet + vector store. Đây là bước **build index**,
chạy sau `init` + nạp input, trước `query`.

Luồng code:
- `cli/main.py:138` → `_index_cli`
- `cli/index.py:44` → `index_cli` → `_run_index` → `api.build_index(...)`
- pipeline: `index/workflows/factory.py` ; executor: `index/run/run_pipeline.py`

---

## INPUT

### Tham số CLI (cli/main.py:138-181)
| Option              | Cờ tắt | Mặc định    | Ý nghĩa |
|---------------------|--------|-------------|---------|
| `--root`            | `-r`   | cwd         | Thư mục project (phải tồn tại) |
| `--method`          | `-m`   | `standard`  | Cách index: `standard` / `fast` / `standard-update` / `fast-update` |
| `--verbose`         | `-v`   | `False`     | Log chi tiết |
| `--dry-run`         |        | `False`     | Chỉ validate config, **không gọi LLM**, không chạy step nào rồi thoát |
| `--cache/--no-cache`|        | `True`      | Dùng cache LLM (tránh gọi lại khi chạy lại) |
| `--skip-validation` |        | `False`     | Bỏ preflight validate tên model/deployment |

Truyền option qua poe: `uv run poe index -- --method fast --verbose`

### Dữ liệu/đầu vào thực tế đọc từ project
- `settings.yaml` + `.env` (config + model + 9router).
- `input/` — các tài liệu (theo `input.type`, ở đây `text` → mọi `.txt`).
- `prompts/*.txt` — prompt cho từng bước LLM.
- `cache/` — cache kết quả LLM (nếu `--cache`).

### Preflight (nếu không `--skip-validation`) — `index/validate_config.py`
Gọi thử completion + embedding để xác thực model/credential **trước khi** chạy.
→ Với 9router: bước này sẽ thật sự gọi `http://localhost:20128/v1`. Nếu sai key/endpoint
hoặc 429, sẽ báo lỗi ngay ở đây.

---

## XỬ LÝ — pipeline Standard (factory.py:52-62)
Chạy **tuần tự**, mỗi workflow đọc/ghi bảng pandas qua TableProvider (parquet):
```
load_input_documents
 → create_base_text_units      (chunk văn bản: size 1200 / overlap 100)
 → create_final_documents
 → extract_graph               (LLM: trích entity + relationship)   ← gọi LLM nhiều nhất
 → finalize_graph              (layout, độ đo graph)
 → extract_covariates          (claims — TẮT vì extract_claims.enabled=false)
 → create_communities          (phân cụm Leiden, max_cluster_size 10)
 → create_final_text_units
 → create_community_reports     (LLM: tóm tắt mỗi community)         ← gọi LLM nhiều
 → generate_text_embeddings     (embedding entity/text_unit/report) ← gọi EMBEDDING nhiều
```
Biến thể `fast`: thay `extract_graph` (LLM) bằng `extract_graph_nlp` + `prune_graph`
(dùng NLP, **ít gọi LLM hơn nhiều** → hợp khi sợ 429/tiết kiệm). Vẫn cần LLM cho community reports.

Executor (`run_pipeline.py`): tạo storage/cache/table-provider từ config, dựng
`PipelineRunContext` (state dùng chung), chạy lần lượt, ghi `stats.json`/`context.json` giữa các bước,
yield 1 `PipelineRunResult` mỗi workflow.

---

## OUTPUT (ghi vào `output/` theo settings.yaml)

### Bảng parquet chính
| File | Nội dung |
|---|---|
| `documents.parquet`        | tài liệu gốc |
| `text_units.parquet`       | các chunk văn bản |
| `entities.parquet`         | thực thể (node của graph) |
| `relationships.parquet`    | quan hệ (cạnh của graph) |
| `communities.parquet`      | cụm community (Leiden) |
| `community_reports.parquet`| báo cáo tóm tắt mỗi community (do LLM viết) |
| `covariates.parquet`       | claims — chỉ có nếu bật `extract_claims` |

### Khác
- `output/lancedb/` — **vector store** (embedding) cho local/drift/basic search.
- `output/stats.json`, `context.json` — thống kê + state pipeline.
- `cache/` — cache LLM (json).
- `logs/` — log + reporting (theo mục `reporting` trong settings.yaml).

### Mã thoát
- `0` nếu mọi workflow OK; `1` nếu có workflow lỗi (`cli/index.py:133-135`).

---

## Lưu ý khi chạy với 9router (xem [[03-config-9router]])
- `index` gọi LLM **hàng trăm lần** (mỗi chunk 1 lần ở extract_graph + mỗi community ở reports)
  → free-tier dễ **429**. `retry: exponential_backoff` đã bật để chịu đựng, nhưng nếu nghẽn:
  - đổi `.env`: `GRAPHRAG_CHAT_MODEL=ollama/gpt-oss:120b` (local), hoặc
  - dùng `--method fast` để giảm số lần gọi LLM.
- Embedding cũng qua openrouter free → bước `generate_text_embeddings` có thể 429.
- Nên thử trước: `uv run poe index -- --dry-run` (chỉ validate config, không tốn token),
  rồi `uv run poe index -- --verbose` để theo dõi.
- `--cache` (mặc định bật): chạy lại sau khi lỗi giữa chừng sẽ tái dùng kết quả LLM đã có → đỡ tốn.

## Kết quả chạy thực tế (A Christmas Carol, 9router + gpt-oss:120b)
- Tổng ~**26 phút** (extract_graph 21.6' — model local reasoning chậm; community_reports 4.3').
- Output `output/`: documents 1, text_units 42, **entities 98**, **relationships 106**,
  communities 19, community_reports 19.
- Vector store `output/lancedb/`: entity_description, community_full_content, text_unit_text.
- Lưu ý: fail ở lần đầu (gemma 403) → đã đổi model + reasoning_effort=low, xem [[03-config-9router]].

## Bước tiếp theo
`uv run poe query` (xem note query nếu đã có). Cập nhật thêm tài liệu → `uv run poe update`.

Liên quan: [[01-graphrag-init]], [[02-nap-input]], [[03-config-9router]].
