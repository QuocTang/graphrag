# 02 — Assumptions & threat model

> AI-generated. Hidden assumption section là **giá trị cao nhất** của file này — paper thường không nói thẳng, AI extract bằng cách đọc giữa dòng.
>
> Lưu ý: GraphRAG là method QFS, **không phải hệ thống security**, nên "threat model" cổ điển (attacker/capability/goal) không áp dụng trực tiếp. Phần dưới mình diễn giải lại "threat model" thành **failure / robustness model** — hệ gãy ở đâu, input xấu nào chưa được xét.

## Explicit assumptions (paper nói thẳng)

- "RAG fails on global questions directed at an entire text corpus… since this is inherently a query-focused summarization (QFS) task, rather than an explicit retrieval task" (Abstract) — giả định bài toán đáng giải tồn tại và khác hẳn retrieval.
- "Prior QFS methods… do not scale to the quantities of text indexed by typical RAG systems" (Abstract) — giả định QFS cổ điển không scale (nên cần index-time summarization).
- "GraphRAG is generally resilient to duplicate entities since duplicates are typically clustered together for summarization" (§3.1.3, p.5) — giả định trùng lặp entity tự được community gom lại nên không hại.
- "Each level of this hierarchy provides a community partition that covers the nodes… in a mutually exclusive, collectively exhaustive way" (§3.1.4, p.6) — giả định Leiden cho phân hoạch MECE sạch.
- LLM là evaluator hợp lệ: "Prior work has shown LLMs to be good evaluators of natural language generation… competitive with human evaluations" (§2.4, p.3).

## Implicit assumptions (paper không nói thẳng nhưng cần)

### Deployment / cost
- **Indexing là one-shot, corpus tĩnh.** 281 phút + hàng nghìn lời gọi GPT-4 để index 1M token (§4.1.3). Leiden là thuật toán *global* → thêm/sửa tài liệu về nguyên tắc phải chạy lại community detection + re-summarize. Paper **không có** cơ chế cập nhật incremental. Giả định ngầm: corpus đủ tĩnh để chi phí index amortize qua nhiều query.
- **Query-time cost chấp nhận được dù map quét mọi community.** Không report latency/$ per query trong head-to-head. Với C3 (nhiều cụm) chi phí map tuyến tính theo số cụm — ngầm giả định số cụm vừa phải.
- **Context window 8k là tối ưu phổ quát.** Chọn từ test trên *baseline SS* rồi áp đồng loạt (§C, p.19); giả định optimum của SS cũng là optimum cho GraphRAG.

### Data
- **Tiếng Anh.** Mọi prompt hard-code *"Return output in English"* (§E.1, p.21). Chất lượng extraction/summary trên tiếng Việt (hay đa ngôn ngữ) không được xét — giả định ngầm corpus tiếng Anh.
- **Entity = surface string khớp nhau.** Exact string matching (§3.1.3) giả định cùng thực thể xuất hiện cùng tên. Sai với viết tắt, dịch, biến thể chính tả.
- **Cấu trúc cộng đồng ≈ cấu trúc chủ đề.** Giả định nền tảng nhất: modularity cấu trúc (Leiden) trùng với cách con người gom theme. Không có ground-truth theme nào được dùng để verify giả định này — chỉ đo gián tiếp qua chất lượng answer.
- **Corpus ~1M token là "đủ lớn" để kết luận scalable.** Test max 1.7M token nhưng claim "scales with… the quantity of source text" (Abstract).

### Trust / quality
- **LLM extraction trung thực & nhất quán.** Toàn graph đứng trên việc GPT-4 trích entity/quan hệ không bịa và không drift giữa các chunk. Không có cơ chế phát hiện entity/relationship bịa.
- **LLM-as-judge không tự thiên vị.** Answer generator VÀ judge đều là GPT-4 → rủi ro self-preference bias (xem `03`). Giả định ngầm: bias này nhỏ / triệt tiêu khi average replicate.
- **Comprehensiveness/diversity là proxy hợp lệ cho chất lượng**, dù không đo tính đúng (factuality).

### User behavior
- **Query trung thực, không đối kháng.** Không xét prompt injection qua tài liệu nguồn (tài liệu độc có thể nhồi entity/claim giả vào graph index), cũng không xét query cố tình moi thông tin. Giả định người dùng & corpus lành tính.

## Threat model (diễn giải = failure / robustness model)

### As stated (reconstructed)
Paper **không có** threat-model section. Tái dựng từ §3.1.3, §6.2 broader impacts:
- **"Attacker" / nguồn lỗi**: chủ yếu là *lỗi mô hình* (extraction sai, answer không phản ánh nguồn) chứ không phải tác nhân ác ý. "there are risks… if the generated answers do not accurately represent the source data" (§6.2, p.12).
- **Goal/quan tâm**: tránh "samples of retrieved facts falsely presented as global summaries" — chính là điểm GraphRAG tuyên bố giảm so với vector RAG.
- **Out-of-scope (thừa nhận)**: fabrication rate ("would also strengthen the current analysis", §6.1), generalization sang domain/scale khác.

### Holes in threat/failure model
- **Indexing-time prompt/document injection**: tài liệu nguồn độc hại có thể khiến LLM trích entity/claim giả → đầu độc graph index → mọi câu trả lời sau bị nhiễm. Không xét.
- **Hallucinated edges/claims**: LLM có thể bịa quan hệ "clearly related" không có trong text → edge ma → community sai. Không có kiểm chứng claim đúng/sai (Claimify chỉ *đếm* claim, không *verify* claim đúng).
- **Conflict / mâu thuẫn trong corpus**: hai tài liệu nói ngược nhau → community summary gộp ra sao? Không có cơ chế phát hiện/giải quyết mâu thuẫn.
- **Seed sensitivity**: shuffle ngẫu nhiên ở map step (§3.1.6) → cùng query có thể ra answer khác theo seed; robustness không đo.

## Assumption ranking

> Top 3 assumption mà nếu *flip* → mở ra cơ hội nghiên cứu (feed vào `04`).

1. **"Cấu trúc cộng đồng (Leiden, structural) ≈ cấu trúc chủ đề".** Flip → "phân cụm bằng GNN/embedding ngữ-nghĩa cho community chất lượng hơn Leiden". Đây là delta đắt giá nhất & khớp expertise GNN của advisor.
2. **"Graph homogeneous (1 loại node, edge generic) là đủ".** Flip → "graph dị thể có type (HIN) + meta-path cho community/answer tốt hơn". Khớp trực tiếp HIN của advisor.
3. **"Corpus tĩnh, index một lần".** Flip → "incremental GraphRAG: cập nhật graph + community khi tài liệu đổi mà không re-index toàn bộ". Graph-centric, sát với domain tài liệu thay đổi theo kỳ.

## 🔍 Verify list
- Verify: ở map step LLM-judge có counterbalance vị trí answer (answer 1 vs 2) không — paper không nói rõ; nếu không thì position bias là confound. (Trùng verify ở `03`.)
- Verify: code repo có hỗ trợ entity resolution "soft" (embedding-based) sẵn không, hay vẫn exact-match như manuscript mô tả — quan trọng nếu định dùng làm baseline tiếng Việt.
