# Architecture of an LLM-Based Chatbot

A production chatbot is not "prompt in, text out" — that's a demo, not a system. A real architecture has to handle grounding (the model doesn't inherently know your data), memory (conversations carry state), safety (users will try to break it), and cost/latency (you can't call a flagship model for every token). Below is the architecture end-to-end: the components, why each exists, and the engineering decisions inside each one.

## High-Level Flow

```
User Input
   │
   ▼
[1] Interface Layer (web/app/voice/API)
   │
   ▼
[2] Input Processing (moderation, PII scrub, intent/language detection)
   │
   ▼
[3] Orchestration Layer  ◄──────────────┐
   │         │           │              │
   ▼         ▼           ▼              │
[4] Memory  [5] Retrieval [6] Tools/     │
 (short +    (RAG:         Agents        │
  long term)  vector DB,   (APIs, DB     │
              re-ranker)   calls, code)  │
   │         │           │              │
   └────┬────┴─────┬─────┘              │
        ▼          ▼                    │
   [7] Prompt Assembly (system prompt +  │
       context + retrieved docs + tools) │
        │                                │
        ▼                                │
   [8] LLM Core (inference)              │
        │                                │
        ▼                                │
   [9] Output Guardrails (fact-check,    │
       moderation, format validation) ───┘ (loop back if tool call needed)
        │
        ▼
   [10] Response Delivery (streaming, citations, UI rendering)
        │
        ▼
   [11] Logging / Eval / Feedback loop
```

The core design principle underneath this: **the LLM is a stateless reasoning engine you call repeatedly, not a system with memory or knowledge of its own.** Every property people associate with "the chatbot" — memory, grounding, personality, safety — is actually implemented *outside* the model, in the scaffolding around it.

---

## 1. Interface Layer

Channel-agnostic entry point (web widget, Slack, WhatsApp, voice via ASR/TTS). This is where wildly different input formats — text, voice, structured form submissions — get normalized into a single internal message schema before anything downstream has to reason about them.

## 2. Input Processing

Before anything touches the LLM:

- **Language ID + normalization** — routes to language-specific prompts or a translation pre-step if the base model is weaker in that language.
- **PII detection and redaction** — regex + NER (e.g. Presidio) to mask sensitive data before logging or sending to a third-party API, for GDPR/HIPAA compliance.
- **Cheap moderation pass** — a lightweight classifier (Llama Guard, a distilled BERT model) catches obvious abuse before an expensive model call is made. This is purely a cost-control step: you don't want to pay flagship-model prices to generate a refusal.
- **Query rewriting** — resolving coreference ("what about *that*?") into a self-contained query before retrieval, usually via a small, fast LLM call separate from the main generation.

## 3. Orchestration Layer — the actual engineering core

This decides, per turn: does this need retrieval? A tool call? Is it simple enough for a cheap model? It's implemented as one of three patterns, in increasing complexity:

| Pattern              | How it works                                                                   | When to use               |
| -------------------- | ------------------------------------------------------------------------------ | ------------------------- |
| Fixed pipeline       | Always: retrieve → assemble → generate                                       | Simple Q&A, narrow domain |
| Router / classifier  | A cheap classifier picks a path (RAG / tool-call / direct-answer / escalate)   | Multi-intent bots         |
| Agentic loop (ReAct) | LLM decides turn-by-turn: Thought → Action → Observation, until final answer | Complex, multi-step tasks |

The ReAct loop concretely:

```
Thought: I need the user's order status before I can answer.
Action: call_tool("get_order_status", {"order_id": "12345"})
Observation: {"status": "shipped", "eta": "Sept 20"}
Thought: I now have enough info to respond.
Final Answer: Your order shipped and should arrive by Sept 20.
```

The orchestrator parses each `Action`, executes it against the real backend, and re-injects the `Observation` for the next call. The key architectural decision is whether state transitions are **explicit** (a graph you define — predictable, easy to guardrail) or **implicit** (the LLM decides freely — flexible, harder to bound). Most production systems converge on explicit graphs with local LLM decisions at fixed nodes, because a fully free-form loop is genuinely hard to keep reliable and cheap.

**Model cascading** also lives here: a router (often a near-zero-cost fine-tuned classifier) tags query complexity, and only "hard" queries reach the expensive model — since real chatbot traffic is heavily skewed toward simple, repetitive intents, this alone can cut inference cost 40–70%.

### What feeds into the orchestrator

```
   Memory          Retrieval (RAG)      Tools / agents
 (short + long) (vector search+rerank)  (function calls)
       │                 │                    │
       └────────┬────────┴─────────┬──────────┘
                ▼                  ▼
              Prompt assembly (token-budgeted context)
                          │
                          ▼
                       LLM core
```

Each source competes for a shared, finite token budget — none of them get to write to the prompt unconditionally.

## 4. Memory

**Short-term (working memory).** Naive full-history concatenation breaks down fast: context windows fill, and cost scales with every resent token. Production patterns instead use a sliding window (keep last *N* turns verbatim, drop the rest), rolling summarization (compress older turns periodically via a separate LLM call, most common in practice), or token-budgeted truncation.

**Long-term (persistent memory).** Two distinct stores, often conflated:

- *Structured facts* (name, preferences, account tier) — a plain key-value or relational store, fetched deterministically. Don't use a vector DB for things you can look up exactly.
- *Episodic memory* (past conversation summaries) — embedded and stored in a vector DB, retrieved by similarity against the current query — same mechanism as RAG below.

Write policy matters as much as read policy: a separate process (often an end-of-conversation LLM call) decides what's worth remembering, or long-term memory fills with noise and retrieval precision degrades.

## 5. Retrieval-Augmented Generation (RAG) — usually the highest-leverage component

**Ingestion:**

1. **Chunking** — semantic chunking (split on section/header boundaries) or recursive splitting with ~10–20% overlap generally beats naive fixed-size chunks, which cut facts mid-sentence.
2. **Embedding** — general-purpose models (`text-embedding-3`, `bge-large`, `e5-mistral`) work for general text, but domain-specific fine-tuning of the embedding model often yields bigger accuracy gains than swapping the generator model.
3. **Indexing** — vector DB (pgvector at smaller scale; Pinecone/Weaviate/Milvus at larger scale), storing metadata (source, timestamp, permissions) for filtering.

**Query time:**

1. **Hybrid search** — dense vector similarity alone underperforms on exact-match cases (SKUs, names, numbers). Combining with sparse retrieval (BM25) via Reciprocal Rank Fusion is often the single biggest recall improvement available.
2. **Re-ranking** — retrieve top-50 cheaply via vector search, then re-rank with a cross-encoder (`bge-reranker`, Cohere Rerank) for the true top-5. Cross-encoders score query+doc jointly and are far more accurate than cosine similarity, but too slow to run over a full corpus — hence the two-stage retrieve-then-rerank pattern.
3. **Context injection with citations** — inject retrieved chunks with source tags, instructing the model to answer only from provided context. This is what output-side hallucination checking later verifies against.

Design against "lost in the middle" — models attend less to context buried mid-prompt. Keep retrieved context short and highly relevant rather than stuffing in everything that fits.

## 6. Tools / Function Calling

The model emits a structured call matching a JSON schema instead of free text:

```json
{ "name": "check_order_status", "parameters": {"order_id": {"type": "string"}} }
```

Practical guardrails: always validate emitted arguments against the schema before execution (models hallucinate malformed arguments more than expected); insert a human-confirmation checkpoint before destructive/irreversible actions (cancel order, send email) rather than letting an agent loop execute side effects autonomously; and truncate/summarize large tool results before feeding them back in, or they blow the next turn's token budget.

## 7. Prompt Assembly

Treat prompts as versioned, tested artifacts, not inline strings. A typical assembly order: system prompt → long-term memory facts → retrieved RAG chunks → conversation summary → recent turns → current query → tool schemas — instructions closest to the query tend to be followed most reliably. Token budget allocation is a real constraint: e.g., of a 16K window, reserve ~2K for system prompt, 4K for RAG context, 6K for history, leaving headroom for output.

## 8. LLM Core

**Hosted API vs. self-hosted:**

| Factor                    | Hosted API (GPT/Claude/Gemini)      | Self-hosted open-weight (Llama, Mistral, Qwen)   |
| ------------------------- | ----------------------------------- | ------------------------------------------------ |
| Time-to-production        | Fast                                | Slower (infra, serving stack)                    |
| Data residency/compliance | Vendor-dependent                    | Full control                                     |
| Cost at scale             | Per-token, can get expensive        | Fixed infra cost, cheaper at very high volume    |
| Fine-tuning flexibility   | Limited                             | Full (LoRA/QLoRA, full fine-tune)                |
| Quality ceiling           | Generally higher on frontier models | Closing gap, usually behind on complex reasoning |

Self-hosted serving relies on inference engines built for throughput — vLLM or TGI, using continuous batching and a shared KV cache — the difference between naive `generate()` calls and something that serves real production traffic.

**Fine-tuning vs. prompting vs. RAG**, the decision most often confused: need the model to *know* facts → RAG, not fine-tuning (fine-tuning teaches style/behavior, not reliable fact recall, and facts go stale). Need a consistent tone/format → light fine-tuning (LoRA) or strong system prompting. Need narrow task specialization (structured extraction from one document type) → fine-tuning earns its cost.

## 9. Output Guardrails

Two checks after generation, separate from input-side moderation:

- **Faithfulness/hallucination check** — a secondary, often cheaper LLM call verifies claims are entailed by the retrieved context (NLI-style), the technique behind evaluation frameworks like RAGAS.
- **Policy/format validation** — schema validation for structured output, plus a moderation pass on the generated text itself, since models can be jailbroken into producing bad output even from a clean input.

## 10–11. Response Delivery & Observability

Token streaming for perceived latency; citation rendering. On the backend, every conversation is logged (with privacy controls) and fed into an offline eval set (regression-tested on every prompt/model change) plus online signals — thumbs up/down, abandonment, rephrase-rate as an implicit failure signal. Semantic caching (via embedding similarity, not exact string match) cuts cost and latency on repeat questions in FAQ-heavy bots. Without this loop, quality drift is invisible until users complain.

---

## Latency Budget

Architecture, not just model choice, drives perceived speed. A single RAG-backed turn:

```
Moderation check                         ~50ms
Query embedding                          ~30ms
Vector search                            ~50ms
Re-ranking                               ~100ms
Prompt assembly                          ~5ms
LLM generation (streamed, first token)   ~300–800ms
──────────────────────────────────────────────
Time to first token                      ~600–1000ms
```

Every retrieval/reranking/tool-call step adds serial latency unless parallelized — this is why streaming is a first-class architectural requirement, not a UI nicety.

---
