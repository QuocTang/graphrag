# 04 — Weaknesses & thesis idea seeds

> AI-generated. Idea seeds là starting points, KHÔNG phải chốt-down idea. User cần brainstorm thêm + tự verify novelty (Google Scholar quick search) trước khi commit thesis direction.
>
> Calibrate theo project: mọi idea dưới đây giữ **mức-3 incremental** (1 anchor + 1 delta) và cố làm **graph/HIN/GNN load-bearing** — đúng viability filter của thesis. Anchor thứ hai (paper HIN/community-detection của advisor) còn TBD → đánh dấu 🔗 ở chỗ cần ghép.

## Weakness list

### Explicit (paper thừa nhận trong Limitations / Future Work)
- "More work is needed to understand how performance generalizes to datasets from various domains with different use cases" (§6.1, p.11) — chỉ 2 corpus, ~1M token, tiếng Anh.
- "Comparison of fabrication rates… would also strengthen the current analysis" (§6.1, p.11) — không đo factuality.
- "we see potential in hybrid RAG schemes that combine embedding-based matching with just-in-time community report generation… as well as… a more exploratory 'drill down' mechanism" (§6.2, p.12) — chưa có local/hybrid/routing mode.

### Implicit (đọc kỹ thấy)
- **Graph không tách bạch được giá trị**: §5.2 — "no statistically significant differences… between global search and TS (graph-free)". Paper tên "GraphRAG" nhưng eval không chứng minh graph cần thiết. (Điểm yếu *và* cơ hội số 1.)
- **Community detection mù ngữ nghĩa**: Leiden phân cụm thuần cấu trúc (degree/modularity), bỏ qua nội dung/embedding của node (§3.1.4).
- **Entity resolution = exact string match** (§3.1.3) → graph phân mảnh với biến thể tên / đa ngôn ngữ; "softer matching" được nhắc nhưng không test.
- **Query-time map quét mọi community** (§3.1.6) → đắt tuyến tính theo số cụm, không routing.
- **Không có cập nhật incremental** — Leiden là thuật toán global, corpus đổi ⇒ re-index.

### Conceptual (dev / system / domain angle)
- **Graph homogeneous**: 1 loại node, edge generic, không type, không meta-path, không learned embedding. Trong domain thật (vd tài liệu học vụ: Môn học / Chương trình / Quy chế / Tiên quyết / Học kỳ / Giảng viên) quan hệ vốn *dị thể* — ép về graph đồng nhất làm mất tín hiệu type.
- **Reproduce đắt** với ngân sách thạc sĩ (281 phút GPT-4/corpus) → cần thay bằng model rẻ/open khi làm thực nghiệm.
- **Tiếng Việt chưa được xét** — prompt hard-code English; pipeline trên tài liệu tiếng Việt là vùng trắng.

## Weakness ranking

> Top 3 weakness có khả năng đỡ một đóng góp thesis trong ~6 tháng. Tiêu chí: (a) đủ cụ thể để định nghĩa experiment, (b) khả thi, (c) chưa bị ai obvious vá.

1. **Graph nông & không tách bạch giá trị (homogeneous + Leiden structural-only).** Đáng vá nhất: vừa là lỗ hổng paper thừa nhận gián tiếp (§5.2), vừa khớp *chính xác* expertise HIN/GNN của advisor → biến graph thành load-bearing là delta tự nhiên, defensible, và có baseline code công khai để dựng trên.
2. **Community detection mù ngữ nghĩa.** Thay Leiden bằng phân cụm dựa GNN/embedding là một experiment gọn, đo được (chất lượng community → chất lượng answer).
3. **Không cập nhật incremental.** Thực tế & graph-centric, nhưng nặng về engineering hơn về "novelty học thuật" → ưu tiên thấp hơn cho mục tiêu Q1.

## Thesis idea seeds (3-4 candidates)

### Idea 1 — HIN-GraphRAG (typed graph + meta-path-aware community)

