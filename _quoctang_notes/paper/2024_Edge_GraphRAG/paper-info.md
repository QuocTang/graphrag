# GraphRAG — From Local to Global: A GraphRAG Approach to Query-Focused Summarization

| Field | Value |
|---|---|
| **Ref ID** | — (chưa có trong inventory `05-literature-scan`) |
| **Cluster** | graph-llm-rag |
| **Paper Type** | Method (system/framework — có pipeline + implementation + eval) |
| **Title** | From Local to Global: A GraphRAG Approach to Query-Focused Summarization |
| **Authors** | Darren Edge†, Ha Trinh†, Newman Cheng, Joshua Bradley, Alex Chao, Apurva Mody, Steven Truitt, Dasha Metropolitansky, Robert Osazuwa Ness, Jonathan Larson (†equal contribution) |
| **Affiliation** | Microsoft Research (+ Strategic Missions & Technologies, Office of the CTO) |
| **Venue** | **arXiv preprint (CoRR)** — *"Preprint. Under review."* — KHÔNG có venue peer-review |
| **Year** | 2024 (v1 24/04/2024); v2 19/02/2025 |
| **Citations** | Rất cao — landmark paper khai sinh thuật ngữ "GraphRAG". 🔍 Số chính xác cần verify trên Google Scholar (snapshot 2026-05-29) |
| **DOI** | [10.48550/arXiv.2404.16130](https://doi.org/10.48550/arXiv.2404.16130) (arXiv DOI, không phải venue DOI) |
| **Source File** | `paper.pdf` (arXiv 2404.16130v2) |
| **Source URL** | https://arxiv.org/abs/2404.16130 |
| **Code** | Có — [github.com/microsoft/graphrag](https://github.com/microsoft/graphrag) (open-source, có bản tích hợp LangChain / LlamaIndex / NebulaGraph / Neo4j) |
| **Dataset** | (1) Podcast transcripts *Behind the Tech* ~1M tokens (1669 × 600-token chunks); (2) News articles từ corpus **MultiHop-RAG** (Tang & Yang 2024) ~1.7M tokens (3197 chunks). Bán-công khai (news corpus công khai; podcast cần re-derive). |
| **Compute** | Indexing 1 corpus ~1M tokens: **281 phút** trên VM 16GB RAM / Xeon, dùng public OpenAI endpoint `gpt-4-turbo` (2M TPM, 10k RPM). Query-time context window cố định 8k tokens. |

> **Paper Type** = Method. Có pipeline đầy đủ (indexing + query-time), implementation công khai, eval định lượng. Không phải survey/benchmark thuần.

## ⚠️ Venue caveat (đọc trước khi dùng làm baseline)

Đây là **preprint-only** — DBLP để venue = `CoRR`, không có DOI venue peer-review, header ghi *"Preprint. Under review."*. Theo rule độ chặt của thesis (baseline phải Q1 peer-reviewed), GraphRAG **không đủ tư cách làm baseline so sánh chính thức** — nó là **landmark / reference paper** (bài định nghĩa khái niệm "GraphRAG", được hàng chục paper Q1 sau này trích dẫn và mở rộng). Dùng nó như điểm neo khái niệm + nguồn gốc của dòng nghiên cứu, rồi chọn baseline peer-reviewed (HippoRAG, HybridRAG, KGRAG-Rec… đã có trong cluster) để so sánh thực nghiệm.

## Summary (2-3 câu)

GraphRAG giải bài toán **global sensemaking** — câu hỏi kiểu "các chủ đề chính trong toàn bộ corpus là gì?" mà vector RAG (lấy top-k đoạn gần nghĩa) trả lời tệ vì câu trả lời không nằm gọn ở vài đoạn. Ý tưởng: ở **indexing time**, dùng LLM trích entity + quan hệ từ toàn corpus → dựng knowledge graph → phân cụm phân cấp bằng **Leiden community detection** → sinh **community summary** cho từng cụm (bottom-up). Ở **query time**, dùng **map-reduce**: mỗi community summary sinh 1 câu trả lời từng phần (map, song song), rồi gộp lại thành câu trả lời toàn cục (reduce). Kết quả: thắng vector RAG 72–83% win-rate về comprehensiveness & diversity (LLM-as-judge), và bản root-level (C0) tốn ít hơn ~97% token so với tóm tắt toàn văn.

## Real-world Analogy

Hỏi *"các chủ đề lớn xuyên suốt toàn bộ bài viết Wikipedia về biến đổi khí hậu là gì?"*. **Vector RAG** = quăng câu hỏi vào ô search, đọc 5 đoạn gần nghĩa nhất rồi trả lời → thấy cây không thấy rừng, bỏ sót chủ đề chỉ xuất hiện rải rác. **GraphRAG** = trước đó đã lập sẵn một *bản đồ khái niệm* (ai/cái gì liên quan tới cái gì), gom thành các nhóm chủ đề, viết sẵn một bản tóm tắt cho mỗi nhóm; khi có câu hỏi thì hỏi từng bản tóm tắt nhóm "bạn đóng góp gì cho câu này?", rồi ghép các mẩu lại thành câu trả lời bao quát. Đánh đổi: dựng bản đồ rất tốn công (281 phút + nhiều lần gọi LLM) nhưng tái sử dụng cho mọi câu hỏi sau.

## Limitations

> Fill từ §6.1 Limitations + §6.2 Future Work.

1. **Generalization chưa chứng minh** — chỉ test 2 corpus, đều ~1M token, đều tiếng Anh. Không rõ scale lên 10M+ token hay sang domain/ngôn ngữ khác có giữ kết quả (§6.1, p.11).
2. **Không đo fabrication / factuality** — eval chỉ đo comprehensiveness & diversity (số lượng & độ đa dạng claim), KHÔNG đo claim đúng/sai. Paper tự thừa nhận nên thêm so sánh fabrication rate kiểu SelfCheckGPT (§6.1, p.11).
3. **Chưa có local/hybrid mode** — toàn bộ pipeline là "global"; map-reduce chạy qua *tất cả* community nên đắt. Future work đề xuất embedding-match query↔graph + just-in-time community report + drill-down (§6.2, p.12). → Đây là khe hở lớn cho idea thesis.

## Reading Status

| Level | Done? | Date | Output |
|---|---|---|---|
| Skim | ✓ | 2026-05-29 | paper-info.md (file này) |
| Read | ✓ | 2026-05-29 | digest 00–04 (AI deep-digest, ngang mức Read) |
| Deep | ☐ | — | code annotations (chưa clone repo) |
