---
layout: post
title: 'Why Even Frontier Coding Agents Write "Slop": Root Causes and How to Fix It'
date: 2026-11-15 14:00:00 +0800
description: Counterfactual snapshot splicing, public multi-language coding trajectories, and live evaluations of AST gates and persistent workspace contracts.
tags: [llm, coding-agent, code-quality, benchmark, evaluation, refactoring]
lang: en
translation_key: coding-agent-code-erosion-governance
cite_key: qin2026codeerosion
dollar_math: false
toc_labels:
  "Core Prompts Used in the Experiments (Distilled)": "Core experimental prompts"
  "1. Starting-Point Experiment: Is Later Degradation Driven by Bad Early Structure or Early Bugs?": "Starting-point experiment"
  "2. Offline Empirical Analysis of Public Trajectories and 6,028 Multi-Language Commits": "Public trajectories and commits"
  "3. Why Models Default to Not Refactoring & Two Practical Fixes (Group G & Group D+)": "Practical governance fixes"
  "4. Practical Takeaways": "Practical takeaways"
---

**Summary**

On **SlopCodeBench**—a benchmark where each task unfolds across 8 sequential feature checkpoints, and each checkpoint starts a fresh container and session with only workspace files carried over—we previously observed a clear contrast: under the default `just-solve` prompt, **Claude Opus 5.5** never refactored spontaneously across 25 checkpoint transitions, letting entry-point functions grow larger and larger. Yet when asked in a separate session to _only_ refactor, **all 6 attempts succeeded with zero test breakage**, dropping peak function complexity (throughout this post, "complexity" refers to single-function cyclomatic complexity—the number of `if/for/while` branching paths inside a function) from `24–34` down to `8–13`. Even more tellingly, adding the modular `anti_slop` prompt from Checkpoint 1 kept 8-checkpoint complexity growth to `0 ~ +6` (vs. `+14 ~ +54` under default) while **reducing total cost by 39% ($13.12 vs. $21.40)** on the complex `circuit_eval` task.

To see whether this was just a fluke on a couple of tasks or a general pattern across coding agents, we conducted three follow-up studies:

1. **Separating "Bad Early Structure" from "Early Bugs" (Section 1)**: At Checkpoint 3 of `forge`, we built **Group B'** by patching all failing tests in place inside Group A's single-file code (reaching `101/101` passing tests while keeping peak complexity at `29.7`). Fixing early bugs on a messy structure did **nothing** to reduce new failures in Checkpoints 5–8 (Group B' failed the exact same `19.0` new tests as Group A and ended up with `5.0` functions at complexity <span class="mathjax_process">$\ge 20$</span>, vs. `5.3` failed tests and `1.3` large functions when starting from the modular reference solution in Group B).

2. **Auditing 16,000+ Public Sessions and 6,028 Multi-Language Commits (Section 2)**: Offline static analysis across **CodeMem**, **Thoughtworks / RouterBench / Finding-the-Right-Fit**, and **ProgramBench** showed that adding cross-checkpoint memory (`ProjectMem`) or retaining full history (`full_trajectory`) does not stop complexity growth; on single-turn SWE-bench bug fixes, even human developers have a `0/23 (0%)` refactoring rate on high-complexity files; and across 591 from-scratch ProgramBench projects in Rust, Go, C, C++, and Python, models extracted helpers on high-complexity files only **~0.3%** of the time (all mixed with feature edits; zero pure refactorings), while adding more branches to existing large functions ~50% of the time.

3. **Testing Two Lightweight Fixes (Section 3)**: On `forge`, running a pre-exit AST check via Claude Code's `Stop` hook (**Group G**) intercepted bloated functions 13 times across 24 checkpoints—each resolved on the first try—cutting Checkpoint 8 peak complexity from `41.0` to **`13.7`** at just **+19% cost ($2.14 vs. $1.80)**, half the cost of full `anti_slop` ($4.14). On `circuit_eval`, placing a `CLAUDE.md` file (documenting module roles and a complexity <span class="mathjax_process">$\le 12$</span> limit) in the workspace after a Checkpoint 4 refactor (**Group D+**) kept peak complexity <span class="mathjax_process">$\le 13$</span> across all 12 continuation checkpoints, finishing at **`10.3`** and eliminating the rebound to `34.3` seen without `CLAUDE.md`.

---

### Core Prompts Used in the Experiments (Distilled)

Omitting standard boilerplate regarding virtual environments and `requirements.txt`, here are the core instructions of the three prompts compared across our experiments:

- **1. `just-solve` (Default Prompt — Used in Group A, continuations of B / B' / D / D+, and Group G)**

  > _"Implement a program that 100% solves the specification. That is all you need to do. Your task is: `{% raw %}{{ spec }}{% endraw %}`"_

- **2. `anti_slop` (Quality-Guided Prompt — Used across all 8 checkpoints in Group C)**

  > _"You are an exceptional Python software engineer... Focus only on adding in the new features/changes below. Follow best coding practices: **Group functions into files based on related functionality; Keep your code clean; No god functions/classes**; Make sure the code is documented appropriately so that it is easy to pick up. Minimize the following gotchas: extra defensive checks, heavy nesting, if/else ladders, trivial wrappers, or a ton of helper methods. Your task is: `{% raw %}{{ spec }}{% endraw %}`"_

- **3. `refactor_only` (Standalone Refactoring Prompt — Used for the post-C4 refactor in Group D and periodic refactoring runs; contains no task specification)**
  > _"The requirements for this program have not changed. **Do not add any new features.** Your task is to refactor the existing code in this directory to improve its structure: **Break up large or deeply nested functions into smaller, focused ones; Remove duplicated logic; Organize the code so that it is easy to extend with new commands and features later.** The program's observable behavior (CLI, outputs, error messages and exit codes) must stay exactly the same. Before you finish, run the program on a range of inputs to verify that its behavior is unchanged."_

---

## 1. Starting-Point Experiment: Is Later Degradation Driven by Bad Early Structure or Early Bugs?

### 1.1 Background: Group A and Group B

In SlopCodeBench, each problem spans 8 sequential checkpoints (<span class="mathjax_process">$\text{C1} \to \text{C8}$</span>). **Each checkpoint runs in a fresh Docker container and a brand-new session—conversation history is wiped, and only the workspace files carry over.**

On the 8-checkpoint `forge` task, we ran **Claude Opus 5.5** (Claude Code 2.1.44, default `just-solve` prompt) under two baseline conditions (3 runs each):

- **Group A (Model's Own Start: Single-File High Complexity + Minor Bugs)**
  - **Setup**: The model runs naturally from Checkpoint 1 to 8 without intervention.
  - **At Checkpoint 3**: All code lives in **1 single file** (`18 / 26 / 21` functions), peak function complexity reaches **`32 / 29 / 28` (mean `29.7`)**, and **`95 / 93 / 95` out of 101 tests pass (mean `94.3/101`)**.
  - **At Checkpoint 8**: Peak function complexity climbs to **`41.0` (35, 39, 49)**, `main()` complexity hits **`34.0`**, and full test pass rate is **`91.1%`**.

- **Group B (Reference Start: Modular + 100% Passing)**
  - **Setup**: At the end of Checkpoint 3, we replace the workspace with the official Checkpoint 3 reference solution (canary removed) and resume Checkpoints 4–8 under the same `just-solve` prompt. Because each checkpoint is a fresh session, the model cannot tell whether the code was written by itself.
  - **At Checkpoint 3**: Peak function complexity is **`20.0`** (`9.7` lower than Group A), and **`101 / 101` tests pass**.
  - **At Checkpoint 8**: Peak function complexity stays down at **`25.7` (25, 26, 26)** (matching the official Checkpoint 8 reference solution's `26`), functions with complexity <span class="mathjax_process">$\ge 20$</span> drop from `4.3` to **`1.3`**, and pass rate rises to **`98.2%` (+7.1pp over Group A)**.

---

### 1.2 Constructing Group B' (Messy Structure + 101/101 Passing): Separating Structure from Bugs

Group B's reference start has two advantages at Checkpoint 3: **better structure (peak complexity `20.0` vs. `29.7`)** and **fewer bugs (`101/101` vs. `94.3/101`)**. To separate them, we inspected the 6–8 failing Checkpoint 3 tests in Group A:

- Most were not logic bugs, but error-message formatting issues: `name: must be...` had an extra colon; `invalid_operation` printed the `allocation id` instead of the offending operation value.

- Only `run2` had a real bug: `blueprints.json` was stored as a `dict` when tests expected a `list`.

We wrote all patches directly inside Group A's existing functions to create **Group B' (Messy Structure + 101/101 Passing)**, satisfying four checks:

1. **Checkpoint 3 tests**: Raised from `95 / 93 / 95` to **`101 / 101`**;

2. **Checkpoint 3 peak complexity**: Kept unchanged at **`32 / 29 / 28` (mean `29.7`)**;

3. **Function count**: Kept unchanged at **`18 / 26 / 21`**;

4. **File count**: Kept at **1 single file**.

{% include code-erosion-splice-design-en.svg %}

Resuming Checkpoints 4–8 from Group B' yielded:

| Metric (Mean of 3 Runs)                                                               | Group A: Messy + Bugs<br>_(C3: 94.3/101)_ | **Group B': Messy + 101/101**<br>_(In-Place Patched C3)_ | Group B: Clean + 101/101<br>_(Reference C3)_ |
| :------------------------------------------------------------------------------------ | :---------------------------------------: | :------------------------------------------------------: | :------------------------------------------: |
| **C3 Start: Peak Function Complexity**                                                |             29.7 (32, 29, 28)             |                  **29.7 (32, 29, 28)**                   |                   **20.0**                   |
| **C8 Final: Peak Function Complexity**                                                |             41.0 (35, 39, 49)             |                  **34.3 (37, 34, 32)**                   |            **25.7 (25, 26, 26)**             |
| **C3 <span class="mathjax_process">$\to$</span> C8: Peak Complexity Delta**           |                   +11.3                   |                         **+4.7**                         |                   **+5.7**                   |
| **C8 Final: Functions with Complexity <span class="mathjax_process">$\ge 20$</span>** |                    4.3                    |                         **5.0**                          |                   **1.3**                    |
| **C8 Final: `main()` Complexity**                                                     |                   34.0                    |                         **24.3**                         |                   **19.0**                   |
| **C8 Final: Full Test Pass Rate**                                                     |                   91.1%                   |                        **93.6%**                         |                  **98.2%**                   |
| **C8 Final: Failed Tests from C1–C4**                                                 |                  **7.3**                  |                         **0.0**                          |                   **0.0**                    |
| **C8 Final: Failed Tests from C5–C8**                                                 |                 **19.0**                  |                         **19.0**                         |                   **5.3**                    |

{% include code-erosion-splice-en.svg %}

### 1.3 Conclusions and Limitations

1. **Clean split of test pass rates**: Group B' and Group A had the **exact same failures in Checkpoints 5–8 (`19.0` each, failing the exact same test cases)**. Thus, the `+7.1pp` gap between Group A and Group B splits into:
   - **~`+2.5pp` from early Checkpoint 1–3 bugs**: Later sessions never fixed them because prior regression tests were hidden, so they kept deducting points until the end;
   - **~`+4.6pp` from the reference start preventing new failures in Checkpoints 5–8 (`5.3` vs. `19.0`)**: Fixing early bugs on a messy structure did nothing to prevent later errors.

2. **Complexity follows the starting baseline**: Group B' finished `8.6` points higher in peak complexity than Group B (`34.3` vs. `25.7`, close to their `9.7` starting gap) and had **`5.0` functions at complexity <span class="mathjax_process">$\ge 20$</span>** (vs. `1.3` in Group B). However, Group B''s increment (`+4.7`) was close to Group B's (`+5.7`) and did not repeat Group A's extra `+11.3` jump (in 2 of 3 Group A runs, Checkpoint 8 kept piling branches into `main()`, whereas Group B' did not). Minor error-string fixes are unlikely to change how Checkpoint 8 is written, so this difference looks like <span class="mathjax_process">$n=3$</span> random variation rather than bug fixes suppressing bloat; the solid conclusion is that **final complexity is mainly determined by starting structure**.

3. **An unseparated confounder**: Group B's `+4.6pp` advantage over Group B' may not come purely from structure. The reference solution also encodes accurate interpretations of the specification—such as **error precedence** and **UUID validation conventions**—which may make Checkpoint 6 and 7 tests easier to pass.

4. **Corroboration from Anthropic's Fable 5.2 report**: In the **Claude Fable 5.2 Prompting Guide ("Say who owns the code")**, Anthropic noted that when codebase ownership is unstated, models act like guests—adding code onto existing structures (consolidating duplicate code **<span class="mathjax_process">$&lt;10\%$</span>** of the time) and only reporting nearby bugs. Explicitly telling the model _"This codebase is yours: what it's for and how it's built are your call, and you'll keep building on it"_ raises proactive cleanup and deduplication to **~50%**, while prompting it to fix adjacent issues.

---

## 2. Offline Empirical Analysis of Public Trajectories and 6,028 Multi-Language Commits

### 2.1 Does Cross-Checkpoint Memory (`ProjectMem`) or Full History Stop Degradation?

Recomputing AST complexity across all **36 Python tasks (784 snapshots)** in [zychen22/CodeMem-SCB-outputs](https://huggingface.co/datasets/zychen22/CodeMem-SCB-outputs/tree/f7cf9afb5e215c763742b011e1e6bec0babfad4f) (`glm-5.3-flash`, `mini_swe`, `just-solve`):

| Group                                | Tasks <span class="mathjax_process">$N$</span> | Initial Peak Complexity<br>_(Mean / Median)_ | Final Peak Complexity<br>_(Mean / Median)_ | Paired Delta<br>_(Mean / Median)_ | Tasks w/ Higher Final Complexity | High-Complexity (<span class="mathjax_process">$\ge 20$</span>)<br>Refactor Candidates |
| :----------------------------------- | :--------------------------------------------: | :------------------------------------------: | :----------------------------------------: | :-------------------------------: | :------------------------------: | :------------------------------------------------------------------------------------: |
| **`baseline` (No Memory)**           |                       36                       |                25.92 / 24.50                 |             **43.22 / 38.50**              |          +17.31 / +11.00          |          31/36 (86.11%)          |                                   6/133 (**4.51%**)                                    |
| **`ProjectMem` (Scoped Memory)**     |                       36                       |                25.94 / 21.50                 |             **49.81 / 39.50**              |          +23.86 / +12.50          |          29/36 (80.56%)          |                                   4/125 (**3.20%**)                                    |
| **`full_trajectory` (Full History)** |                       35                       |                25.91 / 24.00                 |             **52.09 / 49.00**              |        **+26.17 / +23.00**        |          34/35 (97.14%)          |                                   3/125 (**2.40%**)                                    |
| **`memory_without_scope`**           |                       36                       |                25.92 / 24.50                 |             **44.33 / 39.00**              |          +18.42 / +14.00          |          34/36 (94.44%)          |                                   4/132 (**3.03%**)                                    |

- **Cross-checkpoint memory did not eliminate degradation**: Under `ProjectMem` and `full_trajectory`, final peak complexity rose to `49.81` and `52.09` (e.g., `sheeteval.py::grade_sheet` grew across 7 checkpoints from complexity `20 → 79` [80 to 601 SLOC], and `mocked_http::build_behavior_from_item` grew from `89 → 206`).

- **Within single long sessions (Thoughtworks, 15,000 sessions)**: Across **500 strictly reconstructed sessions (<span class="mathjax_process">$\ge 30$</span> turns, 684 function sequences, 3,013 function edits across `swe-agent` and `openhands`)** in [thoughtworks/agentic-coding-trajectories](https://huggingface.co/datasets/thoughtworks/agentic-coding-trajectories/tree/cef72d1f4d0caabf85937adf8337a14b7522c782), **88.58% (2,669/3,013)** of edits did not reduce function complexity (55.23% unchanged, 33.36% increased, 11.42% decreased; e.g., `sunpy`'s `XRSTimeSeries.observatory` rose across 15 edits from complexity `8 → 53`). Across **592 edits to files with peak complexity <span class="mathjax_process">$\ge 20$</span>**, manual code review confirmed true helper extraction in only **3 / 592 (0.51%)** cases; when directly editing a function already at complexity <span class="mathjax_process">$\ge 20$</span> (<span class="mathjax_process">$N=380$</span>), agents **added more branches 43.16% (164/380)** of the time.

---

### 2.2 Frontier Models (Opus 5.5 / Fable 5.1 / GPT-6 Astra) and Paired Human Gold Patches

Across [RouterBench](https://huggingface.co/datasets/jerryyan/routerbench-trajectories), [Finding the Right Fit](https://huggingface.co/datasets/yixuanli97/finding-the-right-fit), and native Fable 5 Claude Code logs ([Log 1](https://huggingface.co/datasets/armand0e/claude-fable-5-claude-code), [Log 2](https://huggingface.co/datasets/AlinCiocan/fable-5-claude-code-traces)):

1. **GPT-6 Astra in long sessions**: Across **57 strict long sessions (101 function sequences, 457 edits)**, **92.12% (421/457)** of edits did not reduce complexity (e.g., `simglucose`'s `SubmissionController.act` dipped from `32 → 25` before climbing to **`59`** across 13 edits; `fin-saccr-rwa`'s `main()` stayed stagnant at complexity **`98`** across 7 edits). Across **447 non-test high-complexity (<span class="mathjax_process">$\ge 20$</span>) file edits**, only **1 (0.22%)** extracted a helper (`vllm` streaming parser complexity `41 → 12` alongside an algorithm rewrite), while direct edits to functions with complexity <span class="mathjax_process">$\ge 20$</span> (<span class="mathjax_process">$N=215$</span>) increased complexity **35.35% (76/215)** of the time.

2. **Paired SWE-bench Verified (45 identical tasks)**: Comparing Opus 5.5, Fable 5.1, and human Gold Patches over the union of modified non-test Python files:

| Participant (Same 45 SWE-bench Tasks) | Tasks <span class="mathjax_process">$N$</span> | Peak Complexity Delta (Mean / Median) | Tasks w/ Function Count Increase | Tasks w/ Peak Complexity Increase | High-Complexity (<span class="mathjax_process">$\ge 20$</span>)<br>`RefactorProxy` Rate |
| :------------------------------------ | :--------------------------------------------: | :-----------------------------------: | :------------------------------: | :-------------------------------: | :-------------------------------------------------------------------------------------: |
| **Claude Opus 5.5**                   |                       45                       |            +0.089 / 0.000             |          21/45 (46.67%)          |           4/45 (8.89%)            |                                   **0 / 23 (0.00%)**                                    |
| **Claude Fable 5.1**                  |                       45                       |            +0.089 / 0.000             |          21/45 (46.67%)          |           4/45 (8.89%)            |                                   **0 / 23 (0.00%)**                                    |
| **Human Developers (Gold Patch)**     |                       45                       |            +0.067 / 0.000             |          21/45 (46.67%)          |           3/45 (6.67%)            |                                   **0 / 23 (0.00%)**                                    |

- Both models matched the human Gold Patch's peak complexity delta on **44/45 (97.78%)** tasks, and **human Gold Patches also had a `0/23 (0%)` refactoring rate** on high-complexity files (e.g., on `django__django-15629`, the human author, Opus 5.5, and Fable 5.1 all added 2 branches to Django's complexity-`79` `_alter_field` function to make it `81`). Minimal-invasive patching is standard practice for one-off bug fixes, but causes bloat when carried into multi-turn development.

---

### 2.3 What If Models Build Their Own Project From Scratch (Rust / Go / C++)?

Seeing the SWE-bench results in Section 2.2 raises a natural question: _“On SWE-bench, models are patching someone else's legacy Python repo. What if a model builds its own project from an empty directory (100% code ownership) in systems languages like Rust, Go, or C++? Will it still keep piling branches into huge functions?”_

To test this, we used `lizard` [lizard documentation](https://github.com/terryyin/lizard) to scan all **591 from-scratch repositories and 6,028 first-parent Git commits** in **ProgramBench** ([Opus 5.5](https://huggingface.co/datasets/programbench/20261005_mini-v2.4.5_opus-5.5-xhigh): 195 tasks / 3,504 commits; [Fable 5.1](https://huggingface.co/datasets/programbench/20261007_mini-v2.4.5_fable-5.1-xhigh): 196 tasks / 2,119 commits; [GPT-6 Astra](https://huggingface.co/datasets/programbench/20261001_mini-v2.4.5_gpt-6-astra-max): 200 tasks / 405 commits, where Opus 5.5 and Fable 5.1 used Rust, Go, and C/C++ in over 90% of projects):

| Model (ProgramBench Commits)            | Paired Tasks <span class="mathjax_process">$N$</span> | First-to-Last Peak Complexity Delta<br>_(Mean / Median)_ | <span class="mathjax_process">$\ge 3$</span> Same-Func Edits<br>**Non-Decreasing Complexity Rate** | High-Complexity (<span class="mathjax_process">$\ge 20$</span>) File Edits | `RefactorProxy` Candidates | **Confirmed Helper Extractions**<br>_(All Mixed w/ Features; Pure=0)_ | Direct Edits to Complexity <span class="mathjax_process">$\ge 20$</span> Functions<br>**That Added Branches** |
| :-------------------------------------- | :---------------------------------------------------: | :------------------------------------------------------: | :------------------------------------------------------------------------------------------------: | :------------------------------------------------------------------------: | :------------------------: | :-------------------------------------------------------------------: | :-----------------------------------------------------------------------------------------------------------: |
| **Claude Opus 5.5**                     |                          185                          |                      +16.71 / +2.00                      |                                     2,148 / 2,382 (**90.18%**)                                     |                                 **3,852**                                  |         20 (0.52%)         |                        **12 / 3,852 (0.31%)**                         |                                          **1,342 / 2,490 (53.90%)**                                           |
| **Claude Fable 5.1**                    |                          167                          |                      +15.83 / 0.00                       |                                     1,093 / 1,242 (**88.00%**)                                     |                                 **2,662**                                  |         14 (0.53%)         |                         **8 / 2,662 (0.30%)**                         |                                           **916 / 1,892 (48.41%)**                                            |
| **GPT-6 Astra** _(few mid-run commits)_ |                           3                           |                       0.00 / 0.00                        |                                             0 / 0 (NA)                                             |                                   **4**                                    |         0 (0.00%)          |                           **0 / 4 (0.00%)**                           |                                                 0 / 3 (0.00%)                                                 |

The pattern is identical: **even when starting from an empty folder and writing their own Rust, Go, or C++ codebases from scratch, models still default to adding branches rather than splitting functions.** Whenever Opus 5.5 and Fable 5.1 modified a function they had written that was already at complexity <span class="mathjax_process">$\ge 20$</span>, they added more branches **53.90%** and **48.41%** of the time, while confirmed helper extractions across all 6,518 high-complexity file edits sat at just **0.31% and 0.30%** (all mixed with feature additions; zero pure refactorings). By the final commit, single-project peak function complexity averaged **`87.4–89.8`** across all three models (e.g., Opus 5.5 grew `calcurse`'s C `ui_main` monotonically across 11 commits from complexity `1` to `93`, and `nsh`'s Rust `run` from `2` to `101`; Fable 5.1 grew `broot`'s Rust `execute_internal` from `168` to `242`).

---

## 3. Why Models Default to Not Refactoring & Two Practical Fixes (Group G & Group D+)

### 3.1 Group G: In-Session AST Gatekeeper on `forge` (`just-solve` + `Stop` Hook)

We mounted `scripts/ast_stop_gatekeeper.py` (complexity threshold <span class="mathjax_process">$\le 15$</span>) in the harness's user-level `~/.claude/settings.json` (`claude_code-2.1.44-astgate`), keeping `.claude/` out of workspace snapshots and tracking retry counts per session ID so counts do not bleed across checkpoints:

| `forge` Checkpoint 8 (Mean of 3 Runs)                                       |                Group A: `just-solve`                 |          **Group G: `just-solve` + Gatekeeper**          |              Group C: Full `anti_slop`               |
| :-------------------------------------------------------------------------- | :--------------------------------------------------: | :------------------------------------------------------: | :--------------------------------------------------: |
| **Peak Function Complexity**                                                |                         41.0                         |                  **13.7 (13, 14, 14)**                   |                         10.0                         |
| **Functions with Complexity <span class="mathjax_process">$\ge 20$</span>** |                         4.3                          |                          **0**                           |                          0                           |
| **`erosion` (C1 <span class="mathjax_process">$\to$</span> C8)**            | 0.78 <span class="mathjax_process">$\to$</span> 0.69 | **0.12 <span class="mathjax_process">$\to$</span> 0.17** | 0.00 <span class="mathjax_process">$\to$</span> 0.02 |
| **Pass Rate**                                                               |                        91.1%                         |                        **91.5%**                         |                        92.1%                         |
| **Cost**                                                                    |                        $1.80                         |                     **$2.14 (+19%)**                     |                    $4.14 (+130%)                     |

{% include code-erosion-forge-en.svg %}

- **13 intercepts, each fixed in 1 try**: Across 24 checkpoints, the gatekeeper triggered 13 times—catching the exact functions that bloated in Section 1 (`alloc_bind` at complexity 25–28 and `main/run` at complexity 17–21). Every time, the current session split the function on the first retry, never hitting the 2-retry cap. It achieved near-`anti_slop` complexity at only **+19% cost ($2.14 vs. $1.80)** while remaining a single file without premature modularization. _(Note: Final complexity <span class="mathjax_process">$\le 15$</span> is partly a direct result of the gatekeeper's hard rule.)_

### 3.2 Group D+: Checkpoint 4 Refactor + `CLAUDE.md` on `circuit_eval`

| `circuit_eval` Checkpoint 8 (Mean of 3 Runs)                                |                 Group A: No Refactor                 |             Group D: Refactor Once (C4)              |           **Group D+: Refactor + `CLAUDE.md`**           |              Group C: Full `anti_slop`               |
| :-------------------------------------------------------------------------- | :--------------------------------------------------: | :--------------------------------------------------: | :------------------------------------------------------: | :--------------------------------------------------: |
| **Peak Function Complexity**                                                |                         61.3                         |                         34.3                         |                  **10.3 (11, 10, 10)**                   |                         11.0                         |
| **Functions with Complexity <span class="mathjax_process">$\ge 20$</span>** |                         8.0                          |                         5.0                          |                          **0**                           |                          0                           |
| **`erosion` (C1 <span class="mathjax_process">$\to$</span> C8)**            | 0.31 <span class="mathjax_process">$\to$</span> 0.74 | 0.31 <span class="mathjax_process">$\to$</span> 0.52 | **0.31 <span class="mathjax_process">$\to$</span> 0.01** | 0.00 <span class="mathjax_process">$\to$</span> 0.07 |
| **Pass Rate**                                                               |                        99.8%                         |                        99.8%                         |                        **99.8%**                         |                        99.6%                         |
| **Cost**                                                                    |                        $21.40                        |                        $16.35                        |            **~$16.40** _(incl. timeout est.)_            |                      **$13.12**                      |

{% include code-erosion-circuit-en.svg %}

- **Eliminated post-refactor rebound**: Group D began rebounding at Checkpoint 5 and reached `34.3` by Checkpoint 8; Group D+ kept peak complexity <span class="mathjax_process">$\le 13$</span> across all 12 continuation checkpoints, finishing at **`10.3`** (matching full `anti_slop`'s `11.0`), and `run3` even updated `CLAUDE.md`'s module map on its own at Checkpoint 8.

- **Cost & limitation**: `run2` timed out at 2.7 hours on Checkpoint 8 (after finishing all code with `566/566` passing tests and peak complexity `10`, so complexity and pass rate are valid, but trajectory cost was recorded as `$0`). Adding the estimated cost (`$11.99`) from `checkpoint_results.jsonl` puts Group D+ at **`~$16.40`**, matching Group D (`$16.35`) rather than beating full `anti_slop` (`$13.12`). Also, `CLAUDE.md` added both the module map and the explicit complexity <span class="mathjax_process">$\le 12$</span> limit, so this experiment cannot separate which of the two played the main role.

---

## 4. Practical Takeaways

- **Known complex, multi-turn projects (`circuit_eval`)**: Use `anti_slop` from Turn 1—it delivers the best structure and saves 39% in total cost.

- **Smaller tasks or uncertain complexity (`forge`)**: Use default prompting with a pre-exit `Stop` hook AST check (Group G) to split bloated functions on the spot for just +19% cost.

- **Mid-course refactoring or codebase handoffs (Group D+)**: Always pair refactoring with a workspace `CLAUDE.md` specifying module roles and complexity limits so future sessions don't undo the cleanup.