- **Formula**: flip assumption "graph homogeneous là đủ" → dựng **Heterogeneous Information Network** có node type + meta-path, thay community detection generic bằng phân cụm meta-path-aware. 🔗 Ghép với paper HIN của advisor làm anchor #2.
- **Pitch (1 câu)**: *Lần đầu chứng minh việc gán type + meta-path cho graph index của GraphRAG cho community chất lượng hơn và answer toàn cục tốt hơn so với entity-graph đồng nhất, trên corpus tài liệu học vụ công khai.*
- **Why it's novel**: GraphRAG gốc dùng graph phẳng + Leiden cấu trúc; chưa ai (trong cluster hiện có) đặt câu hỏi "HIN-typing graph index có cải thiện sensemaking không". Đây là *delta đơn*, không phải kiến trúc mới từ đầu.
- **Feasibility (6 tháng thạc sĩ)**:
  - **Time**: ~10–12 tuần (4 dựng HIN schema + ingest, 4 thay community module, 3 eval).
  - **Compute**: thay `gpt-4-turbo` bằng model rẻ/open (gpt-4o-mini / Qwen / Llama) cho indexing → giảm chi phí; GNN nếu có chạy được trên 1 GPU.
  - **Dataset**: tài liệu học vụ công khai (catalog môn, quy chế, chương trình) — đúng hướng "public docs only" đã chốt. Tự build → cần effort annotate schema.
  - **Baseline code**: ✓ microsoft/graphrag công khai (dựng HIN-variant lên trên).
  - **Scoop risk**: ⚠️ trung bình-cao — cluster đã có HybridRAG, KGRAG-Rec, DocumentGraphRAG, Papageorgiou HybridMultiAgentGraphRAG, DualKG. Phải Google Scholar check "heterogeneous graph + GraphRAG community summarization" trước khi commit; differentiate rõ khỏi KG-RAG dùng KG có sẵn (GraphRAG *tự sinh* graph từ text — đó là điểm phân biệt).
- **First 3 experiments**:
  1. Reproduce GraphRAG gốc (homogeneous + Leiden) trên corpus học vụ làm baseline nội bộ.
  2. Thêm node type + meta-path → đo chất lượng community (modularity + coherence ngữ nghĩa) vs Leiden phẳng.
  3. So answer end-to-end (HIN-GraphRAG vs GraphRAG vs vector RAG) bằng LLM-judge **+ thêm factuality** (vá đúng weakness §6.1).
- **Verdict**: **pursue** (ứng viên mạnh nhất cho advisor-fit).

### Idea 2 — GNN-community thay Leiden (semantic-aware partition)

- **Formula**: flip assumption "structural modularity ≈ thematic structure" → học node embedding bằng **heterogeneous GNN (HGT/HAN)** rồi phân cụm trong embedding-space, thay Leiden thuần cấu trúc. 🔗 Ghép paper GNN của advisor.
- **Pitch (1 câu)**: *Community sinh từ embedding GNN (kết hợp cấu trúc + ngữ nghĩa) cho summary sensemaking tốt hơn community thuần cấu trúc (Leiden) trong pipeline GraphRAG.*
- **Why it's novel**: tấn công thẳng vào điểm "graph ≈ no-graph" (§5.2) — nếu community ngữ-nghĩa-hoá làm graph *cuối cùng* vượt TS có ý nghĩa thống kê, đó là đóng góp sạch & trả lời đúng câu hỏi paper bỏ ngỏ.
- **Feasibility**:
  - **Time**: ~10 tuần. **Compute**: GNN nhỏ, 1 GPU đủ.
  - **Dataset**: dùng chung corpus với Idea 1.
  - **Baseline code**: ✓ graphrag + thư viện GNN (PyG/DGL).
  - **Scoop risk**: trung bình — "GNN community detection" là mảng cũ; cái mới là *ghép vào GraphRAG QFS pipeline*. Check kỹ.
