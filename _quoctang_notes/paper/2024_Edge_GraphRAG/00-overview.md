# 00 — Overview

> AI-generated digest. Mọi claim trích từ paper có anchor `(§X, p.Y)`. Verify list ở cuối — spot-check trước khi cite.
>
> **Reading scope của AI:** đọc kỹ §1–§7 (toàn bộ body) + Appendix A (gleaning/self-reflection), B (community example), C (context window), D (ví dụ answer), E (system prompts), G (statistical analysis). Skim Appendix F (eval prompts — chỉ là wording của criteria). Tổng **Verify items: 7** (gom ở cuối mỗi file).

## TL;DR (30 giây đọc)

Vector RAG (lấy top-k đoạn gần nghĩa) trả lời tốt câu hỏi *cục bộ* (fact nằm ở vài đoạn) nhưng **gãy với câu hỏi toàn cục** kiểu "các chủ đề chính trong corpus là gì" — vì đó là bài query-focused summarization, không phải retrieval. GraphRAG giải bằng cách **đẩy việc tóm tắt sang indexing time**: LLM dựng knowledge graph entity→quan hệ, Leiden phân cụm phân cấp, mỗi cụm có sẵn một community summary; query-time chỉ map-reduce qua các summary đó. Bằng chứng mạnh nhất: thắng vector RAG **72–83% win-rate** (comprehensiveness, p<.001) trên 2 corpus ~1M token, và bản root-level tốn **ít hơn ~97% token** so với tóm tắt toàn văn. **Điểm cần nhớ nhất (chìm trong §5.2):** phần *graph* đóng góp ít — global-có-graph (C0–C3) so với global-không-graph (TS) **gần như không khác biệt có ý nghĩa thống kê**. Cú thắng lớn là "global vs vector", không phải "graph vs no-graph".

## 5C analysis

### Category
**System / framework.** Có Methodology đầy đủ (pipeline 6 bước, §3.1), implementation công khai (microsoft/graphrag), và eval định lượng 2 thí nghiệm (§4–5). Không phải theory (không có theorem) cũng không phải survey.

### Context
Subfield: **RAG cho LLM** ở giao điểm với **query-focused summarization (QFS)** và **knowledge-graph-augmented retrieval**.

- Phân biệt với **vector RAG** (Lewis et al. 2020): vector RAG "do not support sensemaking queries… that require global understanding of the entire dataset" (§2.1, p.2). GraphRAG đặt cược vào "a previously unexplored quality of graphs… their inherent modularity (Newman, 2006) and the ability to partition graphs into nested modular communities" (§2.2, p.3).
- Phân biệt với **hierarchical-summary RAG** (RAPTOR/Sarthi 2024, Kim 2023): GraphRAG khác ở chỗ "generating a graph index from the source data, then applying graph-based community detection to create a thematic partitioning" (§2.1, p.3) — tức cụm chủ đề đến từ *cấu trúc graph*, không phải cây tóm tắt thuần văn bản.
- Phân biệt với **KG-as-index / subgraph-in-prompt** (G-Retriever, KAPING, KGP): các method đó dùng graph để *truy hồi* facts cục bộ; GraphRAG dùng graph để *tóm tắt toàn cục*.

### Correctness (assumptions tier-1)
- **LLM trích entity/quan hệ đủ tốt để graph có nghĩa.** Toàn pipeline đứng trên chất lượng extraction của GPT-4. Sai → graph rác → community rác → summary rác.
- **Cấu trúc cộng đồng (community) của graph ≈ cấu trúc chủ đề (theme) của corpus.** Đây là cú đặt cược trung tâm: phân cụm theo *modularity cấu trúc* (Leiden) sẽ trùng với cách con người gom chủ đề. Paper không chứng minh — chỉ giả định và đo gián tiếp qua chất lượng câu trả lời.
- **Comprehensiveness/diversity (do LLM chấm) là proxy hợp lệ cho "câu trả lời tốt".** Nếu metric chỉ thưởng độ dài/độ rậm → "win" có thể là artifact (xem §03 critique).

