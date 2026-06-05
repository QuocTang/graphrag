# Config GraphRAG dùng 9router (local OpenAI-compatible proxy)

Dashboard 9router: http://localhost:20128/dashboard/combos
Endpoint API (OpenAI-compatible): `http://localhost:20128/v1`

## Nguyên lý
GraphRAG (v3, LiteLLM) gọi model bằng cách ghép `{model_provider}/{model}` rồi truyền
`api_base` (xem `packages/graphrag-llm/.../lite_llm_completion.py:239-241`).
→ Với endpoint OpenAI-compatible như 9router: đặt `model_provider: openai` + `api_base` trỏ về 9router.
LiteLLM nhận `openai/<model>`, bỏ tiền tố `openai/`, gửi `model: <model>` tới `api_base`.

Env substitution: GraphRAG dùng `string.Template(text).substitute(os.environ)`
(`graphrag-common/.../load_config.py:88`) → **mọi** `${VAR}` trong settings.yaml lấy từ `.env`.
Lưu ý: thiếu 1 biến `${...}` trong môi trường → `KeyError` khi load.

## File `.env` (CONFIG CUỐI CÙNG đã chạy index thành công)
```
GRAPHRAG_API_KEY=sk-9router                # 9router ko bắt buộc key thật, nhưng phải khác rỗng
GRAPHRAG_API_BASE=http://localhost:20128/v1
GRAPHRAG_CHAT_MODEL=ollama/gpt-oss:120b    # local, KHÔNG rate-limit (xem mục troubleshooting)
GRAPHRAG_EMBEDDING_MODEL=openrouter/text-embedding-3-small
```
> ⚠️ gemma-4-31b-it:free ban đầu bị **403 moderation** khi extract_graph → phải đổi sang gpt-oss.

## `settings.yaml` (2 block model)
```yaml
completion_models:
  default_completion_model:
    model_provider: openai
    model: "${GRAPHRAG_CHAT_MODEL}"
    api_base: "${GRAPHRAG_API_BASE}"
    auth_method: api_key
    api_key: ${GRAPHRAG_API_KEY}
    call_args:                       # BẮT BUỘC cho gpt-oss (reasoning model)
      extra_body:                    # extra_body -> đẩy thẳng vào body request OpenAI-compatible
        reasoning_effort: low        # ko có -> đốt hết token vào reasoning, content rỗng, 0 entity
    retry:
      type: exponential_backoff      # cần thiết vì free-tier hay 429

embedding_models:
  default_embedding_model:
    model_provider: openai
    model: "${GRAPHRAG_EMBEDDING_MODEL}"
    api_base: "${GRAPHRAG_API_BASE}"
    auth_method: api_key
    api_key: ${GRAPHRAG_API_KEY}
    retry:
      type: exponential_backoff
```

## Khảo sát model trên 9router (kết quả thực tế)
| Model | Trạng thái |
|---|---|
| `ollama/gpt-oss:120b` + reasoning_effort=low | ✅✅ **ĐANG DÙNG** — local, ko rate-limit, ra entity OK |
| `ollama/minimax-m2.5` | ✅ local — reasoning (cũng cần hạ reasoning) |
| combo `main` | ✅ = gpt-oss:120b nhưng nhồi ~2072 tok system-prompt |
| `openrouter/text-embedding-3-small` | ✅ embedding DUY NHẤT chạy (1536 chiều) — ĐANG DÙNG |
| `openrouter/google/gemma-4-31b-it:free` | ❌ 403 "requires moderation on OpenInference" khi extract_graph |
| `openrouter/qwen/qwen3-next-80b-a3b-instruct:free` | ❌ 429 rate-limit |
| `openrouter/qwen/qwen3-coder:free` | ❌ 429 |
| `openrouter/google/gemma-4-26b-a4b-it:free` | ❌ 429 |
| `ollama/qwen3.5`, `ollama/glm-4.7-flash` | ❌ 404 chưa pull |
| `ollama/kimi-k2.5`, `ollama/glm-5` | ❌ 403 cần subscription |
| `openai/...` (embedding) | ❌ "No credentials for provider: openai" |

## ⚠️ TROUBLESHOOTING (đã gặp thực tế, đã fix)
1. **gemma free → 403 moderation**: call ngắn lọt, nhưng prompt extract_graph thật bị chặn
   → mọi chunk fail → "No entities detected" → pipeline dừng. Giải: đổi model.
2. **gpt-oss/minimax (reasoning) → content rỗng**: model đốt sạch token vào reasoning_content,
   `content`='' kể cả max_tokens 1500-3000. Giải: `call_args.extra_body.reasoning_effort: low`.
   LiteLLM chặn `reasoning_effort` ở top-level (UnsupportedParamsError) → PHẢI bọc trong extra_body.
3. **Kết quả**: index A Christmas Carol thành công ~26 phút (extract_graph 21.6' do model local chậm).
   → 98 entities, 106 relationships, 19 communities. Xem [[04-graphrag-index]].

Quan trọng:
- Mọi route qua 9router bị nhồi ~2000+ token system-prompt mỗi call → tốn/chậm.
- Embedding cũng đi qua openrouter free → có thể 429 ở workflow generate_text_embeddings.
- Nếu index bị 429 chặn → đổi 1 dòng trong `.env`:
  `GRAPHRAG_CHAT_MODEL=ollama/gpt-oss:120b` (local, không rate-limit; chấp nhận reasoning).

## Lệnh kiểm chứng (đã chạy, đều PASS)
```bash
# 1) load config + thay env
uv run python -c "from graphrag.config.load_config import load_config; c=load_config('.'); print(c.completion_models['default_completion_model'].api_base)"
# 2) end-to-end đúng cách GraphRAG gọi (openai/<model> + api_base)
uv run python -c "import litellm; print(litellm.completion(model='openai/openrouter/google/gemma-4-31b-it:free', api_base='http://localhost:20128/v1', api_key='sk-9router', messages=[{'role':'user','content':'Reply OK'}], max_tokens=20).choices[0].message.content)"
# completion → 'OK' ; embedding openai/openrouter/text-embedding-3-small → dim 1536
```

## Bước tiếp theo
`uv run poe index` → `uv run poe query`. Theo dõi log trong `logs/` nếu gặp 429.

Liên quan: [[01-graphrag-init]], [[02-nap-input]].
