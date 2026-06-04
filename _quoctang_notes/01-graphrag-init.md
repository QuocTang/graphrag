# Lệnh `uv run poe init` (graphrag init)

## Tóm tắt
`uv run poe init` = `python -m graphrag init` (định nghĩa trong `pyproject.toml`, dòng 99).

Mục đích: tạo **bộ khung (scaffold)** cho một project GraphRAG mới — sinh file config mặc định,
file `.env`, thư mục `input/` và toàn bộ prompt mặc định. Đây là **bước đầu tiên** chạy trước
`index` rồi `query`.

Luồng code:
- `cli/main.py:98` → hàm `_initialize_cli`
- gọi `cli/initialize.py:38` → `initialize_project_at`
- template config: `config/init_content.py` (`INIT_YAML`, `INIT_DOTENV`)

---

## INPUT — các tham số (cli/main.py:99-128)

| Option        | Cờ tắt | Mặc định                  | Ý nghĩa |
|---------------|--------|---------------------------|---------|
| `--root`      | `-r`   | thư mục hiện tại (cwd)     | Thư mục gốc project để init vào |
| `--model`     | `-m`   | `gpt-4.1`                 | Model chat/completion. **Prompt hỏi** nếu không truyền cờ |
| `--embedding` | `-e`   | `text-embedding-3-large`  | Model embedding. **Prompt hỏi** nếu không truyền cờ |
| `--force`     | `-f`   | `False`                   | Ghi đè kể cả khi project đã tồn tại |

`--model` và `--embedding` có `prompt=...` nên nếu không truyền sẽ hỏi tương tác trên terminal:
```
Specify the default chat model to use [gpt-4.1]:
Specify the default embedding model to use [text-embedding-3-large]:
```

Chạy không tương tác:
```shell
uv run poe init -- --root ./ragtest --model gpt-4.1 --embedding text-embedding-3-large
```

Ràng buộc: nếu `settings.yaml` đã tồn tại trong `root` và KHÔNG có `--force`
→ ném `ValueError: Project already initialized` (initialize.py:61-63).

---

## OUTPUT — những thứ được tạo ra

Cấu trúc sinh ra trong `<root>`:

```
<root>/
├── settings.yaml          ← file config chính
├── .env                   ← GRAPHRAG_API_KEY=<API_KEY>
├── input/                 ← thư mục rỗng để bỏ tài liệu vào
└── prompts/               ← 13 file prompt .txt
```

### 1. `settings.yaml` (initialize.py:70-73)
- Lấy từ template `INIT_YAML`, thay 2 placeholder `<DEFAULT_COMPLETION_MODEL>` và
  `<DEFAULT_EMBEDDING_MODEL>` bằng model đã chọn.
- Gồm các nhóm: `completion_models`, `embedding_models`, `input`, `chunking`
  (size 1200, overlap 100), các `*_storage`, `cache`, `vector_store`, cấu hình workflow
  (`extract_graph`, `summarize_descriptions`, `community_reports`...) + 4 chiến lược query
  (`local/global/drift/basic_search`).
- Dùng `.replace()` thay vì `.format()` cố ý — vì có placeholder `${GRAPHRAG_API_KEY}`
  phải giữ nguyên để `.env` overlay sau này.

### 2. `.env` (initialize.py:75-77)
- Nội dung: `GRAPHRAG_API_KEY=<API_KEY>`. Phải sửa `<API_KEY>` thành key thật.
- Chỉ ghi nếu chưa tồn tại HOẶC có `--force`.

### 3. `input/` (initialize.py:65-68)
- Thư mục rỗng (tên lấy từ `input_storage.base_dir`, mặc định `"input"`).
- Nơi đặt tài liệu (csv/text/json) để index.

### 4. `prompts/` — 13 file (initialize.py:82-101)
- Indexing: `extract_graph.txt`, `summarize_descriptions.txt`, `extract_claims.txt`,
  `community_report_graph.txt`, `community_report_text.txt`.
- Query: `drift_search_system_prompt.txt`, `drift_reduce_prompt.txt`,
  `global_search_map_system_prompt.txt`, `global_search_reduce_system_prompt.txt`,
  `global_search_knowledge_system_prompt.txt`, `local_search_system_prompt.txt`,
  `basic_search_system_prompt.txt`, `question_gen_system_prompt.txt`.
- Mỗi file chỉ ghi nếu chưa tồn tại hoặc có `--force` → không đè prompt đã chỉnh tay.

Trả về: hàm trả `None`, chỉ log `Initializing project at <path>`. "Output" thực sự là
các file/thư mục trên đĩa.

---

## Hành vi với `--force`
- `settings.yaml`: luôn ghi đè (check force ở dòng 61).
- `.env` và từng prompt: chỉ ghi đè khi có `--force` (ngược lại giữ file cũ).

## Bước tiếp theo sau init
1. Sửa `.env` → điền API key thật.
2. Tùy chỉnh `settings.yaml` (provider, model, storage...).
3. Bỏ tài liệu vào `input/`.
4. Chạy `uv run poe index` → rồi `uv run poe query`.

## Lưu ý v3
Model layer đã chuyển sang LiteLLM: `type` là `chat`/`embedding` (không còn `openai_chat`...),
và cần `model_provider` (vd `openai`, `azure`). Default provider lấy từ
`config/defaults.py: DEFAULT_MODEL_PROVIDER`.
