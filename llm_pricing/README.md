# AI Pricing & Token Costs

This directory centralizes the pricing configuration for the LLMs used in our clipping project. The `llm_pricing.json` file is used by the application to dynamically calculate token usage costs.

> 🎁 **Free Credits:** We currently have **$300** in free credits for LLM API usage.

---

## 📏 Understanding Tokens

* **Rule of Thumb:** In plain English, **1 token represents roughly ¾ of a word** (or 100 tokens $\approx$ 75 words).
* **1,000,000 (1M) tokens** is approximately 750,000 words. To put that into perspective, 1M tokens translates to roughly **1,500 to 3,000 pages** of standard text.

---

## Supported Models & Costs

> **Note:** All prices are in USD ($) and represent the cost per **1 Million (1M) tokens**.
> *Last updated: 03/20/2026*

| Model | Input Price (per 1M) | Output Price (per 1M) | Notes |
| :--- | :--- | :--- | :--- |
| `gemini-2.5-flash-lite` | $0.10 | $0.40 | Highly cost-effective for simple tasks. |
| `gemini-2.5-flash` | $0.30 | $2.50 | Standard model for general processing. |
| `gemini-2.5-pro` | $1.25 / $2.50* | $10.00 / $15.00* | *Higher rate applies for long contexts (>200k tokens). |
| `gemini-3.1-flash-lite-preview` | $0.25 | $1.50 | Latest preview of the flash-lite tier. |
| `gemini-3-flash-preview` | $0.50 | $3.00 | Latest preview of the flash tier. |
| `gemini-3.1-pro-preview` | $2.00 / $4.00* | $12.00 / $18.00* | *Higher rate applies for long contexts (>200k tokens). |