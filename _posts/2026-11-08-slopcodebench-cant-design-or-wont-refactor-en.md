---
layout: post
title: Can't Design or Won't Refactor? Dissecting Code Erosion in SlopCodeBench
date: 2026-11-08 12:00:00 +0800
description: We reproduced and extended SlopCodeBench on GLM-5.3-flash and Claude Opus 5.5. Agents can refactor but don't do it unprompted; a day-one anti_slop prompt flattens the degradation slope and cut total cost by 39% on a long-horizon task.
tags: [llm, coding-agent, code-quality, benchmark, evaluation]
lang: en
translation_key: slopcodebench-erosion
cite_key: qin2026slopcode
dollar_math: false
toc_labels:
  "3. Claude Opus 5.5 Comparison & Where Complexity Accumulates": "Where complexity accumulates"
  "1. Zero Spontaneous Refactoring Under Default Prompting": "Zero spontaneous refactoring"
  "Finding 1: Mid-Course Refactoring Decays on Hard Tasks, and Periodic Refactoring Breaks Correctness": "Finding 1: Periodic refactoring backfires"
  "Finding 2: Continuous anti_slop Flattens the Degradation Slope — Directly Contradicting the Paper's Conclusion": "Finding 2: anti_slop flattens the slope"
  "4. Step 3: Counterfactual Checkpoint Splicing — Proving Path Dependence": "Step 3: Checkpoint Splicing"
  "9. Conclusion & Takeaways for Practitioners": "Takeaways"
  "8. Bonus: Three Upstream Harness Bugs Uncovered": "Bonus: Harness bugs"
subtitle: "Five controlled experiments on code erosion in long-horizon coding agents"
---

