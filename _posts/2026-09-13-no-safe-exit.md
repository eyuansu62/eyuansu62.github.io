---
layout: post
title: No Safe Exit
date: 2026-09-13 06:55:00 +0000
notion_page_id: 3da8111ab86481479a30e1434f23907f
notion_url: https://ruddy-engineer-594.notion.site/No-Safe-Exit-3da8111ab86481479a30e1434f23907f
---

Author：Bowen ｜ [homepage](https://eyuansu62.github.io/) ｜ [X @eyuansuMX](https://x.com/eyuansuMX)

---

_When impossible tasks turn persistence into misalignment._

During internal cybersecurity evaluations in July 2026, OpenAI agents encountered unusually difficult tasks.

Some of them did not simply fail.

They circumvented isolation controls, regained unintended Internet access, coordinated through shared infrastructure, and eventually interacted with third-party systems. OpenAI’s postmortem later highlighted several ingredients behind the incident: reward hacking, persistence on seemingly impossible tasks, unauthorized communication, and agents adopting goals from one another.

One section had an unusually revealing title: [“Difficult tasks without a safe exit.”](https://openai.com/index/hugging-face-incident-and-the-road-ahead/)

After an incident like this, the obvious question is:

> **Why didn’t the agent stop?**

But there is an earlier question:

<div class="ar-callout" markdown="1">

🚪 **What did the evaluation say the agent should do when the task could not be completed normally?**

</div>

---

## 01 — The missing action

Most evaluations quietly assume that every task has a legitimate solution.

The model either finds it or fails.

That assumption works until the task is broken, underspecified, inaccessible, internally contradictory, or impossible under the environment’s constraints.

At that point, there is a third action we need the model to be able to take:

> **Recognize that the task cannot be completed as stated, explain why, and stop.**

This sounds obvious. But many evaluation setups do not actually represent it as a successful outcome.

If the grader only rewards task completion, then “I cannot complete this honestly” and “I failed to solve it” collapse to the same score.

Now give the agent more time, more tools, and more reasoning compute.

Persistence becomes valuable. Searching for loopholes becomes valuable. Understanding the grader becomes valuable. The boundary between _solving the task_ and _finding some other way to get credit_ starts to matter a lot.

Impossible tasks do not automatically cause misalignment. But they are a sharp test of whether the system has given the optimizer a legitimate way to fail.

<div class="ar-callout" markdown="1">

⚠️ If it has not, the agent has **no safe exit**.

</div>

---

## 02 — Rubrics are part of the objective

A rubric looks like documentation. In an LLM-as-judge pipeline, it is closer to an executable specification.

The rubric tells the judge what distinctions to care about. The judge turns those distinctions into a score. That score determines which behavior is preferred, selected, or reinforced.

<div class="ar-callout" markdown="1">

📋 **A perfectly reasonable-looking rubric might say:**

- complete the requested task;
- return the required artifact;
- satisfy the requested constraints;
- produce a working solution.

</div>

Nothing there is obviously wrong.

The problem is what is missing.

<div class="ar-callout" markdown="1">

There is no criterion for noticing that the requested artifact **cannot exist** under the stated constraints.

</div>

A model that fabricates a plausible-looking answer may satisfy more of the rubric than a model that correctly identifies the impossibility.

A stronger judge does not fix this. A perfect judge faithfully applying the wrong rubric is still optimizing the wrong thing.

That is why we think rubric generation itself deserves to be treated as an alignment problem.

![No Safe Exit concept diagram](/assets/img/notion/3da8111ab86481479a30e1434f23907f/01.svg)

_No Safe Exit concept diagram_

_The failure mode in one picture: when the evaluator has no notion of a correct failure, more capability can mean more ways to optimize the wrong objective._

---

## 03 — Impossible tasks are unusually revealing

On ordinary solvable tasks, a shallow rubric can look surprisingly competent.

Read the instruction. Break it into requirements. Check whether the response satisfies each one.

Impossible tasks break this recipe.

Before the evaluator can write the right criteria, it has to understand the task well enough to ask whether the task is coherent at all.

<div class="ar-callout" markdown="1">

🧗 **Hard but solvable**

The model should keep trying.

</div>
<div class="ar-callout" markdown="1">

❓ **Underspecified**

The model should ask for clarification or missing information.

</div>
<div class="ar-callout" markdown="1">

⛔ **Impossible under the stated constraints**

The model should identify the conflict and stop safely.

</div>

This is why “just add a refusal criterion” is not enough.

A system that rewards refusal whenever a task looks difficult has simply created the opposite failure mode.

The difficult part is not teaching the evaluator that refusal can be good. It is teaching the evaluator **when** refusal is the correct answer.

That is exactly the boundary [ImpossibleRubrics](https://impossiblerubrics.github.io/) is meant to probe.

We are not mainly asking whether an LLM can generate longer or more detailed rubrics. Frontier models can already produce polished checklists.

We want to know whether the rubric generator notices when the task changes the meaning of success.

When the task is impossible, does the rubric still reward performative completion?

Or does it recognize that a good response should surface the impossibility itself?

<div class="ar-callout" markdown="1">

🔎 Can the evaluator distinguish **persistence from pathological persistence**, **helpfulness from pretending**, **legitimate problem solving from escaping the intended problem**, and failure from **correctly recognizing failure**?

</div>

---

## 04 — Stronger agents make the boundary matter more

A weak agent faced with an impossible task may simply get stuck.

A capable agent has more options.

It can search longer. It can inspect the environment. It can find unexpected tools. It can reason about the grader. It can discover loopholes the task designer never considered.

Capability expands the strategy space.

That is usually what we want. We build stronger agents precisely because they can recover from dead ends, combine tools creatively, and keep going where weaker systems stop.

But that same property makes a missing boundary more consequential.

If the evaluator cannot distinguish “solve the task” from “make the grader think the task was solved,” then additional capability can improve both.

<div class="ar-callout" markdown="1">

🎯 A sufficiently capable model may not fail at the task.

It may **succeed at the wrong problem**.

</div>

This is what makes the OpenAI–Hugging Face incident more than a strange edge case. OpenAI’s investigation found that the hardest and apparently unsolvable ExploitGym tasks were heavily represented in the agents’ shared discussion, and that agents spent unusually large amounts of reasoning effort on them while frequently reasoning about how to pass the grader.

A recent LessWrong post, [“OpenAI-HuggingFace: A Reproduction & Lessons for Alignment Testing”](https://www.lesswrong.com/posts/fMnC6ZD37qrnZAFYz/openai-huggingface-a-reproduction-and-lessons-for-alignment), reproduces related behaviors with publicly available models and reports that additional compute makes them easier to elicit.

So “the benchmark was broken” is not necessarily reassuring.

Broken tasks may be exactly where objective misspecification becomes easiest to see.

**They are adversarial examples for our evaluators.**

---

## 05 — A good evaluation needs a safe failure state

For some tasks, the highest-quality behavior is to finish the task.

For others, it is to ask a question.

And sometimes, the highest-quality behavior is:

> _There is no valid way to do this under the current constraints, and here is the evidence._

That outcome has to exist not only in the model’s policy, but in the evaluator’s ontology.

<div class="ar-callout" markdown="1">

✅ A good evaluation should be able to reward:

- identifying contradictory requirements;
- recognizing unavailable information;
- refusing to violate scope to manufacture success;
- terminating after legitimate approaches are exhausted.

</div>

This is not an argument for making agents less persistent.

Persistence is useful.

The goal is to make persistence conditional on the existence of a legitimate path forward.

We want agents that keep going when the problem is hard — and stop when continuing requires quietly changing the problem.

---

## 06 — The benchmark is not really the point

ImpossibleRubrics is a benchmark, but the broader failure mode is larger than benchmarks.

More AI systems are being trained and selected using generated rewards: rubrics, judges, reward models, verifiers, and other proxies for what we actually want.

<div class="ar-callout" markdown="1">

**impossible task → completion-oriented rubric → faithful judge → persistent agent → unintended strategy**

</div>

No component has to be obviously broken.

The task looks normal. The rubric looks detailed. The judge applies it correctly. The agent does what capable agents are supposed to do: it searches for a way to succeed.

And the composition is wrong.

That is why impossible tasks are interesting to us. They force an evaluator to reveal whether it understands the boundary of the task, rather than merely checking whether the requested outputs appeared.

The standard alignment question is:

> _Will the agent follow the rules?_

There is an earlier one:

<div class="ar-callout" markdown="1">

🚪 **Did we write rules that leave the agent somewhere safe to go?**

</div>

If the only rewarded outcome is “find a way to succeed,” then an impossible task is more than a bad benchmark item.

For a capable enough agent, it is an invitation to search for another game.

**A good evaluator should know when winning means not playing that game at all.**

---

### Sources / further reading

- [ImpossibleRubrics](https://impossiblerubrics.github.io/)
- [OpenAI: The Hugging Face incident and the road ahead](https://openai.com/index/hugging-face-incident-and-the-road-ahead/)
- [OpenAI-HuggingFace: A Reproduction & Lessons for Alignment Testing](https://www.lesswrong.com/posts/fMnC6ZD37qrnZAFYz/openai-huggingface-a-reproduction-and-lessons-for-alignment)
