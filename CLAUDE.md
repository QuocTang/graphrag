# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

GraphRAG is a data pipeline that extracts a knowledge graph from unstructured text using LLMs, then answers questions over that graph. There are two halves: an **indexing** engine (text → graph → community summaries, stored as parquet tables + a vector store) and a **query** engine (four search strategies over the indexed artifacts).

## Repository layout

This is a **`uv` workspace monorepo**. The `graphrag` package depends on seven sibling packages (all version-pinned to match):

- `packages/graphrag/` — the main package (`graphrag`): CLI, public API, config, indexing pipeline, query engine, data model, prompts.
- `packages/graphrag-llm/` — `graphrag_llm`: the LLM layer, a wrapper over **LiteLLM** providing completion/embedding with caching, rate limiting, retry, threading, and middleware.
- `packages/graphrag-cache/`, `-storage/`, `-vectors/`, `-input/`, `-chunking/`, `-common/` — pluggable infrastructure modules, each with its own README and `example_notebooks/`.

`unified-search-app/` is a **separate** Streamlit demo app with its own `uv.lock` — it is *not* part of the workspace. `tests/` and `scripts/` live at the repo root and run against the installed workspace packages.

> Note: `DEVELOPING.md` / `CONTRIBUTING.md` describe an older single-package layout (`graphrag/api`, `graphrag/index`, …). Those paths now live under `packages/graphrag/graphrag/`. Python requirement is **3.11–3.13** (per `pyproject.toml`), not 3.10.

## Commands

Tasks are run with `uv run poe <task>` (poethepoet). All commands run from the repo root.

```shell
uv sync --all-packages        # install everything in the workspace
uv run poe check              # CI gate: ruff format --check, ruff check, pyright
uv run poe fix                # auto-fix lint; `format` to just format
uv run poe test               # all tests + coverage report
uv run poe test_unit          # tests/unit  (also: test_integration, test_smoke, test_verbs)
uv run poe test_notebook      # tests/notebook (runs with pytest-xdist -n auto)
uv run poe test_only "<expr>" # single test by -k pattern, e.g. test_only "test_create_cache"
```

CLI entrypoints (also exposed as the `graphrag` console script = `graphrag.cli.main:app`, a Typer app):

```shell
uv run poe init        # graphrag init  — generate starter settings.yaml + prompts in a root dir
uv run poe index       # graphrag index — build an index
uv run poe update      # graphrag update — incremental re-index
uv run poe query       # graphrag query — run a search
uv run poe prompt_tune # graphrag prompt-tune — auto-tune prompts to your corpus
```

- **Tests load `.env`** (`pytest-dotenv`); integration/smoke tests need real model credentials. Some storage/smoke tests need **Azurite** running (`./scripts/start-azurite.sh`).
- **CI** (`python-checks.yml`) runs `poe check` + `uv build --all-packages` on Python 3.11 & 3.13, Ubuntu & Windows.

## Architecture

### Factory + registration pattern (pervasive)

Every swappable component is built through a factory that exposes a `register(...)` classmethod, so users can plug in custom implementations: pipelines (`index/workflows/factory.py`), storage, cache, vector stores, table providers, loggers, and query engines all follow this shape. When adding a new backend for one of these, register it with the corresponding factory rather than branching on type.

### Indexing pipeline

`PipelineFactory` (`index/workflows/factory.py`) maps an `IndexingMethod` (`Standard`, `Fast`, `StandardUpdate`, `FastUpdate`) to an ordered list of **workflow names**, producing a `Pipeline` of `(name, WorkflowFunction)` pairs. Each workflow in `index/workflows/` is an async function `(config, context) -> WorkflowFunctionOutput`.

`run_pipeline` (`index/run/run_pipeline.py`) is the executor: it creates storage/cache/table-provider from config, builds a `PipelineRunContext` (storage + cache + callbacks + shared mutable `state`), then runs workflows **sequentially**, yielding a `PipelineRunResult` per workflow and persisting `stats.json` / `context.json` between steps. Tables move between workflows as pandas DataFrames read/written through a **`TableProvider`** (parquet by default). Workflows are stateful via the shared `state` dict; a workflow can set `stop` to halt the pipeline. Update runs write a timestamped delta index and merge it with a backed-up `previous` copy.

The Standard pipeline roughly: `load_input_documents → create_base_text_units → create_final_documents → extract_graph → finalize_graph → extract_covariates → create_communities → create_final_text_units → create_community_reports → generate_text_embeddings`. The **Fast** variant swaps LLM graph extraction for NLP-based noun-graph extraction (`extract_graph_nlp` + `prune_graph`).

### Query engine

Four strategies live in `query/structured_search/`: **local** (entity-centric), **global** (map-reduce over community reports), **drift** (iterative local+global), **basic** (vanilla RAG). The public API (`api/query.py`) exposes each as `<method>_search` and `<method>_search_streaming`. Indexed parquet tables are loaded into data-model objects via `query/indexer_adapters.py`.

### Public API vs internals

`packages/graphrag/graphrag/api/` is the supported library surface (`build_index`, the `*_search` functions, `generate_indexing_prompts`) and the CLI is the supported user surface — **both follow semver**. Everything else (workflows, operations, storage internals, etc.) is "internal" and may change between releases without a semver bump. See `breaking-changes.md`. Prefer building on `graphrag.api` and `graphrag.config` over reaching into internal modules.

### Config

`GraphRagConfig` (`config/models/graph_rag_config.py`) is the pydantic root model; per-feature models live in `config/models/`. `config/load_config.py` resolves `settings.yaml` + env vars. `graphrag init` emits a compatible starter config — **as of v3, the model layer is LiteLLM**, so model `type` is `chat`/`embedding` (the old `openai_chat` etc. are gone) and a `model_provider` (e.g. `openai`, `azure`) is required.

## Contributing mechanics

- **Every PR must include a semversioner change file**, or CI fails:
  ```shell
  uv run semversioner add-change -t <major|minor|patch> -d "<one sentence describing the change>"
  ```
- Run `uv run poe check` before pushing — it's the exact CI gate. Linting is strict ruff (numpy docstring convention, security `S` rules, etc.); tests are exempted from many rules via `per-file-ignores`.
- This is `microsoft/graphrag`; the data model and config are versioned carefully — when touching output tables or `settings.yaml` shape, check `breaking-changes.md` and consider the migration-notebook path.