- **First 3 experiments**: (1) reproduce Leiden baseline; (2) HGT/HAN embedding → clustering, đo community coherence; (3) end-to-end answer + ablation "graph có thực sự vượt TS chưa".
- **Verdict**: **pursue / có thể merge với Idea 1** (HIN typing + GNN community là một combo tự nhiên, nhưng coi chừng scope phình quá mức-3 — chọn *một* delta làm trọng tâm).

### Idea 3 — Incremental GraphRAG (cập nhật index khi corpus đổi)

- **Formula**: flip assumption "corpus tĩnh, index một lần" → community detection + re-summarization **incremental** khi thêm/sửa tài liệu.
- **Pitch (1 câu)**: *GraphRAG cập nhật được — thêm/sửa tài liệu chỉ re-detect community cục bộ + re-summarize cụm bị ảnh hưởng, tránh re-index toàn bộ.*
- **Why it's novel**: vá weakness thực tế (Leiden global). Nhưng nghiêng về systems/engineering → khó bán novelty ở Q1 ML venue hơn Idea 1/2.
- **Feasibility**: time ~10 tuần; compute thấp; dataset chung. **Scoop risk**: thấp-trung bình (dynamic community detection có literature, ghép vào GraphRAG là mới).
- **First 3 experiments**: (1) baseline full re-index cost; (2) incremental algo + đo delta cost; (3) đo answer quality không tụt sau N lần update.
- **Verdict**: **shelve / fallback** — graph-centric nhưng advisor-fit yếu hơn (ít HIN/GNN). Giữ làm phương án B.

### Idea 4 — (cảnh báo) Query routing / local mode

- **Formula**: vá "map quét mọi community" bằng graph-based routing (chỉ map các cụm liên quan). **⚠️ Đây CHÍNH LÀ future work paper nêu** (§6.2 "embedding-based matching… drill down") → **scoop risk cao**, Microsoft và cộng đồng graphrag có thể đã/đang làm. Liệt kê để *tránh*, không khuyến nghị làm mũi nhọn.

## Recommendation

**AI's pick**: **Idea 1 (HIN-GraphRAG)**, có thể nhúng một phần Idea 2 (GNN community) như delta phụ nếu scope cho phép. Lý do: (a) làm graph/HIN *load-bearing* đúng filter #1; (b) là delta đơn trên 1 anchor (GraphRAG) + 1 anchor advisor (HIN) đúng mức-3; (c) trả lời thẳng câu hỏi paper bỏ ngỏ "graph có cần không"; (d) dùng public docs đúng hướng đã chốt.

**Suy nghĩ thêm — trước khi commit hãy check:**
- 🔗 **Anchor #2 còn thiếu**: phải chọn *một* paper HIN/GNN cụ thể của advisor làm điểm neo phương pháp (meta-path / community detection trên HIN). Idea chỉ "đạt chuẩn" khi ghép được vào đó — chưa ghép thì vẫn là mức-3-treo.
- ⚠️ **GraphRAG là preprint, KHÔNG dùng làm baseline Q1 chính thức** (xem `paper-info.md`). Trong thesis nó là *landmark/anchor khái niệm*; baseline so sánh thực nghiệm nên là paper peer-reviewed trong cluster (HippoRAG, HybridRAG, KGRAG-Rec).
- **Scoop check bắt buộc**: Google Scholar "heterogeneous graph GraphRAG", "typed entity graph query-focused summarization", "GNN community detection RAG" — đối chiếu với HybridRAG / DocumentGraphRAG / Papageorgiou / DualKG đã có trong repo để chắc chắn delta chưa bị chiếm.
- **Đừng để scope phình**: HIN + GNN + incremental cùng lúc = mức 5, vi phạm calibrate. Chọn **một** delta trọng tâm.

## 🔍 Verify list
- Verify: các paper trong cluster (HybridRAG, KGRAG-Rec, DocumentGraphRAG, DualKG, Papageorgiou) đã ai làm "HIN-typed GraphRAG community" chưa — đọc lại `paper-info.md` của chúng trước khi chốt Idea 1.
- Verify: advisor có paper nào về meta-path-guided community detection / HIN clustering để làm anchor #2 — tra `docs/02-advisor-profile.md`.