### Contributions
1. **Pipeline GraphRAG**: indexing-time = LLM→entity graph→Leiden hierarchical communities→bottom-up community summaries; query-time = map-reduce qua community summaries (§1, p.2; §3.1, p.4–6).
2. **Cơ chế summary phân cấp tiết kiệm token**: root-level (C0) đạt comprehensiveness/diversity cạnh tranh nhưng tốn ~97% ít token hơn map-reduce toàn văn (Abstract; §5.1, p.10; Table 2).
3. **Quy trình eval cho global sensemaking khi không có ground truth**: (a) sinh câu hỏi bằng persona-based generation (Algorithm 1, §3.2, p.6); (b) LLM-as-judge head-to-head theo 4 tiêu chí Comprehensiveness/Diversity/Empowerment + control Directness (§3.3, p.7).
4. **Validation độc lập bằng claim-based metric** (Claimify → 47.075 claim; comprehensiveness = #claim, diversity = #cluster) khớp ~78%/69–70% với LLM-judge (§4.2, §5.2, p.9–11).
5. **Gleaning / self-reflection** cho extraction: cho phép dùng chunk lớn (rẻ) mà không mất recall entity (§A.2, p.18–19; Fig. 3).

### Clarity
Viết rõ, pipeline dễ theo nhờ Fig. 1. Điểm mạnh: ví dụ "NeoChip" cụ thể hoá extraction (§3.1.2), Appendix E in full system prompts → reproduce được. Điểm lộn xộn nhất: **phần kết quả** — Figure 2 là ma trận win-rate 6×6 bị OCR/extract thành một rừng số rời rạc (dòng 490–842 của `paper.txt`), rất khó đọc nếu không mở PDF gốc; nên đọc Table 6/App G để lấy con số chính xác. Định nghĩa C0–C3 ("projected downwards" khi không có sub-community) hơi khó nắm ở lần đọc đầu (§4.1.2, p.8).

## Top 3 things user nên nhớ

1. **Giá trị thật của graph chưa được chứng minh tách bạch.** Paper tên là "GraphRAG" nhưng eval cho thấy global-có-graph (C0–C3) ≈ global-không-graph (TS) — "no statistically significant differences… between global search and TS" (§5.2, p.11). Win lớn là *global vs vector*, graph chỉ thêm chút ít. → Đây vừa là điểm yếu lớn nhất, vừa là **khe hở vàng cho thesis**: làm cho graph *thực sự* load-bearing (HIN typing, GNN community, meta-path) là delta hợp lý.
2. **Đây là method "đẩy chi phí về indexing".** Tốn 281 phút + rất nhiều lời gọi GPT-4 để index 1M token, đổi lại query-time rẻ và trả lời toàn cục tốt. Hệ quả: **không có câu chuyện cập nhật incremental** — corpus đổi là phải re-index (Leiden là thuật toán global). Với domain tài liệu thay đổi (quy chế học vụ theo kỳ) đây là vấn đề thực.
3. **Metric chỉ đo "rậm & đa dạng", KHÔNG đo "đúng".** Comprehensiveness = số claim, diversity = số cụm claim; không hề đo claim đúng/sai. Paper tự thừa nhận thiếu so sánh fabrication rate (§6.1, p.11). Khi cite, đừng đọc kết quả thành "GraphRAG chính xác hơn".

## Reading order recommendation

- **Chỉ cần lit-review / hiểu khái niệm** → đọc `00` (file này) + `01-method.md` là đủ.
- **Muốn rút idea thesis** → `00` → `04-weaknesses-ideas.md` → `02-assumptions.md` (assumption nào flip được thành đề tài).
- **Muốn cãi lại / dùng làm baseline reference** → thêm `03-eval.md` (chỗ metric yếu + chỗ graph không tách bạch).

## 🔍 Verify list
- Verify: số citation chính xác (file này ghi "rất cao, cần verify") — tra Google Scholar.
- Verify: liệu v2 (Feb 2025) sau cùng có được nhận ở venue peer-review nào không, hay vẫn CoRR/preprint — DBLP hiện chỉ thấy CoRR.
