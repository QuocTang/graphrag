# Lệnh `uv run poe query` (graphrag query)

## ⚠️ BẪY CÚ PHÁP (đã gặp thực tế)
`query` là **positional argument**, KHÔNG phải cờ `--query`. Và đừng chèn `--`.

SAI:
```shell
uv run poe query -- --method global --query "What are the main themes?"
# → Error: Got unexpected extra arguments (-- --query ...)
```
ĐÚNG (chạy thẳng graphrag, câu hỏi để cuối, trong ngoặc kép):
```shell
uv run graphrag query --method global "What are the main themes of the story?"
uv run graphrag query --method local  "Who is Scrooge?"
```

## Chữ ký CLI (cli/main.py @app.command("query"))
| Tham số | Loại | Ghi chú |
|---|---|---|
| `QUERY` | **positional** (bắt buộc) | câu hỏi, để cuối lệnh, trong "..." |
| `--method` / `-m` | option | `local` / `global` / `drift` / `basic` |
| `--root` / `-r` | option | thư mục project (mặc định cwd) |
| `--data` | option | trỏ thẳng tới thư mục output parquet (nếu khác config) |
| `--community-level` | option | độ sâu community dùng cho global/local |
| `--dynamic-community-selection` | flag | chọn community động (global) |
| `--response-type` | option | vd "Multiple Paragraphs", "Single Page", "List" |
| `--streaming/--no-streaming` | flag | in dần phản hồi |
| `--verbose` / `-v` | flag | log chi tiết |

## 4 phương pháp search (query/structured_search/)
- **global**: map-reduce trên **community_reports** → câu hỏi tổng quát/chủ đề toàn corpus.
  (KHÔNG cần embedding/vector store.)
- **local**: tập trung quanh entity liên quan (entities + relationships + text_units) → hỏi về thực thể cụ thể.
  (CẦN embedding → vector store lancedb.)
- **drift**: lặp local+global, đào sâu dần.
- **basic**: RAG thường trên text_units (vector similarity).

## INPUT cần có
- `output/*.parquet` (entities, relationships, communities, community_reports, text_units) — do `index` sinh.
- `output/lancedb/` (vector store) — cho local/drift/basic.
- `settings.yaml` + `.env` (model qua 9router, xem [[03-config-9router]]).
- `prompts/*search*` — prompt cho từng method.

## OUTPUT
In câu trả lời ra stdout, kèm trích dẫn `[Data: Reports(...)]` / `[Data: Entities(...)]`
chỉ về dữ liệu nguồn trong các bảng. Không ghi file (trừ khi tự redirect).

## Kết quả chạy thực tế
`--method global "What are the main themes of the story?"` (A Christmas Carol):
→ trả 8 chủ đề (Redemption, Generosity vs Miserliness, Social Class, ...) kèm citation report. OK.
Global dùng gpt-oss (map 19 reports + reduce) → hơi chậm vì model local reasoning.

## Lưu ý 9router
Global gọi LLM (gpt-oss) nhiều lần (map mỗi report) → chậm. Local/basic nhẹ hơn về LLM
nhưng cần embedding (openrouter/text-embedding-3-small).

Liên quan: [[01-graphrag-init]], [[02-nap-input]], [[03-config-9router]], [[04-graphrag-index]].
