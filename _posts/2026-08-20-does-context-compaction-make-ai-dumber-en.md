---
layout: post
title: Does Context Compaction Make AI Coding Assistants Dumber?
date: 2026-08-20 12:00:00 +0800
description: An empirical analysis of ~400K real coding-agent turns (TraceLab + the author's own Codex / Claude Code logs). After compaction, correctness barely degrades — but the model pays an "efficiency tax," re-reading and re-editing to recover lost details.
tags: [llm, coding-agent, context-compaction, evaluation, methodology]
lang: en
translation_key: context-compaction
cite_key: qin2026compaction
subtitle: "An empirical analysis of ~400,000 real coding-agent turns"
---

Long-session AI coding assistants inevitably hit a wall: the context window. As a conversation grows, the system "compacts" the history into a summary to free up space. This raises a natural question: **after compaction, does the model still remember what it was doing? Does it get dumber?**

We analyzed three real datasets — an aggregated trace set from [TraceLab](https://github.com/uw-syfi/TraceLab) (UW SYFI; ~357K turns, 4,265 sessions), plus the author's own Codex (495 sessions) and Claude Code (5,856 sessions) raw logs. Along the way we fell into two methodological traps and reached some counter-intuitive conclusions.

## 0. Data: three mutually corroborating traces

| Source                                                                          | Scale                                      | Characteristics                                                 | Compact detection |
| ------------------------------------------------------------------------------- | ------------------------------------------ | --------------------------------------------------------------- | ----------------- |
| **[TraceLab](https://github.com/uw-syfi/TraceLab)** (UW SYFI aggregated traces) | 357,161 turns / 4,265 sessions / 23 models | Claude & GPT families; turn-level metadata, **no tool content** | token drop        |
| Author's own **Codex** logs                                                     | 495 sessions / 10,810 turns                | native `compacted` events + full command content                | native event      |
| Author's own **Claude Code** logs                                               | 5,856 sessions                             | full tool_use file paths + usage                                | token drop        |

TraceLab provides **cross-model breadth** (23 models) but only metadata; the two self-collected logs provide **content depth** (commands, file paths), letting us directly observe "re-read to recover" behavior. The three corroborate each other — no single dataset's conclusion stands alone.

## 1. Defining "capability": output tokens are a trap

The intuitive approach is to compare model "output" before and after compaction. We did this at first: many models' output tokens dropped sharply post-compact (claude-opus-4-8 by 52%), nearly leading us to conclude "severe degradation." **That was wrong.**

Before compaction the context is near the window limit, inflating output; after compaction the freed context yields shorter — possibly more efficient — responses. Using output tokens as capability mistakes "context pressure" for "capability." We switched to metrics closer to capability, defining each explicitly:

- **Error rate**: fraction of tool calls flagged as failed by the framework (e.g., non-zero Bash exit code). This is "tool execution failure," not "model answer wrong."
- **Recovery rate**: fraction of error rounds with no further error within 3 rounds — self-correction ability.
- **Blind retry**: retrying the same tool after an error while still erroring within 3 rounds — a failure loop; the strongest degradation signal.

## 2. The second trap: one bad session fabricated "severe degradation"

In TraceLab, claude-opus-4-8 looked terrible: post-compact error rate 8.8% → 21.6%, blind retry 14% → 40%. By any standard, "severe degradation." But we ran an **outlier sensitivity check** — removing the single session contributing the most errors and recomputing — and the conclusion flipped:

| Metric                  | With outlier | Removed |
| ----------------------- | -----------: | ------: |
| post-compact error rate |        21.6% |    7.7% |
| error-rate change       |      +12.9pp |  +0.1pp |
| blind retry             |          40% |      0% |

That session contributed 26% of the model's errors, with up to 18/21 tool calls failing in one round, and errors bursting both before and after compact — a broken environment, unrelated to compaction. **Lesson: for any small-sample conclusion, do a leave-one-out check first. A verdict that flips on one session is an artifact, not a finding.**

After checking all models, only two show robust post-compact correctness degradation: claude-opus-4-7 and gpt-5.4. The largest-sample model, gpt-5.5, stays stable throughout.

## 3. Our own data: correctness holds, but the model works harder

**Finding 1: correctness barely degrades.** Codex error/recovery/blind-retry are stable across compact; Claude's error rate even **drops** (haiku 13.5% → 1.3%) — degradation actually occurs _before_ compact (the "pressure" state near the limit); compaction resets it. Compact is relief, not harm.

**Finding 2: but the model is clearly more effortful.** Post-compact effort rises across sources: Codex tools/round doubles from 9.3 to 17.3, almost entirely edits (apply_patch 1432 → 3021); Claude reads increase ~45%.

## 4. Is it "recalling"? No — re-doing and compensating

Does the doubled tool use reflect active "recall," or just ordinary extra work? The content-rich self data lets us tell.

- Reads are a tiny share (&lt;3%), but their **nature changes**: ~48.5% of post-compact reads re-access files already seen before compact (vs 7.7% pre) — a genuine "lost detail → re-read to recover" signal.
- We caught it in the act: post-compact the model re-runs `sed -n` on an already-read `core.py`, and re-runs `rg "def generate_until"` to relocate a function it forgot.
- Edits: the re-edit rate of old files rises only slightly (59.8% → 63.5%), so the doubling is not mass "re-doing lost work" but more iterative convergence on the same hot files.

```text
compact loses some details
   → model notices; re-reads old files / relocates functions (compensate)
   → more edit iterations under incomplete info
   → final result still correct (correctness holds)
   → but ~2× the steps (the efficiency tax)
```

**Correctness holds precisely because the model compensates for lost details with extra effort.** Output quality didn't degrade; time cost did — like someone whose notes were compressed, re-checking the source and redrafting to keep quality, at the cost of time.

## 5. Limitations: the invisible is the dangerous part

- **Re-reads are only the "successfully compensated" part.** If the model loses a detail without noticing and proceeds on the summary (silent loss), telemetry can't catch it, yet it may cause subtle errors. "Correctness holds" is an observation, not zero risk.
- **TraceLab has no content**, so detail loss is unobservable there; only the self data can confirm it directly.
- **Causality isn't airtight.** Compact coincides with intensive editing phases; part of the effort rise is task rhythm.
- Results don't generalize to all models: in TraceLab, opus-4-7 and gpt-5.4 genuinely degrade.

## 6. Takeaways for practitioners

1. **Don't measure capability by output tokens**; use error/recovery metrics and define each explicitly.
2. **Run outlier checks on small samples**; a verdict that flips on one session is untrustworthy.
3. **Compact's real cost is efficiency, not correctness** — the model buys the result with more steps. Optimize summaries to retain "hot" information (frequently re-read files, key decisions) to cut the compensation cost.
4. **Beware silent loss**: visible re-reads are the tip of the iceberg; summary quality determines the invisible risk.

Compaction doesn't make models dumber — **same correctness, double the effort**.  
And the real danger was never the errors you can see, but the **details you lose without noticing**.
{: .ar-coda}

Data & methods in §0: [TraceLab](https://github.com/uw-syfi/TraceLab) aggregated traces (UW SYFI, 357,161 turns); the author's own Codex (495 sessions, native compacted events) and Claude Code (5,856 sessions, token-drop detection) logs.
{: .ar-fine}
