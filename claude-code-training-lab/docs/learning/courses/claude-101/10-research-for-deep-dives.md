# Lesson 10: Research for Deep Dives

- **Course:** Claude 101 (lesson 10 of 13, ~10 min)
- **Source:** https://academy.claude.com/courses/claude-101/research-mode-for-deep-dives
- **Date:** 2026-10-13
- **Status:** In progress

All exercises use ReviewRadar as the topic and are done on Claude.ai.

## Setup (do once)

In a new chat, click **+** (lower left) and turn on **Web search**. **Research** is selected from the same menu and only works with web search on. A Research run takes minutes, so do Ex 2 once.

## Exercises

### Ex 1: Which tool for which question?

**Where:** Claude.ai (regular chat, no Research)

Expected answers (check yourself):

| # | Question | Expected |
|---|----------|----------|
| 1 | What is the current price of the Claude API for Sonnet 5.5? | Web search (quick, specific fact) |
| 2 | Is `select_related` or `prefetch_related` right for Branch to Reviews? | Thinking (reasoning, no outside info) |
| 3 | What did we decide about the Review model in our internal docs? | Enterprise search (internal knowledge) |
| 4 | Compare review-management tools for multi-branch clinics: features, pricing, sentiment support | Research (multi-source, citations) |
| 5 | Why does this pytest fail with a Django ORM error? | Thinking |
| 6 | Summarize regulations on storing customer reviews that contain personal data, with sources | Research |

**Initial prompt:**
```
Should I use web search, thinking, enterprise search, or Research for these? 1) Current Claude API price for Sonnet 5.5. 2) select_related vs prefetch_related for Branch to Reviews. 3) Our internal decision about the Review model. 4) Compare review-management tools for clinics. 5) Why a pytest fails with a Django ORM error. 6) Regulations on storing reviews with personal data.
```
**Link:**

**Improved prompt** (new chat):
```
Claude has four ways to find or work out answers. Web search: a quick, specific fact. Thinking: reasoning-based problems (math, code, logic) that need no outside information. Enterprise search: an organization's internal knowledge. Research: multi-source, multi-step investigations that produce a cited report and take minutes.

For each question, pick one and give a one-line reason.

1) Current Claude API price for Sonnet 5.5.
2) Is select_related or prefetch_related right for Branch to Reviews?
3) What did we decide about the Review model in our internal docs?
4) Compare review-management tools for multi-branch clinics: features, pricing, sentiment support.
5) Why does this pytest fail with a Django ORM error?
6) Summarize regulations on storing customer reviews that contain personal data, with sources.

Output: a table with columns # | Tool | Reason.
```
**Link:**

### Ex 2: Run Research

**Where:** Claude.ai (new chat, **+** > Research on, web search on)

**Initial prompt:**
```
Research review management tools.
```
**Link:**

**Improved prompt** (new chat):
```
I am deciding whether to build ReviewRadar or recommend an existing product to a 3-branch clinic chain. Research the main review-management products used by clinics and spas. For each product, cover: core features, multi-branch support, sentiment analysis, reply suggestions, and pricing. Constraints: only products with public pricing or clear pricing tiers, sources from the last 2 years, English-language sources. Structure: summary (5 lines), comparison table, gaps a custom-built tool could fill, and a recommendation. Cite a source for every claim.
```
**Link:**

Then open at least 3 cited sources and check that they say what the report claims.

### Ex 3: Refine the research question first

**Where:** Claude.ai (regular chat, no Research)

**Initial prompt:**
```
Write me a research prompt about sentiment classification.
```
**Link:**

**Improved prompt** (new chat):
```
I want to research how accurate LLM sentiment classification is on customer reviews written in English and Vietnamese, to decide whether ReviewRadar needs a fine-tuned model. Help me write a strong Research prompt. First ask me up to 5 questions about my goal, constraints, and the structure I want, then write the final prompt.
```
**Link:**

## Key takeaways

- **Research** turns Claude into a systematic investigator: it plans with Thinking, runs many searches that build on each other, synthesizes a report, and **cites sources**. A run takes minutes.
- Turn it on with **+** > **Research**; **web search must be on**.
- Choose the right tool:
  - **Web search:** a quick, specific fact.
  - **Thinking:** reasoning (math, code debugging, logic) with no outside information.
  - **Enterprise search:** internal organizational knowledge.
  - **Research:** multi-source, comprehensive, cited reports.
- Good Research prompts: **specific goal** (the decision you need), **structure** (sections), **constraints** (budget, dates, geography), and optionally have Claude **refine the prompt** before you run it.
- With connectors (Google Workspace, Slack), Research can combine internal context with web research: "Pull relevant context from my Google Drive."
- Verify citations yourself on important claims; you stay accountable (Diligence).
