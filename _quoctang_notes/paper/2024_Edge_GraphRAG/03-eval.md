# 03 — Eval setup, results, critique

> AI-generated. Critique section là phần valuable nhất - reviewer angle.

## Setup

### Dataset
- **Name**: (1) Podcast transcripts — *Behind the Tech with Kevin Scott*; (2) News articles — lấy từ corpus **MultiHop-RAG** (Tang & Yang 2024).
- **Size**: Podcast ~1M token (1669 × 600-token chunks, overlap 100); News ~1.7M token (3197 chunks). Graph kết quả: Podcast 8.564 node / 20.691 edge; News 15.754 node / 19.520 edge (§5.1, p.9).
- **Public**: News corpus công khai (qua MultiHop-RAG); Podcast là transcript công khai nhưng phải tự re-derive → reproducibility một phần.
- **Why chosen (paper rationale)**: "representative of corpora that users may encounter in their real-world activities" + nằm trong khoảng 1M token (§4.1.1, p.8).
- **Anchor**: §4.1.1, p.8.

### Baselines
- **SS (semantic search / vector RAG)** — baseline chính, "naïve RAG": retrieve chunk theo similarity tới khi đầy context (§4.1.2, p.8).
- **TS (text summarization)** — *ablation của chính paper*: map-reduce thẳng trên source text, KHÔNG graph. Đây là baseline "global nhưng graph-free" — quan trọng nhất để đo giá trị graph.
- **C0–C3** — GraphRAG ở 4 mức community (C0 root/ít nhất → C3 leaf/nhiều nhất).
- **Fairness check**: ⚠️ baseline ngoài *chỉ có 1* (SS) và nó là "naïve". **Không** so với advanced RAG nào khác (RAPTOR, HippoRAG, hierarchical-summary variants). TS là ablation nội bộ chứ không phải baseline độc lập. Context window & prompt giữ giống nhau qua 6 điều kiện (điểm fair, §4.1.2).

### Metrics
- **Measured (Exp 1, LLM-as-judge head-to-head)**: Comprehensiveness, Diversity, Empowerment + control **Directness**. Win-rate % theo cặp, 125 câu/dataset, mỗi cặp lặp 5 lần rồi average (§3.3, §4.1; Fig. 2).
- **Measured (Exp 2, claim-based, validation)**: Comprehensiveness = trung bình #claim/answer (Claimify); Diversity = trung bình #cluster claim (agglomerative, complete linkage, distance = 1−ROUGE-L, nhiều threshold) (§4.2, p.9).
- **Not measured (gap)**: **factuality / fabrication rate** (paper tự nhận thiếu); **latency & $ per query**; failure-mode breakdown; độ nhạy theo seed (shuffle); kết quả ngoài tiếng Anh; scale > 1.7M token.

### Hardware / setting
- `gpt-4-turbo`, context window 8k (ablation 8/16/32/64k → 8k thắng, §C). Indexing 281 phút/Podcast trên VM 16GB/Xeon. Leiden qua `graspologic`. Question gen K=N=M=5 → 125 câu (Algorithm 1).

## Results summary

### Headline numbers
- **Global (C0–C3) vs vector RAG (SS), Comprehensiveness**: win-rate **72–83%** (Podcast, p<.001) và **72–80%** (News, p<.001) (§5.1, p.9). App G xác nhận, vd C2 vs SS = 80.56% (t=−8.21, p<.001).
- **Global vs SS, Diversity**: **75–82%** (Podcast, p<.001) và **62–71%** (News, p<.01) (§5.1).
- **Token cost (Table 2, p.10)**: C0 Podcast = 26.657 token = **2.6%** so với TS (~1.01M); root-level "9x–43x" ít token hơn; C3 ít hơn TS 26–33%; C0 ít hơn TS >97%.
- **Claim-based (Exp 2, Table 3)**: mọi điều kiện global có #claim cao hơn SS rõ rệt (SS ~25.2–26.5 vs global ~32–34, p<.05) (§5.2, p.11).
- **Directness (control)**: vector RAG (SS) thắng đều — đúng kỳ vọng (answer ngắn/thẳng) → xác nhận thiết kế eval không bị "GraphRAG thắng mọi thứ" một cách vô lý (§5.1, p.9; §D, p.20).

### Subtle findings (đọc kỹ mới thấy — quan trọng)
- 🔴 **Graph KHÔNG tách bạch được giá trị**: "for both comprehensiveness and diversity, across both datasets, there were **no statistically significant differences** observed among the global search conditions or **between global search and TS**" (§5.2, p.11). Tức GraphRAG (có graph) ≈ TS (không graph). Đây là phát hiện quan trọng nhất và bị chôn trong §5.2.
- **Empowerment kết quả "mixed"** cho cả global-vs-SS lẫn GraphRAG-vs-TS (§5.1, p.9) — không phải thắng sạch.
- **News diversity yếu hơn Podcast**: claim-based chỉ C0 vượt SS có ý nghĩa ở *mọi* threshold; C1–C3 chỉ significant ở vài threshold (§5.2, p.11).
- **Alignment LLM-judge ↔ claim-based chỉ đo trên non-tie**: ties bị loại, non-tie chỉ chiếm 33% (comprehensiveness) / 39% (diversity); trong đó khớp 78% / 69–70% (§5.2, p.11). → "moderately strong" là cách nói lạc quan cho một mẫu đã lọc.

