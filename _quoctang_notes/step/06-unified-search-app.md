# Unified Search App — chạy demo so sánh 4 kiểu search trên UI

App Streamlit ở `unified-search-app/` (TÁCH RIÊNG khỏi workspace, có uv.lock riêng).
Chạy: `cd unified-search-app && DATA_ROOT="$(pwd)/us_data" uv run poe start` → http://localhost:8501

## ⚠️ BẪY SETUP (đã gặp thực tế, đã sửa)
1. **App ghim `graphrag==2.5.0` (pypi) nhưng index của mình là v3** → 2.5.0 không parse được
   settings.yaml dạng LiteLLM (`completion_models`/`model_provider`). Fix: trỏ graphrag về
   workspace local qua `[tool.uv.sources]` trong `unified-search-app/pyproject.toml`
   (phải khai đủ **cả 8 package**: graphrag + 7 sibling, vì graphrag-cache==3.1.0... không có trên pypi).
2. **uv mặc định chọn Python 3.13** → `spacy → thinc` không có wheel 3.13, build C++ fail
   (`_PyLong_AsByteArray` đổi chữ ký). Fix: `rm -rf .venv && uv sync --python 3.11`.
3. **`uv run poe start` báo "Failed to spawn: poe"** → poethepoet nằm trong optional `dev`.
   Fix: `uv sync --extra dev`.
4. **App cần `DATA_ROOT` + `listing.json`** (không có thì raise lúc import —
   `app/knowledge_loader/data_sources/default.py`). Đã tạo `unified-search-app/us_data/listing.json`
   với `path` là **đường dẫn tuyệt đối** tới repo root (os.path.join gặp path tuyệt đối sẽ bỏ prefix
   → không cần copy data). Dataset folder phải có: `output/`, `settings.yaml`, `.env`, `prompts/`.
5. **Bug v3: `api.basic_search` bắt buộc `response_type`** (v2 có default) — app cũ thiếu →
   bật toggle "Include basic RAG" là crash. Đã vá `app/app_logic.py` (thêm `response_type="Multiple Paragraphs"`).
6. **Bug "5 câu hỏi gợi ý dính thành 1"**: app sinh câu hỏi bằng global search với
   `response_type="Single paragraph"` → gpt-oss trả `1. ... 2. ... 3. ...` trên MỘT dòng,
   mà parser `convert_numbered_list_to_array` (`app/ui/search.py`) tách theo `\n` → cả blob
   thành 1 row. Đã vá: `re.split(r"\s*\d+\.\s+", line)` tách được cả inline.

## Bố cục UI
- **Sidebar trái (Options)** — mặc định thu gọn, bấm `>` để mở: dropdown Dataset (từ listing.json),
  số câu hỏi gợi ý (mặc định 5), 4 toggle search. Mặc định bật: **Local + Global**.
- **Nút "Suggest some questions"** → bảng câu hỏi, tick 1 dòng → tự chạy search. Nút Reset để quay lại.
- **Ô "Ask a question to compare the results"** → Enter → chạy SONG SONG mọi search đang bật.
- **Tab "Search"**: mỗi search đang bật = **1 cột dọc**, thứ tự cố định Basic → Local → Global → Drift.
  Trả lời hiện dưới header cột của nó; dưới nữa là Citations CỦA CỘT ĐÓ. Cột nào xong trước hiện trước
  (~10–60s/cột với 9router).
- **Tab "Community Explorer"**: trái = danh sách 19 community reports (id + title);
  phải = report đang chọn: summary → Priority (rating 1-10) + lý do → Key Findings →
  bảng entities/relationships được trích. KHÔNG tốn LLM call → dùng để soi chất lượng index.

## "Suggest some questions" — cơ chế
KHÔNG có API riêng — chỉ là **global search trá hình** với meta-prompt
"Generate numbered list only with the top N most important questions of this dataset"
(`app/home_page.py`, `dynamic_community_selection=True`). LLM chỉ đọc community reports
→ câu hỏi phản ánh cái reports cho là quan trọng (nên mới lòi câu về Project Gutenberg license —
index ăn cả boilerplate đầu/cuối file input).

## 4 kiểu search — ví von "thư viện"
Sau khi index, sách được chế thành 3 thứ:
- 📄 42 trang photo rời (text_units / **Sources**)
- 🕸️ danh bạ + sơ đồ quan hệ (98 **entities** + 106 **relationships**)
- 📋 19 bản tóm tắt theo cụm chủ đề (**community reports**) — LLM viết sẵn LÚC INDEX

