# GitHub Models & Copilot — Available Models, Free Allowances & Rate Limits

Reference for the C-A-B project. Two separate systems are relevant: **GitHub Models** (API access) and **GitHub Copilot** (IDE + chat). Both have free tiers.

Sources: [GitHub Models Billing](https://docs.github.com/en/billing/managing-billing-for-your-products/about-billing-for-github-models) · [Copilot Requests](https://docs.github.com/en/copilot/concepts/billing/copilot-requests) · [Copilot Plans](https://docs.github.com/en/copilot/concepts/billing/individual-plans) · [GitHub Models Prototyping](https://docs.github.com/github-models/prototyping-with-ai-models) · [Models Costs](https://docs.github.com/en/billing/reference/costs-for-github-models)

---

## Free Allowances Summary

### GitHub Models API (what our `demo_with_llm.py` uses)

| Item | What's Free |
|------|------------|
| **Access** | All GitHub accounts get rate-limited access to all models at no cost |
| **Models** | All listed models available within rate limits |
| **Limits** | Per-tier RPM/RPD (see tables below) — once exhausted, requests are blocked |
| **Paid upgrade** | Opt-in pay-as-you-go at $0.00001/token unit beyond free quota |

**Endpoint:** `https://models.inference.ai.azure.com/chat/completions`
**Auth:** `Authorization: Bearer <github_token>` (from `gh auth token`)

### GitHub Copilot Pro ($10/month)

| Item | What's Included |
|------|----------------|
| **Premium requests** | 300/month |
| **Included models (0 multiplier)** | GPT-5 mini, GPT-4.1, GPT-4o — unlimited use, no premium request cost |
| **Budget models (0.25–0.33x)** | Claude Haiku 4.5, Gemini 3 Flash, GPT-5.4 mini, Grok Code Fast 1 |
| **Standard models (1x)** | Claude Sonnet 4/4.5/4.6, Gemini 2.5/3/3.1 Pro, GPT-5.1/5.2/5.3/5.4 |
| **Premium models (3x)** | Claude Opus 4.5, Claude Opus 4.6 |
| **Experimental (30x)** | Claude Opus 4.6 fast mode |
| **Extra premium requests** | $0.04 each beyond 300/month |

---

## Copilot Model Multipliers (Premium Request Cost)

| Model | Multiplier (Pro) | Multiplier (Free) | 300 requests = |
|-------|:----------------:|:------------------:|:--------------:|
| **GPT-5 mini** | **0 (included)** | 1 | Unlimited |
| **GPT-4.1** | **0 (included)** | 1 | Unlimited |
| **GPT-4o** | **0 (included)** | 1 | Unlimited |
| Raptor mini | **0 (included)** | 1 | Unlimited |
| Grok Code Fast 1 | 0.25 | 1 | 1200 uses |
| Claude Haiku 4.5 | 0.33 | 1 | 909 uses |
| Gemini 3 Flash | 0.33 | N/A | 909 uses |
| GPT-5.4 mini | 0.33 | N/A | 909 uses |
| GPT-5.1 Codex (mini) | 0.33 | N/A | 909 uses |
| Claude Sonnet 4 / 4.5 / 4.6 | 1 | N/A | 300 uses |
| Gemini 2.5 Pro | 1 | N/A | 300 uses |
| Gemini 3 / 3.1 Pro | 1 | N/A | 300 uses |
| GPT-5.1 / 5.2 / 5.3 / 5.4 | 1 | N/A | 300 uses |
| Claude Opus 4.5 | 3 | N/A | 100 uses |
| Claude Opus 4.6 | 3 | N/A | 100 uses |
| Claude Opus 4.6 fast | 30 | N/A | 10 uses |

---

## GitHub Models API — All Available Models

| Model | Provider | Tier | Input ($/1M tokens) | Output ($/1M tokens) | Notes |
|-------|----------|:----:|:-------------------:|:--------------------:|-------|
| **GPT-4o** | OpenAI | High | $2.50 | $10.00 | Multimodal, cached input $1.25 |
| **GPT-4o mini** | OpenAI | Low | $0.15 | $0.60 | Best cost/perf, cached $0.08 |
| **GPT-4.1** | OpenAI | High | $2.00 | $8.00 | Latest GPT-4, cached $0.50 |
| **GPT-4.1 mini** | OpenAI | Low | $0.40 | $1.60 | Smaller GPT-4.1, cached $0.10 |
| **o1 / o3 / GPT-5** | OpenAI | Special | — | — | Reasoning, 1 RPM / 8 RPD |
| **o1-mini / o3-mini / o4-mini** | OpenAI | Special | — | — | 2 RPM / 12 RPD |
| **GPT-5 mini / nano** | OpenAI | Special | — | — | 2 RPM / 12 RPD |
| **DeepSeek-R1** | DeepSeek | Special | $1.35 | $5.40 | Open-weight reasoning |
| **DeepSeek-R1-0528** | DeepSeek | Special | $1.35 | $5.40 | Updated R1 |
| **DeepSeek-V3-0324** | DeepSeek | Special | $1.14 | $4.56 | Non-reasoning |
| **MAI-DS-R1** | Microsoft | Special | $1.35 | $5.40 | MS-hosted DeepSeek R1 |
| **Grok 3** | xAI | Special | $3.00 | $15.00 | 1 RPM / 15 RPD |
| **Grok 3 Mini** | xAI | Special | $0.25 | $1.27 | 2 RPM / 30 RPD |
| **Llama 4 Maverick 17B** | Meta | Low | $0.25 | $1.00 | Open-weight FP8 |
| **Llama 3.3 70B Instruct** | Meta | Low | $0.71 | $0.71 | Open-weight |
| **Phi-4** | Microsoft | Low | $0.13 | $0.50 | Small, fast |
| **Phi-4 mini instruct** | Microsoft | Low | $0.08 | $0.30 | Cheapest option |
| **Phi-4 multimodal** | Microsoft | Low | $0.08 | $0.32 | Vision + text |

---

## GitHub Models API — Rate Limits (Copilot Pro)

### Standard Tiers

| Tier | RPM | RPD | Input Tokens/Req | Output Tokens/Req | Concurrent |
|------|:---:|:---:|:----------------:|:-----------------:|:----------:|
| **Low** | 15 | 150 | 8,000 | 4,000 | 5 |
| **High** | 10 | 50 | 8,000 | 4,000 | 2 |
| **Embedding** | 15 | 150 | 64,000 | — | 5 |

### Special Tier Limits

| Model Group | RPM | RPD | Input/Output Tokens | Concurrent |
|-------------|:---:|:---:|:-------------------:|:----------:|
| o1, o3, GPT-5 | 1 | 8 | 4K / 4K | 1 |
| o1-mini, o3-mini, o4-mini, GPT-5 mini/nano | 2 | 12 | 4K / 4K | 1 |
| DeepSeek-R1 variants | 1 | 8 | 4K / 4K | 1 |
| Grok 3 | 1 | 15 | 4K / 4K | 1 |
| Grok 3 Mini | 2 | 30 | 4K / 8K | 1 |

---

## Practical Analysis for C-A-B Project

### What we can do for free

| Scenario | Model | Free Capacity | Enough? |
|----------|-------|:------------:|:-------:|
| **Dev/test one scenario** (35 turns) | GPT-4o mini (Low) | 150 RPD | 4 full runs/day |
| **Smoke test** (5 turns) | GPT-4o mini (Low) | 150 RPD | 30 runs/day |
| **Scenario S1+S2+S3** (105 turns) | GPT-4o mini (Low) | 150 RPD | 1 full suite + 45 spare |
| **CP4 user study** (10 users × 20 msgs) | GPT-4o mini (Low) | 150 RPD | Not enough (200 needed) |
| **Multi-model consensus** (3 models × 35 turns) | 3× Low tier | 150 RPD each | 1 run, tight |

### When we need paid

- **CP4 user study with 10+ participants** — exceeds 150 RPD on free tier
- **Parallel multi-model testing** — 3× models × S1/S2/S3 = 315 requests
- **Iterative red-team runs** — repeated scenario testing burns through daily quota

### Recommended setup

| Role | Model | System | Why |
|------|-------|--------|-----|
| VTuber persona (main LLM) | GPT-4o mini | GitHub Models API | $0.15/1M, 15 RPM, free tier covers dev |
| Copilot for coding | GPT-4.1 | Copilot Pro (included) | 0 multiplier, unlimited |
| Semantic classifier (future Dir.4) | Phi-4 mini | GitHub Models API | $0.08/1M, cheapest available |
| Red-team attacker | GPT-4.1 | GitHub Models API | Stronger reasoning |
| Baseline comparison | Same as persona | Same | Fair A/B with toggle |