## Critique of eval design

### Strong points
- **Có significance testing thật**: paired test, p-value đầy đủ trong Appendix G (win-rate + t-stat + p cho từng cặp).
- **Multi-replicate** (5×/cặp) → giảm nhiễu stochastic của LLM.
- **Hai metric độc lập** (LLM-judge + claim-based Claimify) cross-validate nhau.
- **Control criterion (Directness)** như sanity check — chứng tỏ method không thắng-tất-cả một cách đáng ngờ.
- **Ablation hữu ích**: context window (§C), gleaning/self-reflection (Fig. 3), 4 community level.

### Weak points
- **Chỉ 1 baseline ngoài, lại "naïve".** Không có advanced-RAG baseline (RAPTOR, HippoRAG…). "Thắng naïve RAG" là thanh thấp cho một method tốn 281 phút indexing.
- **Graph không được chứng minh cần thiết.** TS (graph-free) ngang ngửa → eval không support được hàm ý của chính cái tên "GraphRAG". (xem mismatch bên dưới.)
- **Metric thưởng độ rậm, không normalize độ dài.** Comprehensiveness ≈ "answer dài & nhiều mục"; GraphRAG sinh answer dài có cấu trúc → lợi thế cấu trúc của metric, không hẳn lợi thế chất lượng. Không có length-control.
- **Không đo factuality.** Comprehensive ≠ correct. Một answer có thể "comprehensively wrong"; Claimify đếm claim chứ không kiểm claim đúng.
- **LLM tự chấm output của chính họ-hàng (GPT-4 judge GPT-4 answer)** → self-preference bias khả dĩ; không có human eval đối chiếu trong paper này.
- **Không cost/latency trong head-to-head**: chi phí query-time (map qua mọi community) bị bỏ ngoài bảng so sánh chất lượng.
- **Scale & ngôn ngữ hẹp**: 2 corpus, ~1M token, tiếng Anh — nhưng claim "scales with the quantity of source text".

### Mismatch claim vs evidence
- **Claim "GraphRAG" (graph là cốt lõi) ↔ evidence "graph ≈ no-graph"**: §5.2 nói thẳng không có khác biệt có ý nghĩa giữa global-search và TS. Claim phòng-thủ-được thực ra là *"global/hierarchical summarization > vector RAG cho sensemaking"*; vai trò *cần thiết* của graph chưa được chứng minh.
- **Claim "scales with quantity of source text" ↔ test ≤ 1.7M token.** Không có điểm dữ liệu ở 10M/100M để chống đỡ chữ "scales".
- **Claim ưu thế chất lượng ↔ metric không đo đúng/sai.** "Tốt hơn" ở đây = rậm hơn + đa dạng hơn theo LLM-judge, không phải đúng hơn.

### Reviewer rebuttal demands (đóng vai reviewer NeurIPS/EMNLP khó tính)
1. **Ablation tách vai trò graph**: so GraphRAG với (a) random partition cùng kích thước cụm, (b) embedding-clustering partition (no graph), (c) TS. Nếu graph-Leiden không vượt random/embedding partition có ý nghĩa → graph không load-bearing.
2. **Thêm advanced-RAG baseline** (RAPTOR, HippoRAG) + **human eval** trên một mẫu để hiệu chỉnh LLM-judge.
3. **Factuality/fabrication**: chạy SelfCheckGPT hoặc verify claim đúng/sai, không chỉ đếm claim. Report length-normalized comprehensiveness + latency/$ per query.

## Reproducibility check
- **Code public**: ✓ github.com/microsoft/graphrag (+ full prompts §E).
- **Data public**: một phần — News (MultiHop-RAG) công khai; Podcast phải tự re-derive.
- **Hyperparams reported**: ✓ chunk 600/overlap 100, context 8k, K=N=M=5, Leiden via graspologic, gpt-4-turbo.
- **Seed reported**: ✗ (shuffle ngẫu nhiên ở map step không nêu seed/độ nhạy).
- **Reproducibility verdict**: **medium** — code + prompt đầy đủ, nhưng phụ thuộc endpoint `gpt-4-turbo` (model version drift) và chi phí GPT-4 lớn (281 phút/corpus) → khó reproduce với ngân sách thạc sĩ trừ khi thay bằng model rẻ hơn.

## 🔍 Verify list
- Verify: con số win-rate đọc từ Fig. 2 (ma trận bị extract thành rừng số ở `paper.txt` dòng ~490–842) — khi cite số chính xác nên mở PDF gốc / dùng App G (Table win-rate + p-value) thay vì đọc text extraction.
- Verify: LLM-judge có randomize/counterbalance vị trí (answer 1 vs 2) để chống position bias không — paper không nêu rõ ở §3.3.