| Search | Ví von | Cách chạy | Mạnh | Yếu | Chi phí |
|---|---|---|---|---|---|
| **Basic RAG** | Sinh viên ôn cấp tốc | embed câu hỏi → vớt vài trang giống nhất → trả lời | đáp án nằm gọn 1-2 đoạn | câu hỏi toàn cục | rẻ nhất |
| **Local** | Thám tử | tra danh bạ tìm entity khớp → gom quan hệ + trang nhắc tới + report cụm chứa nó | "X là ai? X–Y quan hệ gì?" | câu hỏi không neo entity | 1 embed + 1 call |
| **Global** | Chủ tọa hội nghị | KHÔNG đọc sách: map-reduce trên 19 reports (map: rút ý + chấm điểm; reduce: tổng hợp) | chủ đề/thông điệp toàn cục | chi tiết vụn (tóm tắt làm rơi) | nhiều call |
| **DRIFT** | Nhà báo điều tra | đọc reports định hướng → TỰ SINH câu hỏi con → local search từng câu → gộp | câu phức tạp vừa rộng vừa sâu | chậm + đắt nhất | nhiều vòng |

## Local Search — chi tiết (code v3)
1. **Map câu hỏi → entities**: embed câu hỏi, vector search trên embedding MÔ TẢ ENTITY
   trong lancedb, lấy k=10 (oversample ×2) — `query/context_builder/entity_extraction.py:41`.
2. **Build context trộn** (`query/structured_search/local_search/mixed_context.py:89`),
   chia `max_context_tokens` theo tỷ lệ: text_unit_prop=0.5 (chunk gốc chứa entity),
   community_prop=0.25 (report của cụm), còn lại 0.25 = bảng entities + relationships top-k
   (ưu tiên quan hệ GIỮA các entity đã chọn) + covariates (mình tắt claims).
3. **1 call LLM** với `prompts/local_search_system_prompt.txt`.
Tinh chỉnh trong settings.yaml mục `local_search:`: top_k_entities, text_unit_prop...
Khác Basic RAG ở chỗ: vector search trên MÔ TẢ ENTITY (không phải chunk) rồi mới lần ngược
ra chunk → kéo được cả đoạn không chứa từ khóa nhưng dính tới entity liên quan.

## Citations `[data: ...]` — các ID là gì
ID = **số dòng (`human_readable_id`) trong bảng parquet** — để truy ngược bằng chứng. Ví dụ từ index này:
- `Entities (5)` → dòng 5 entities.parquet = EBENEZER SCROOGE; `Entities (2)` = SCROOGE'S CLERK
- `Relationships (1)` → cạnh SCROOGE → SCROOGE'S CLERK
- `Reports (17)` → report "Scrooge and His Victorian Network" (xem trong Community Explorer)
- `Sources (2)` → chunk gốc "...Scrooge! a squeezing, wrenching, grasping..."
- `+more` = còn nguồn nữa, không liệt kê hết. Trên UI số là LINK bấm nhảy xuống bảng citations.

**Mỗi search chỉ cite được thứ nó ĐỌC** → nhìn đuôi citation biết cột nào:
- Global: chỉ `Reports` (chưa từng thấy văn bản gốc — "tóm tắt của tóm tắt")
- Local/DRIFT: `Entities / Relationships / Sources / Reports` (bằng chứng cấp 1)
- Basic: chỉ `Sources`

## Chấm "cột nào trả lời OK hơn" (chấm tay, ~tiêu chí paper GraphRAG dùng LLM-judge)
1. **Có căn cứ** (quan trọng nhất): bấm vài ID → bằng chứng có thật sự nói vậy không?
2. **Đủ ý** (comprehensiveness): câu hỏi mấy vế, trả được mấy vế?
3. **Trả lời thẳng** (directness): hay vòng vo "dataset này nói về nhiều chủ đề..."?
4. **Đa dạng góc nhìn** (diversity).
Quy luật kỳ vọng: hỏi về thực thể cụ thể → Local thắng; hỏi chủ đề toàn cục → Global thắng.
Ngược kỳ vọng = index có vấn đề → vào Community Explorer soi nguyên liệu.
Mẹo so sánh: hỏi TỪNG CÂU MỘT (đừng gửi blob 5 câu — cả 2 cột đều lan man, khó so).
