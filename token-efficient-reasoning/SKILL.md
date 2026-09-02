---
name: token-efficient-reasoning
description: Improve reasoning token utilization for analysis, research, coding, and tool workflows with adaptive depth, compact state notes, targeted verification, and explicit stop conditions; use when a model overthinks, repeats self-checks, or wastes tokens polling asynchronous work.
---

# Token-Efficient Reasoning

## Purpose

Maximize useful progress per token while preserving correctness, uncertainty reporting, safety, and required verification. “Short” is not the objective by itself: the objective is the shortest process that is sufficient for the task.

Use this skill when the model tends to:

- repeat the prompt or restate the same conclusion;
- narrate simulated human hesitation or use filler such as “Hmm”;
- ask open-ended self-doubt questions without taking an action;
- perform the same calculation or review more than once;
- spend the same reasoning depth on trivial and difficult tasks;
- poll a long-running process frequently just to report that it is still running.

Do not use brevity to skip safety checks, source verification, tests, user-requested detail, or uncertainty that materially affects the answer.

## Operating doctrine

Treat reasoning as a controlled state transition:

```text
task → difficulty/risk → minimal sufficient plan → state updates → targeted check → stop
```

Do not model the process as an open-ended stream of inner monologue. Remove low-information narration, but retain every fact, transformation, constraint, decision, contradiction, or uncertainty needed to reach or audit the result.

## Adaptive reasoning protocol

### 1. Classify before expanding

- **Direct mode:** simple retrieval, transformation, formatting, or an answer already determined by the provided information. Answer directly.
- **Compact mode:** multi-step analysis, coding, math, or planning. Make a short plan and record only essential state changes.
- **Verified mode:** high-stakes, time-sensitive, factual, numerical, code, or externally consequential work. Use authoritative sources, tools, tests, or an independent verifier where available.

Do not force every request into chain-of-thought. Do not force a fixed token budget onto a problem that needs more information. If the task is harder than the available budget, state the limitation or use a more reliable verification route.

### 2. Make intermediate work information-dense

For each step, keep only one of:

- a new fact or extracted evidence;
- a calculation or transformation;
- a constraint or assumption;
- a decision and its reason;
- an identified error and its correction.

Do not repeat the question, paraphrase the previous step, explain that you are thinking, or add emotional or conversational filler. Prefer shorthand, equations, structured fields, and compact tables when they preserve auditability.

If examples are available, imitate concise, information-dense examples rather than merely adding a word-count command. A hard limit such as “five words per step” is an experiment, not a universal rule; do not omit a step that is necessary to reproduce or verify the result.

### 3. Check only at a meaningful checkpoint

A check must name its object. Good objects include an equation, source claim, citation scope, code behavior, boundary condition, rule, or plan constraint.

Use the following compact format by default:

```text
关键断点：<可核对对象>
对吗？对。
```

If it is wrong:

```text
关键断点：<可核对对象>
对吗？不对。改为：<修正>
```

Rules:

- “对” means continue immediately.
- “不对” means correct immediately and continue.
- Check each meaningful checkpoint at most once unless the correction introduces a new critical assumption.
- Never use the check as a ritual or append a second “再检查” pass without a new risk signal.
- If binary judgment is not justified, write `证据不足，需要：<具体信息或验证>` rather than inventing certainty.
- Prefer external or executable verification over free-form self-critique: source lookup, calculation, code execution, unit tests, schema validation, or independent comparison.

### 4. Stop when sufficient

Stop when the answer is supported by the required evidence, the key constraints pass, and no unresolved high-impact contradiction remains. Do not continue because there is remaining context, token budget, or a stylistic expectation to “think harder.”

For repeated candidates or samples, stop when the decision is stable under the selected consistency rule. Do not sample or review easy items as many times as hard items without a reason.

## Language and output style

- Lead with the answer or current result.
- Give only the rationale, evidence, calculations, or caveats that change the user’s decision.
- Report uncertainty semantically: `证据不足`, `无法判断`, `需要外部验证`, or `置信度低/中/高`.
- Do not output simulated inner speech, emotional interjections, self-reassurance, repeated apologies, or commentary with no state change.
- If the user asks how the result was obtained, provide a concise rationale or audit trail. Do not expose private or raw hidden chain-of-thought; provide the useful conclusions, checks, and evidence instead.

## Long-running asynchronous work: mandatory wait discipline

The following requirements are mandatory whenever a process, command, cell, task, or tool call is still running asynchronously:

- Empty `write_stdin` polls **MUST** use `yield_time_ms >= 180000`; prefer `300000` when intermediate output is not needed.
- `functions.wait` **MUST** use `yield_time_ms >= 180000`.
- `functions.exec` **MUST** set its outer `@exec yield_time_ms` at least 30000 ms longer than the longest nested tool wait, so the outer code cell does not yield first.
- Do not apply the long wait to non-empty `write_stdin` calls that send interactive input.
- These tools return early when the process or cell completes. Do not wake the model merely to report that work is still running.

When orchestrating nested calls, calculate the outer wait before sending the call. For example, if the longest nested wait is 300000 ms:

```javascript
// @exec: {"yield_time_ms": 330000}
const result = await tools.exec_command({
  cmd: "long-running-command",
  yield_time_ms: 300000,
});
text(result.output);
```

For an empty poll, use a long wait and inspect only when output, completion, failure, or required input is available. For an interactive call that sends input, use a wait appropriate to the interaction and do not apply the 180000 ms minimum merely because the process is long-running.

## Tool-call economy

- Search or inspect once with a focused query before broadening it.
- Parallelize independent read-only checks when the tools support it.
- Do not repeat an unchanged tool call to manufacture progress.
- Do not poll an unchanged asynchronous state merely to send a status update.
- Keep tool output bounded to the evidence needed for the current decision.
- After a tool returns a definitive result, continue from it instead of re-deriving the same result in prose.

## Silent token audit before final output

Before responding, check silently:

1. Did I repeat the request or previous conclusion without adding information?
2. Did I perform a redundant self-check, calculation, search, or poll?
3. Is every check tied to a falsifiable object or reliable verifier?
4. Can I stop now without losing a required caveat, safety condition, or verification result?

If a final response is needed, output the result and the minimum decision-relevant support. Do not output this audit.
