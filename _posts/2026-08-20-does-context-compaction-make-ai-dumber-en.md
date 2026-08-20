---
layout: post
title: Does Context Compaction Make AI Coding Assistants Dumber?
date: 2026-08-20 12:00:00 +0800
description: An empirical analysis of ~400K real coding-agent turns (TraceLab + the author's own Codex / Claude Code logs). After compaction, correctness barely degrades — but the model pays an "efficiency tax," re-reading and re-editing to recover lost details.
tags: [llm, coding-agent, context-compaction, evaluation, methodology]
---

<div style="font-family:Georgia,'Noto Serif',serif;max-width:760px;margin:0 auto;color:#222;line-height:1.9;">
  <p style="font-size:1.05em;color:#666;margin:0 0 28px;">— An empirical analysis of ~400,000 real coding-agent turns</p>

  <p>Long-session AI coding assistants inevitably hit a wall: the context window. As a conversation grows, the system "compacts" the history into a summary to free up space. This raises a natural question: <strong>after compaction, does the model still remember what it was doing? Does it get dumber?</strong></p>
  <p>We analyzed three real datasets — an aggregated trace set from <a href="https://github.com/uw-syfi/TraceLab">TraceLab</a> (UW SYFI; ~357K turns, 4,265 sessions), plus the author's own Codex (495 sessions) and Claude Code (5,856 sessions) raw logs. Along the way we fell into two methodological traps and reached some counter-intuitive conclusions.</p>

  <h2 style="font-size:1.3em;border-bottom:2px solid #eee;padding-bottom:6px;margin-top:36px;">0. Data: three mutually corroborating traces</h2>
  <table style="width:100%;border-collapse:collapse;font-size:0.88em;font-family:-apple-system,sans-serif;margin:16px 0;">
    <tr style="background:#f5f5f2;"><th style="padding:8px;text-align:left;border-bottom:2px solid #ddd;">Source</th><th style="padding:8px;text-align:left;border-bottom:2px solid #ddd;">Scale</th><th style="padding:8px;text-align:left;border-bottom:2px solid #ddd;">Characteristics</th><th style="padding:8px;text-align:left;border-bottom:2px solid #ddd;">Compact detection</th></tr>
    <tr><td style="padding:8px;border-bottom:1px solid #eee;"><strong><a href="https://github.com/uw-syfi/TraceLab">TraceLab</a></strong> (UW SYFI aggregated traces)</td><td style="padding:8px;border-bottom:1px solid #eee;">357,161 turns / 4,265 sessions / 23 models</td><td style="padding:8px;border-bottom:1px solid #eee;">Claude &amp; GPT families; turn-level metadata, <strong>no tool content</strong></td><td style="padding:8px;border-bottom:1px solid #eee;">token drop</td></tr>
    <tr><td style="padding:8px;border-bottom:1px solid #eee;">Author's own <strong>Codex</strong> logs</td><td style="padding:8px;border-bottom:1px solid #eee;">495 sessions / 10,810 turns</td><td style="padding:8px;border-bottom:1px solid #eee;">native <code>compacted</code> events + full command content</td><td style="padding:8px;border-bottom:1px solid #eee;">native event</td></tr>
    <tr><td style="padding:8px;">Author's own <strong>Claude Code</strong> logs</td><td style="padding:8px;">5,856 sessions</td><td style="padding:8px;">full tool_use file paths + usage</td><td style="padding:8px;">token drop</td></tr>
  </table>
  <p>TraceLab provides <strong>cross-model breadth</strong> (23 models) but only metadata; the two self-collected logs provide <strong>content depth</strong> (commands, file paths), letting us directly observe "re-read to recover" behavior. The three corroborate each other — no single dataset's conclusion stands alone.</p>

  <h2 style="font-size:1.3em;border-bottom:2px solid #eee;padding-bottom:6px;margin-top:36px;">1. Defining "capability": output tokens are a trap</h2>
  <p>The intuitive approach is to compare model "output" before and after compaction. We did this at first: many models' output tokens dropped sharply post-compact (claude-opus-4-8 by 52%), nearly leading us to conclude "severe degradation." <strong>That was wrong.</strong></p>
  <p>Before compaction the context is near the window limit, inflating output; after compaction the freed context yields shorter — possibly more efficient — responses. Using output tokens as capability mistakes "context pressure" for "capability." We switched to metrics closer to capability, defining each explicitly:</p>
  <ul>
    <li><strong>Error rate</strong>: fraction of tool calls flagged as failed by the framework (e.g., non-zero Bash exit code). This is "tool execution failure," not "model answer wrong."</li>
    <li><strong>Recovery rate</strong>: fraction of error rounds with no further error within 3 rounds — self-correction ability.</li>
    <li><strong>Blind retry</strong>: retrying the same tool after an error while still erroring within 3 rounds — a failure loop; the strongest degradation signal.</li>
  </ul>

  <h2 style="font-size:1.3em;border-bottom:2px solid #eee;padding-bottom:6px;margin-top:36px;">2. The second trap: one bad session fabricated "severe degradation"</h2>
  <p>In TraceLab, claude-opus-4-8 looked terrible: post-compact error rate 8.8% → 21.6%, blind retry 14% → 40%. By any standard, "severe degradation." But we ran an <strong>outlier sensitivity check</strong> — removing the single session contributing the most errors and recomputing — and the conclusion flipped:</p>
  <table style="width:100%;border-collapse:collapse;font-size:0.9em;font-family:-apple-system,sans-serif;margin:16px 0;">
    <tr style="background:#f5f5f2;"><th style="padding:8px;text-align:left;border-bottom:2px solid #ddd;">Metric</th><th style="padding:8px;text-align:right;border-bottom:2px solid #ddd;">With outlier</th><th style="padding:8px;text-align:right;border-bottom:2px solid #ddd;">Removed</th></tr>
    <tr><td style="padding:8px;border-bottom:1px solid #eee;">post-compact error rate</td><td style="padding:8px;text-align:right;border-bottom:1px solid #eee;">21.6%</td><td style="padding:8px;text-align:right;border-bottom:1px solid #eee;">7.7%</td></tr>
    <tr><td style="padding:8px;border-bottom:1px solid #eee;">error-rate change</td><td style="padding:8px;text-align:right;border-bottom:1px solid #eee;">+12.9pp</td><td style="padding:8px;text-align:right;border-bottom:1px solid #eee;">+0.1pp</td></tr>
    <tr><td style="padding:8px;">blind retry</td><td style="padding:8px;text-align:right;">40%</td><td style="padding:8px;text-align:right;">0%</td></tr>
  </table>
  <p>That session contributed 26% of the model's errors, with up to 18/21 tool calls failing in one round, and errors bursting both before and after compact — a broken environment, unrelated to compaction. <strong>Lesson: for any small-sample conclusion, do a leave-one-out check first. A verdict that flips on one session is an artifact, not a finding.</strong></p>
  <p>After checking all models, only two show robust post-compact correctness degradation: claude-opus-4-7 and gpt-5.4. The largest-sample model, gpt-5.5, stays stable throughout.</p>

  <h2 style="font-size:1.3em;border-bottom:2px solid #eee;padding-bottom:6px;margin-top:36px;">3. Our own data: correctness holds, but the model works harder</h2>
  <p><strong>Finding 1: correctness barely degrades.</strong> Codex error/recovery/blind-retry are stable across compact; Claude's error rate even <strong>drops</strong> (haiku 13.5% → 1.3%) — degradation actually occurs <em>before</em> compact (the "pressure" state near the limit); compaction resets it. Compact is relief, not harm.</p>
  <p><strong>Finding 2: but the model is clearly more effortful.</strong> Post-compact effort rises across sources: Codex tools/round doubles from 9.3 to 17.3, almost entirely edits (apply_patch 1432 → 3021); Claude reads increase ~45%.</p>

  <h2 style="font-size:1.3em;border-bottom:2px solid #eee;padding-bottom:6px;margin-top:36px;">4. Is it "recalling"? No — re-doing and compensating</h2>
  <p>Does the doubled tool use reflect active "recall," or just ordinary extra work? The content-rich self data lets us tell.</p>
  <ul>
    <li>Reads are a tiny share (&lt;3%), but their <strong>nature changes</strong>: ~48.5% of post-compact reads re-access files already seen before compact (vs 7.7% pre) — a genuine "lost detail → re-read to recover" signal.</li>
    <li>We caught it in the act: post-compact the model re-runs <code>sed -n</code> on an already-read <code>core.py</code>, and re-runs <code>rg "def generate_until"</code> to relocate a function it forgot.</li>
    <li>Edits: the re-edit rate of old files rises only slightly (59.8% → 63.5%), so the doubling is not mass "re-doing lost work" but more iterative convergence on the same hot files.</li>
  </ul>
  <pre style="background:#f5f5f2;border-left:3px solid #ccc;padding:14px;font-size:0.85em;overflow-x:auto;font-family:'SF Mono',Menlo,monospace;">compact loses some details
   → model notices; re-reads old files / relocates functions (compensate)
   → more edit iterations under incomplete info
   → final result still correct (correctness holds)
   → but ~2× the steps (the efficiency tax)</pre>
  <p><strong>Correctness holds precisely because the model compensates for lost details with extra effort.</strong> Output quality didn't degrade; time cost did — like someone whose notes were compressed, re-checking the source and redrafting to keep quality, at the cost of time.</p>

  <h2 style="font-size:1.3em;border-bottom:2px solid #eee;padding-bottom:6px;margin-top:36px;">5. Limitations: the invisible is the dangerous part</h2>
  <ul>
    <li><strong>Re-reads are only the "successfully compensated" part.</strong> If the model loses a detail without noticing and proceeds on the summary (silent loss), telemetry can't catch it, yet it may cause subtle errors. "Correctness holds" is an observation, not zero risk.</li>
    <li><strong>TraceLab has no content</strong>, so detail loss is unobservable there; only the self data can confirm it directly.</li>
    <li><strong>Causality isn't airtight.</strong> Compact coincides with intensive editing phases; part of the effort rise is task rhythm.</li>
    <li>Results don't generalize to all models: in TraceLab, opus-4-7 and gpt-5.4 genuinely degrade.</li>
  </ul>

  <h2 style="font-size:1.3em;border-bottom:2px solid #eee;padding-bottom:6px;margin-top:36px;">6. Takeaways for practitioners</h2>
  <ol>
    <li><strong>Don't measure capability by output tokens</strong>; use error/recovery metrics and define each explicitly.</li>
    <li><strong>Run outlier checks on small samples</strong>; a verdict that flips on one session is untrustworthy.</li>
    <li><strong>Compact's real cost is efficiency, not correctness</strong> — the model buys the result with more steps. Optimize summaries to retain "hot" information (frequently re-read files, key decisions) to cut the compensation cost.</li>
    <li><strong>Beware silent loss</strong>: visible re-reads are the tip of the iceberg; summary quality determines the invisible risk.</li>
  </ol>

  <p style="margin:44px 0 0;padding:22px 8px;border-top:1px solid #ddd;border-bottom:1px solid #ddd;text-align:center;font-size:1.12em;line-height:1.8;color:#111;">Compaction doesn't make models dumber — it makes them <strong>work harder to stay smart</strong>.<br>And the real danger was never the errors you can see, but the <strong>details you lose without noticing</strong>.</p>

  <p style="margin-top:40px;padding-top:16px;border-top:1px solid #eee;font-size:0.8em;color:#999;">Data &amp; methods in §0: <a href="https://github.com/uw-syfi/TraceLab">TraceLab</a> aggregated traces (UW SYFI, 357,161 turns); the author's own Codex (495 sessions, native compacted events) and Claude Code (5,856 sessions, token-drop detection) logs.</p>
</div>