The recently released [SlopCodeBench](https://arxiv.org/abs/2603.24755) (Orlanski et al., arXiv:2603.24755) highlights a painful reality for AI-assisted software engineering: across multi-step iterative tasks, coding agents relentlessly patch existing files rather than refactoring, causing severe structural degradation (Code Erosion). More pessimistically, the paper concludes that **explicit quality prompts only improve initial code quality without affecting degradation rates, while increasing per-checkpoint cost**.

We reproduced and extended SlopCodeBench on GLM-5.3-flash and Claude Opus 5.5 using five controlled counterfactual experiments: **Iterative vs. One-Shot, Checkpoint Splicing, Isolated Refactor-Only, Periodic Exogenous Refactoring, and Continuous Endogenous Constraints (`anti_slop`)**. Our findings challenge several key attributions of the original paper:

1. **The Metric Illusion**: The paper's primary proportional metric (`erosion`) suffers from a Denominator Dilution Paradox and a Threshold Cliff at complexity > 10. Relying on `erosion` alone masks severe monster-function growth and mismeasures the true slope of prompt interventions.
2. **Iterative Bloat & Entrypoint Accumulation**: After aligning one-shot evaluations with the full historical regression suite, iterative development writes 20%–30% more SLOC (p = 0.03) at 2× the time and cost of one-shot generation, concentrating complexity inside the `main()` entrypoint.
3. **Won't Refactor ≠ Can't Refactor**: Under default `just-solve` prompting, Opus 5.5 performed 0 spontaneous refactorings across 25 checkpoint transitions. Yet when given an isolated `refactor_only` prompt, it succeeded 6/6 times with zero test regressions, slashing peak function complexity from 28–34 down to 8–13. Code rot is not an inability to engineer software; it is a rational Minimal-Invasive Patching strategy under cross-checkpoint amnesia and hidden regression tests.
4. **Endogenous Discipline Beats Exogenous Surgery (and Saves 39% in Cost)**: On Opus 5.5, applying `anti_slop` from Checkpoint 1 did not merely shift the intercept—it flattened the 8-checkpoint peak function complexity growth to 0 to +6 (vs. +14 to +54 under `just-solve`). Even more surprisingly, on the complex 8-checkpoint `circuit_eval` task, `anti_slop` reduced total cost by 39% ($13.12 vs. $21.40) by avoiding late-stage technical debt interest. Conversely, periodic exogenous refactoring doubled the cost ($43.58) and triggered cross-checkpoint regressions (pass rate dropped from 99.8% to 90.5%).

## 1. Motivation: Do Coding Agents Really Suffer from Irreversible Architectural Decay?

Anyone who has used Claude Code, Cursor, or OpenCode on a multi-day project knows the pattern: ask an agent to build a greenfield tool (Checkpoint 1), and it produces clean, idiomatic code. Ask it to add the 4th, 5th, and 8th incremental feature, and it almost never refactors its earlier abstractions. Instead, it piles `if-elif` branches into the entrypoint and duplicates helper logic until the repository collapses into unmaintainable spaghetti—"[slop](https://gabeorlanski.github.io/posts/slop-code-bench/)."

To quantify this phenomenon, Orlanski et al. introduced [SlopCodeBench](https://www.scbench.ai/), a benchmark of 36 multi-checkpoint software problems. Each checkpoint launches in a fresh container where only the working directory persists—the agent sees the new specification and the existing code, but neither the previous conversation history nor the prior regression test suite.

The original paper drew three sobering conclusions:

1. **Iterative Degradation is Ubiquitous**: Structural erosion and verbosity worsen in 77%–80% of trajectories (e.g., Opus 4.7's `main()` on `forge` grows 7× in cyclomatic complexity across 8 checkpoints; [NeurIPS 2026](https://neurips.cc/virtual/2026/poster/138903)).
2. **Early Structure Locks In Fate**: Without upfront modularity, early structural shortcuts compound across subsequent checkpoints.
3. **Prompts Move the Intercept, Not the Slope (The Central Claim)**: Testing an explicit `anti_slop` prompt, the authors concluded that it "reduces initial structural erosion by up to 62.3%... without affecting degradation rates (+1.3 percentage points per checkpoint), while increasing per-checkpoint cost by 12.1%" (see also [this discussion on Medium](https://medium.com/@jacksonfdam/your-agents-code-rots-the-discourse-about-it-rots-faster-8b09adff4b79)).

Reading the paper left us with a nagging question: **Are frontier models genuinely incapable of maintaining modularity across a 1,000-line codebase—or is something else driving both the observed rot and the apparent failure of quality prompts?**

To find out, we set up SprocketLab/slop-code-bench (v1.0) using Claude Code (v2.1.44) as a unified harness and conducted a systematic causal dissection across GLM-5.3-flash and Claude Opus 5.5.

## 2. Step 1: Calibrating the Ruler — What Is "Function Complexity," and Why Does erosion Mislead?

Before diving into the data, let's establish a quick, intuitive scale for Function Complexity (formally known in software engineering as Cyclomatic Complexity, or CC):

> 💡 **A 30-Second Guide to Function Complexity (CC)**: Think of it as the number of independent decision paths inside a single function (every `if`, `elif`, `for`, `while`, `and/or`, or `case` adds +1 to the score).
>
> - **Complexity 1–10**: Clean, focused, easy-to-test functions (the standard industry threshold);
> - **Complexity 11–20**: Moderately complex functions that are getting harder to reason about;
> - **Complexity > 20**: Bloated, high-risk functions with deep nesting and tangled responsibilities;
> - **Complexity > 50**: A catastrophic "God Function" where dozens of branches are braided together—touching one line risks breaking everything.
>
> Throughout this post, we track the single most complex bottleneck function in the codebase, which we call **Peak Function Complexity (Max CC)**.

We began by reproducing the paper's flagship example under default `just-solve` prompting. On `forge` (8 checkpoints), Claude Opus 5.5 (`thinking=high`) clearly exhibited entrypoint bloat:

| Checkpoint   | Tests Passed | SLOC | Peak Function Complexity (Max CC) | `main()` Lines / Complexity |
| ------------ | ------------ | ---: | --------------------------------: | --------------------------- |
| Checkpoint 1 | 38 / 40      |  238 |                                21 | 36 lines / 15               |
| Checkpoint 4 | 136 / 142    |  562 |                                33 | 47 lines / 19               |
| Checkpoint 8 | 271 / 295    | 1138 |                                49 | 117 lines / 49              |

However, when we inspected the paper's primary metric—`erosion` (Structural Erosion)—we noticed a striking anomaly:

- On `forge`, while Peak Function Complexity surged from 21 to 35–49, the paper's `erosion` metric dropped from 0.78 to 0.69.
- On `code_search`, Opus 5.5's `erosion` plummeted from 0.82 down to 0.49!

Was the model spontaneously refactoring its code as it iterated? We initially thought so—until we inspected the AST function-by-function and retracted that hypothesis. **Not a single function had been split or deleted, and Peak Function Complexity had actually climbed from 18 to 32.**

Why did `erosion` improve while the largest functions grew worse? The answer lies in the paper's mathematical definition of `erosion`, which measures the proportion of complexity mass held by functions with complexity > 10 ([Hugging Face](https://huggingface.co/papers/2603.24755)):

<div class="ar-math mathjax_process">\[\mathrm{Erosion} = \frac{\sum_{f:\,\mathrm{CC}(f)&gt;10} \mathrm{mass}(f)}{\sum_{f} \mathrm{mass}(f)}, \qquad \text{where } \mathrm{mass}(f) = \mathrm{CC}(f) \times \sqrt{\mathrm{SLOC}(f)}\]</div>

Because `erosion` is a thresholded ratio, it suffers from two severe measurement artifacts:

1. **The Denominator Dilution Paradox**: In Checkpoint 3 of `code_search`, the agent added 24 tiny helper functions (complexity ≤ 3). Because all functions enter the denominator, a burst of trivial helpers dilutes the share of high-complexity functions, creating an illusion of structural healing even as the core dispatcher balloons.
2. **The Threshold Cliff at Complexity > 10**: Because the numerator only counts functions with complexity > 10, a prompt like `anti_slop` that keeps early functions at ≤ 10 scores a perfect 0.00 at Checkpoint 1. If a single function nudges from 10 to 11 in Checkpoint 4, `erosion` jumps discontinuously from 0.00 to 0.10+, inflating the measured slope.

Consequently, we use **absolute AST metrics—Peak Function Complexity (Max CC) and counts of bloated functions (Complexity ≥ 10 and ≥ 20)**—as our primary indicators, while reporting the paper's `erosion` and `verbosity` alongside them.

## 3. Step 2: Iterative vs. One-Shot — Is Complexity Inherent to the Spec or Induced by Iteration?

Before dissecting multi-step degradation, we must rule out a baseline hypothesis: Is final checkpoint complexity high simply because the full specification is complex, or is it specifically induced by step-by-step iterative patching?

### 1. Fixing the Evaluation Gap: Full-Suite Regression Alignment

In the upstream repository, One-Shot mode concatenates all checkpoint specifications into a single prompt and evaluates against the final checkpoint's test suite—omitting earlier checkpoints' regression tests. Using `eval-snapshot`, we re-evaluated all One-Shot outputs against the **complete test suite (including all historical regression tests)** to ensure an apples-to-apples comparison.

### 2. 14 Paired Runs on GLM-5.3-flash (6 Problems)

Under identical configurations (Claude Code 2.1.44, `thinking=none`, `just-solve`), we ran 14 paired Iterative vs. One-Shot comparisons across 6 problems on GLM-5.3-flash:

| Metric                            | Iterative | One-Shot | Paired Diff (One-Shot − Iterative, Mean ± SE) | One-Shot Wins |
| --------------------------------- | --------: | -------: | --------------------------------------------: | ------------: |
| Full Test Suite Pass Rate         |     81.9% |    85.4% |                                  +3.6pp ± 1.1 |       10 / 14 |
| Lines of Code (SLOC)              |      1756 |     1378 |                                    −379 ± 171 |       11 / 14 |
| Peak Function Complexity (Max CC) |      53.2 |     42.4 |                                   −10.8 ± 5.4 |       11 / 14 |
| `erosion` (Paper Ratio Metric)    |     0.720 |    0.721 |                                +0.001 ± 0.034 |        7 / 14 |
| Cost (CNY)                        |     ¥3.86 |    ¥1.84 |                                  −2.03 ± 0.48 |       13 / 13 |
| Wall-Clock Time (min)             |   173 min |   78 min |                                      −95 ± 22 |       14 / 14 |

(Note: When comparing the best-of-3 runs per problem, the pass rate gap vanishes to +0.1pp, indicating that correctness differences are not robust.)

Controlling for specification coverage by restricting to the 13 pairs where both modes completed 100% of checkpoints, a permutation test confirms significant iterative code bloat:

| Controlled Comparison (100% Spec Coverage) | Iterative − One-Shot Diff | Iterative Larger | Permutation Test p-value |
| ------------------------------------------ | ------------------------: | ---------------: | ------------------------ |
| Lines of Code (SLOC)                       |                +414 lines |          11 / 13 | 0.03 (Significant Bloat) |
| `erosion`                                  |                    −0.001 |           7 / 13 | 0.98                     |
| `verbosity`                                |                    +0.044 |           9 / 13 | 0.52                     |

### 3. Claude Opus 5.5 Comparison & Where Complexity Accumulates

We replicated the Iterative vs. One-Shot comparison on Claude Opus 5.5 across `forge` (3 pairs) and `code_search` (1 pair):

| Problem       | Pairs   | Pass Rate (Iterative / One-Shot) | Complex Functions Count (CC ≥ 10, Iterative / One-Shot) | SLOC (Iterative / One-Shot) |
| ------------- | ------- | -------------------------------- | ------------------------------------------------------- | --------------------------- |
| `forge`       | 3 pairs | 91.1% / 90.2%                    | 11.0 / 11.3                                             | 1246 / 1090                 |
| `code_search` | 1 pair  | 91.3% / 93.3%                    | 8 / 10                                                  | 2223 / 1680                 |

Across both models, two conclusions emerge:

1. **Iteration Induces Code Bloat and Doubles Cost**: For the exact same final specification, iterative development writes 15%–30% more code (+414 lines on GLM, p = 0.03) while taking 2× the time and token budget.
2. **Global Foresight Changes Where Complexity Lives**: While the total number of complex functions (CC ≥ 10) is similar, in 2 out of 3 iterative `forge` runs on Opus 5.5, the single most complex function in the entire codebase was `main()`. In One-Shot mode, `main()` was consistently tiny, with complexity properly distributed into subcommand handlers.

## 4. Step 3: Counterfactual Checkpoint Splicing — Proving Path Dependence

To test whether late-stage complexity on `forge` is driven by harder late-stage requirements or by early structural technical debt, we ran a Counterfactual Splicing Experiment on Opus 5.5:

- **Group A (Self-Generated Start)**: Standard iterative run from Checkpoint 1 to 8.
- **Group B (Spliced Reference Start)**: At the end of Checkpoint 3, we replaced the agent's workspace with the clean, modular human reference solution (canary strings stripped, 101/101 tests passing) and resumed Checkpoints 4–8 using the exact same `just-solve` prompt. Because each checkpoint starts a fresh session, the agent cannot tell whether it wrote the Checkpoint 3 code itself.

| Checkpoint 8 Final Metrics (Mean)       | Group A: Agent's Own C3 Start | Group B: Spliced Reference C3 Start | Human Reference (C8) |
| --------------------------------------- | ----------------------------- | ----------------------------------- | -------------------- |
| Peak Function Complexity (Max CC)       | 41.0 (35, 39, 49)             | 25.7 (25, 26, 26)                   | 26                   |
| Large Functions Count (Complexity ≥ 20) | 4.3                           | 1.3                                 | 3                    |
| `main()` Function Complexity            | 34.0                          | 19.0                                | —                    |
| C3 → C8 Peak Complexity Growth          | +11.3                         | +5.7                                | —                    |
| Final Test Pass Rate                    | 91.1%                         | 98.2%                               | 100%                 |

The causal effect is unmistakable: given a clean modular foundation at Checkpoint 3, Opus 5.5 cut its subsequent complexity growth in half (+5.7 vs. +11.3) and finished Checkpoint 8 with a Peak Function Complexity of 25.7—matching the human reference solution (26)!

Coding agents exhibit a powerful Broken Windows Effect (Context-Following Bias): hand them a modular architecture, and they extend it modularly; hand them a monolithic `main()`, and they keep stuffing `elif` branches into it.

(Caveat: The reference Checkpoint 3 snapshot has both better structure and fewer bugs [101/101 vs. 92%–94%]; these two factors are not separated in this experiment.)

## 5. Step 4: Why Don't Agents Refactor? Capability Deficit (Can't) vs. Incentive Deficit (Won't)

If a clean foundation makes such a dramatic difference, why doesn't the agent refactor its own messy code during iterative transitions?

### 1. Zero Spontaneous Refactoring Under Default Prompting

We scanned the AST evolution across all checkpoint transitions in our iterative runs to count how often functions were deleted, split, or substantially reduced in complexity:

| Experimental Group                 | Checkpoint Transitions | Refactoring Events |
| ---------------------------------- | ---------------------: | -----------------: |
| Opus 5.5 `forge` (Own Start)       |                     21 |                  0 |
| Opus 5.5 `code_search`             |                      4 |                  0 |
| Opus 5.5 `forge` (Reference Start) |                     15 |                  2 |
| GLM-5.3-flash (All Iterative Runs) |                     54 |                 10 |

Inspecting the few minor extraction events revealed that every single one was triggered by immediate code reuse for a new feature (e.g., "I'm sharing the unit list's filter parsing and matching with the new commands rather than duplicating it"). **Across 94 transitions, the agent never once refactored proactively to reduce complexity.**

### 2. Isolated refactor_only Sessions: 6/6 Perfect, Zero-Regression Refactorings

Is the model simply bad at refactoring? We took the Checkpoint 4 snapshots of `forge` and `circuit_eval` and ran a standalone session using a custom `refactor_only.txt` prompt—no new features, just instructions to decompose complex functions while preserving behavior:

| Problem        | Runs | Tests Passed (Before → After)          | Peak Function Complexity (Before → After, 3 Runs) |
| -------------- | ---: | -------------------------------------- | ------------------------------------------------- |
| `forge`        |    3 | Unchanged (136/142, 132/142, 136/142)  | 32 → 8, 29 → 11, 28 → 8                           |
| `circuit_eval` |    3 | Unchanged (430/430 → 430/430 in all 3) | 29 → 9, 34 → 13, 24 → 9                           |

All 6 refactoring sessions succeeded on the first try with zero test regressions, slashing Peak Function Complexity from 24–34 down to a clean 8–13.

This cleanly separates Capability from Behavior: **degradation occurs because the model does not spontaneously refactor, not because it cannot refactor.**

Consider the agent's incentives inside SlopCodeBench: each checkpoint drops a fresh, amnesiac agent instance into an unfamiliar repository without access to the prior regression test suite. When you cannot see the historical unit tests, restructuring core modules carries a massive risk of silent regression breakage. Appending minimally invasive branches to existing entrypoints is the rational risk-minimizing strategy.

## 6. Step 5: Finding the Cure — Why Endogenous Discipline Beats Exogenous Surgery

Since the model can refactor when asked, what is the best engineering intervention? Should we let it code fast-and-loose and run dedicated refactoring passes later (Exogenous Surgery), or enforce strict architectural constraints from Checkpoint 1 (Endogenous Discipline)?

We compared four regimes on Opus 5.5 across `forge` and `circuit_eval`:

1. **Group A (`just-solve`)**: Default prompt across all 8 checkpoints.
2. **Group D (Refactor Once)**: Run `refactor_only` after Checkpoint 4, then resume `just-solve` for Checkpoints 5–8.
3. **Group P (Periodic Refactor)**: Run `refactor_only` after Checkpoints 2, 4, and 6.
4. **Group C (Continuous `anti_slop`)**: Use the paper's `anti_slop` prompt ("No god functions", modular file separation) across all 8 checkpoints.

### Finding 1: Mid-Course Refactoring Decays on Hard Tasks, and Periodic Refactoring Breaks Correctness

First, does a single refactoring pass after Checkpoint 4 (Group D) hold up through Checkpoint 8?

| Problem        | Group                            | C4 Peak Complexity | C8 Peak Complexity | C4 → C8 Growth | C8 Large Functions (CC ≥ 20) |
| -------------- | -------------------------------- | -----------------: | -----------------: | -------------: | ---------------------------: |
| `forge`        | Group A: No Refactor             |               29.7 |               41.0 |          +11.3 |                          4.3 |
| `forge`        | Group D: Refactor Once (Post-C4) |                9.0 |               14.3 |           +5.3 |                          0.0 |
| `circuit_eval` | Group A: No Refactor             |               29.0 |               61.3 |          +32.3 |                          8.0 |
| `circuit_eval` | Group D: Refactor Once (Post-C4) |               10.3 |               34.3 |          +24.0 |                          5.0 |

On `forge`, a single refactoring held up well (final Peak Function Complexity 14.3, zero functions ≥ 20). On the much harder `circuit_eval`, where post-C4 refactoring only split functions within a single file, complexity rapidly re-accumulated to 34.3 by Checkpoint 8.

What if we refactor every two checkpoints (**Group P: Periodic Refactor after C2, C4, C6** on `circuit_eval`)?

| `circuit_eval` Periodic Refactor  |  C1 | C2 (Refactored) |  C3 | C4 (Refactored) |  C5 | C6 (Refactored) |  C7 | C8 (Final) |
| --------------------------------- | --: | --------------: | --: | --------------: | --: | --------------: | --: | ---------: |
| Peak Function Complexity (Max CC) |  29 |              9* |  14 |             11* |  11 |             11* |  12 |         42 |

Periodic exogenous refactoring backfired in three ways:

1. **Final-Checkpoint Rebound**: Without a post-C8 refactoring pass, Peak Function Complexity exploded from 12 to 42 in a single step.
2. **Doubled Cost**: Total cost hit $43.58—more than 2× the baseline ($21.40).
3. **Cross-Checkpoint Regression Breakage (Pass Rate Dropped from 99.8% to 90.5%)**: Final test score fell to 512/566. Crucially, none of the three refactoring sessions broke any tests. Instead, after the post-C2 refactoring split the codebase into multiple files, the fresh `just-solve` agent in Checkpoint 3 misunderstood the unfamiliar multi-file structure and broke Checkpoint 2's logic while implementing Checkpoint 3! Alternating between exogenous structural surgery and short-sighted feature patching creates a fatal architectural handoff gap.

### Finding 2: Continuous anti_slop Flattens the Degradation Slope — Directly Contradicting the Paper's Conclusion

The breakthrough came in Group C (Continuous `anti_slop`). Look at the checkpoint-by-checkpoint Peak Function Complexity trajectory on `circuit_eval`:

| Run                  |  C1 |  C2 |  C3 |  C4 |  C5 |  C6 |  C7 | C8 (Final) | C1 → C8 Growth |
| -------------------- | --: | --: | --: | --: | --: | --: | --: | ---------: | -------------: |
| `just-solve` (Run 1) |  16 |  25 |  27 |  29 |  33 |  42 |  53 |         62 |            +46 |
| `just-solve` (Run 2) |  21 |  28 |  30 |  34 |  41 |  51 |  72 |         75 |            +54 |
| `just-solve` (Run 3) |  10 |  18 |  20 |  24 |  30 |  50 |  40 |         47 |            +37 |
| `anti_slop` (Run 1)  |   6 |   9 |  11 |  11 |  11 |  11 |  11 |         12 |             +6 |
| `anti_slop` (Run 2)  |  10 |  10 |  10 |  10 |  10 |  10 |  10 |         10 |              0 |
| `anti_slop` (Run 3)  |  10 |  10 |  10 |  10 |  10 |  10 |  10 |         11 |             +1 |

Across all 12 runs on `forge` and `circuit_eval` (3 pairs each), the two distributions do not overlap at all:

| Problem        | Mode         | Runs | Final Peak Complexity (3 Runs) | 8-Checkpoint Complexity Growth | Final Large Functions (CC ≥ 20) | Pass Rate | Mean Cost |
| -------------- | ------------ | ---: | ------------------------------ | ------------------------------ | ------------------------------: | --------: | --------: |
| `forge`        | `just-solve` |    3 | 35, 39, 49                     | +14 to +28                     |                             4.3 |     91.1% |     $1.80 |
| `forge`        | `anti_slop`  |    3 | 9, 10, 11                      | 0 to +4                        |                             0.0 |     92.1% |     $4.14 |
| `circuit_eval` | `just-solve` |    3 | 47, 62, 75                     | +37 to +54                     |                             8.0 |     99.8% |    $21.40 |
| `circuit_eval` | `anti_slop`  |    3 | 10, 11, 12                     | 0 to +6                        |                             0.0 |     99.6% |    $13.12 |

Even using the paper's own `erosion` and `verbosity` metrics and comparing against Table 3 of the original paper (GPT 5.3–5.5), the reduction on Opus 5.5 is an order of magnitude stronger:

| Model & Scope                        | `just-solve` Erosion | `anti_slop` Erosion | Relative Reduction | Verbosity Change C1 → C8 (`just-solve` vs. `anti_slop`) |
| ------------------------------------ | -------------------- | ------------------- | -----------------: | ------------------------------------------------------- |
| GPT 5.3 Codex (Paper, 36-prob mean)  | 0.64                 | 0.42                |               −34% | —                                                       |
| GPT 5.4 (Paper, 36-prob mean)        | 0.51                 | 0.28                |               −45% | —                                                       |
| GPT 5.5 (Paper, 36-prob mean)        | 0.49                 | 0.21                |               −57% | —                                                       |
| Opus 5.5 `forge` Final (Ours)        | 0.69 (C1: 0.78)      | 0.02 (C1: 0.00)     |               −97% | +0.10 vs. +0.03                                         |
| Opus 5.5 `circuit_eval` Final (Ours) | 0.74 (C1: 0.31)      | 0.07 (C1: 0.00)     |               −91% | +0.11 vs. +0.01                                         |

Why does our finding on Opus 5.5 diverge so sharply from the paper's claim that quality prompts do not affect degradation rates?

1. **Model Generation & Instruction Following**: The paper evaluated `anti_slop` exclusively on GPT 5.3–5.5, whereas Opus 5.5 demonstrates substantially stronger adherence to structural constraints across long horizons.
2. **Threshold & Aggregation Artifacts**: Because `anti_slop` explicitly instructs against god functions, Opus 5.5 keeps Peak Function Complexity around 10–12, holding both complexity growth (0 to +6) and `erosion` increment (+0.02 to +0.07) near zero.

## 7. The Cost Crossover: Why Writing Clean Code Saved 39% on Hard Tasks

The original paper coined a memorable aphorism: "Slop does not fail your tests. It bills you," while simultaneously reporting that `anti_slop` increases per-checkpoint cost by 12.1%.

Comparing all four strategies across the full 8 checkpoints of `circuit_eval` reveals a striking **Cost Crossover**:

| Strategy on `circuit_eval` (8 Checkpoints) | Runs | Final Peak Function Complexity (C8) | Pass Rate | Mean Total Cost (USD) |
| ------------------------------------------ | ---: | ----------------------------------- | --------: | --------------------- |
| 1. Default (`just-solve`)                  |    3 | 61.3 (47–75)                        |     99.8% | $21.40                |
| 2. Refactor Once (Post-C4)                 |    3 | 34.3 (25–43)                        |     99.8% | $16.35                |
| 3. Periodic Refactor (Post-C2/C4/C6)       |    1 | 42.0                                |     90.5% | $43.58                |
| 4. Continuous `anti_slop`                  |    3 | 11.0 (10–12)                        |     99.6% | **$13.12 (−39%)**     |

Why did `anti_slop` cost more on the simpler `forge` task ($4.14 vs. $1.80) but save 39% on the complex `circuit_eval` task ($13.12 vs. $21.40)?

- **Upfront Modularization Overhead**: On simple problems or early checkpoints, splitting code across clean files and interfaces incurs a modest token overhead.
- **Compounding Technical Debt Interest**: On complex long-horizon tasks like `circuit_eval`, the abstraction effort saved by `just-solve` in Checkpoints 1–4 turns into crippling cognitive debt in Checkpoints 6–8. Navigating and debugging a 75-complexity monolithic function forces the agent into long loops of reading context, misplacing edits, failing tests, and retrying.

Clean architecture isn't just for human maintainers—it directly reduces the agent's own late-stage reasoning and debugging token burn.

## 8. Bonus: Three Upstream Harness Bugs Uncovered

While auditing over 150 checkpoint trajectories, we identified three bugs in the slop-code-bench evaluation harness (upstream issues drafted):

1. **`pkill -f` Self-Termination**: The harness passes the full prompt via command-line arguments to `claude`. When an agent runs `pkill -f <script_name>` to clean up background processes, it matches the script name inside its own CLI prompt string and kills the agent process itself—recording 0 tokens and `had_error=False` (observed in 7 of 159 checkpoints; fixed in our scripts by passing prompts via stdin).
2. **Under-Reported Token Usage on Retries**: When a checkpoint retries internally, the harness only logs token usage from the final segment, under-counting up to 250K output tokens in a single checkpoint (corrected in our analysis scripts by summing all `result` events).
3. **Retry Trajectory Overwrites**: Retries overwrite the original trajectory file, permanently erasing cost and trace data from failed attempts (e.g., losing a $2.05 run on `code_search` C3).

## 9. Conclusion & Takeaways for Practitioners

1. **Beware Proportional Metrics**: Never rely solely on ratio metrics like `erosion` (which can be diluted by trivial helper functions); always track absolute complexity indicators like Peak Function Complexity and counts of bloated functions (CC ≥ 20).
2. **Don't Expect Spontaneous Refactoring During Feature Work**: Under default goal-directed prompting without full regression visibility, minimal-invasive patching is the agent's path of least resistance (0/25 spontaneous refactorings), producing 20%–30% code bloat concentrated in `main()`.
3. **Avoid Alternating "Sloppy Feature Sprints" with "Periodic Refactoring Passes"**: Exogenous refactoring sessions create unfamiliar multi-file abstractions that subsequent feature-focused sessions frequently break (dropping pass rates from 99.8% to 90.5% while doubling cost).
4. **Bake Architectural Discipline into Day-0 Prompts (CLAUDE.md)**: On frontier models like Claude Opus 5.5, enforcing modularity and complexity caps from Checkpoint 1 turns path dependence into an asset—flattening complexity growth across 8 iterations to single digits while cutting total token costs on complex tasks by nearly 40%.

**Limitations**: Our core findings on refactoring and `anti_slop` are based on Claude Opus 5.5 across `forge` and `circuit_eval` (typically 3 runs per condition, 1 run for periodic refactoring). Differences from the original paper's GPT 5.3–5.5 results may reflect model-generation capabilities. Future work will expand `anti_slop` evaluations across GPT-5.x and additional problems, and isolate structural modularity from initial bug-free status via self-repaired baselines.

Sources: [SlopCodeBench paper (arXiv:2603.24755)](https://arxiv.org/abs/2603.24755) · [HTML version](https://arxiv.org/html/2603.24755v2) · [Author's blog post](https://gabeorlanski.github.io/posts/slop-code-bench/) · [Project site](https://www.scbench.ai/) · [NeurIPS 2026](https://neurips.cc/virtual/2026/poster/138903) · [Hugging Face](https://huggingface.co/papers/2603.24755) · [Discussion on Medium](https://medium.com/@jacksonfdam/your-agents-code-rots-the-discourse-about-it-rots-faster-8b09adff4b79)
{: .ar-fine}
