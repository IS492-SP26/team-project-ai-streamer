# GitHub Models — Available Models & Rate Limits for Pro Plan

Reference for the C-A-B project. All models accessible via GitHub Models API with a GitHub Pro subscription, using `gh auth token` for authentication.

**Endpoint:** `https://models.inference.ai.azure.com/chat/completions`
**Auth:** `Authorization: Bearer <github_token>`

Sources: [GitHub Models Billing](https://docs.github.com/en/billing/reference/costs-for-github-models) · [GitHub Models Prototyping](https://docs.github.com/github-models/prototyping-with-ai-models)

---

## All Available Models

| Model | Provider | Tier | Input Cost ($/1M tokens) | Output Cost ($/1M tokens) | Notes |
|-------|----------|------|:------------------------:|:-------------------------:|-------|
| **GPT-4o** | OpenAI | High | $2.50 | $10.00 | Flagship multimodal, cached input $1.25 |
| **GPT-4o mini** | OpenAI | Low | $0.15 | $0.60 | Best cost/performance ratio, cached $0.08 |
| **GPT-4.1** | OpenAI | High | $2.00 | $8.00 | Latest GPT-4 series, cached $0.50 |
| **GPT-4.1 mini** | OpenAI | Low | $0.40 | $1.60 | Smaller GPT-4.1, cached $0.10 |
| **o1** | OpenAI | Special | — | — | Reasoning model, very low rate limits |
| **o1-mini** | OpenAI | Special | — | — | Smaller reasoning model |
| **o1-preview** | OpenAI | Special | — | — | Preview reasoning model |
| **o3** | OpenAI | Special | — | — | Advanced reasoning |
| **o3-mini** | OpenAI | Special | — | — | Smaller o3 |
| **o4-mini** | OpenAI | Special | — | — | Latest reasoning mini |
| **GPT-5** | OpenAI | Special | — | — | Frontier model, 1 RPM / 8 RPD |
| **GPT-5 mini** | OpenAI | Special | — | — | Smaller GPT-5 |
| **DeepSeek-R1** | DeepSeek | Special | $1.35 | $5.40 | Open-weight reasoning model |
| **DeepSeek-R1-0528** | DeepSeek | Special | $1.35 | $5.40 | Updated R1 |
| **DeepSeek-V3-0324** | DeepSeek | Special | $1.14 | $4.56 | Non-reasoning variant |
| **MAI-DS-R1** | Microsoft | Special | $1.35 | $5.40 | Microsoft-hosted DeepSeek R1 |
| **Grok 3** | xAI | Special | $3.00 | $15.00 | xAI flagship, 1 RPM / 15 RPD |
| **Grok 3 Mini** | xAI | Special | $0.25 | $1.27 | Smaller Grok, 2 RPM / 30 RPD |
| **Llama 4 Maverick 17B** | Meta | Low | $0.25 | $1.00 | Open-weight, FP8 quantized |
| **Llama 3.3 70B Instruct** | Meta | Low | $0.71 | $0.71 | Open-weight, strong general performance |
| **Phi-4** | Microsoft | Low | $0.13 | $0.50 | Small model, fast |
| **Phi-4 mini instruct** | Microsoft | Low | $0.08 | $0.30 | Very small, lowest cost |
| **Phi-4 multimodal** | Microsoft | Low | $0.08 | $0.32 | Vision + text |

---

## Rate Limits by Tier (Copilot Pro)

| Tier | RPM | RPD | Input Tokens/Req | Output Tokens/Req | Concurrent |
|------|:---:|:---:|:----------------:|:-----------------:|:----------:|
| **Low** | 15 | 150 | 8,000 | 4,000 | 5 |
| **High** | 10 | 50 | 8,000 | 4,000 | 2 |
| **Embedding** | 15 | 150 | 64,000 | — | 5 |

### Special Tier Limits (Pro)

| Model Group | RPM | RPD | Input Tokens/Req | Output Tokens/Req | Concurrent |
|-------------|:---:|:---:|:----------------:|:-----------------:|:----------:|
| o1, o3, GPT-5 | 1 | 8 | 4,000 | 4,000 | 1 |
| o1-mini, o3-mini, o4-mini, GPT-5 mini/nano | 2 | 12 | 4,000 | 4,000 | 1 |
| o1-preview | 1 | 8 | 4,000 | 4,000 | 1 |
| DeepSeek-R1 variants | 1 | 8 | 4,000 | 4,000 | 1 |
| Grok 3 | 1 | 15 | 4,000 | 4,000 | 1 |
| Grok 3 Mini | 2 | 30 | 4,000 | 8,000 | 1 |

---

## Recommended Models for C-A-B Project

| Use Case | Recommended Model | Why |
|----------|------------------|-----|
| **VTuber persona (main LLM)** | GPT-4o mini | Best cost/perf ratio, 15 RPM handles chat volume, $0.15/1M input |
| **Semantic risk classifier (Direction 4)** | Phi-4 mini | Cheapest ($0.08/1M), fast, sufficient for binary classification |
| **Multi-model consensus (Direction 7)** | GPT-4o mini + Llama 3.3 70B + Phi-4 | 3 providers, all Low tier (15 RPM each), diverse failure modes |
| **Red-team attacker model** | GPT-4.1 | Stronger reasoning for generating adversarial scripts |
| **Baseline comparison** | GPT-4o mini | Same model with/without C-A-B for fair comparison |

---

## Practical Constraints for Our Project

- **Free tier is viable for development/testing** — 150 RPD on Low tier models covers 4+ full scenario runs (35 turns × 4 = 140 requests)
- **Paid tier needed for user study** — CP4 user study with 10+ participants sending 20+ messages each = 200+ requests per session
- **Special tier models (o1, GPT-5, DeepSeek-R1) are impractical** — 1 RPM / 8 RPD is too slow for interactive demo
- **Concurrent request limit matters** — Low tier allows 5 concurrent, which supports multi-model consensus voting without sequential bottleneck
- **Token limits are adequate** — 8K input / 4K output per request covers our use case (chat messages are typically <200 tokens, system prompt ~150 tokens)
