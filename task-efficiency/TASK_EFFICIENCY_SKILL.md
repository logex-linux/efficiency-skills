---
name: task-efficiency
description: Select the lightest reliable execution strategy for micro, short, long, or open-ended agent tasks; preserve only the state needed to verify progress, recover, and stop cleanly.
---

# Task Efficiency Skill

## 1. Purpose

Maximize useful execution while minimizing coordination overhead.

Use the lightest process that can reliably complete the task. Plan only enough to act, preserve only enough state to continue or recover, verify the result in proportion to risk, and stop as soon as the requested outcome is complete.

This skill applies across coding, research, writing, data work, and tool-use tasks. Adapt tool names and waiting parameters to the active harness. Never treat this skill as permission to expand scope, access new systems, or make external changes the user did not authorize.

## 2. Task Complexity Classification

Classify the task before choosing an execution mode. Use the combined evidence, not token count or prompt length alone:

- number and dependency of steps;
- number of files, artifacts, systems, or tools involved;
- presence of external dependencies or asynchronous work;
- need for search, investigation, or experimentation;
- uncertainty about the solution or requirements;
- verification depth and consequence of error;
- likelihood of interruption or partial failure;
- need to preserve intermediate state for recovery.

Choose the cheapest mode that can reliably finish the task. Reclassify only when new evidence changes the task; do not restart completed work when changing modes.

## 3. Execution Modes

### Mode A — Micro Task

Use when the outcome is obvious, bounded, and can normally be completed in one direct action.

Loop: **Execute → Verify → Finish**

- Infer ordinary details when low-risk and reversible.
- Do not create a formal plan or checkpoint.
- Perform one minimal verification when there is something meaningful to check.
- Deliver immediately when complete.

### Mode B — Short Task

Use when a few connected actions are needed but durable state management is unnecessary.

Loop: **Understand → Execute → Verify → Finish**

- Identify the outcome and critical constraints briefly.
- Use a mental or one-line plan only if it helps execution.
- Make the smallest sufficient change or analysis.
- Run the narrowest meaningful verification.
- Stop without expanding the scope.

### Mode C — Long Task

Use when the task has multiple dependent phases, files, tools, or long-running operations, or when interruption is plausible.

Loop: **Plan → Execute → Checkpoint → Verify → Continue**

- Define the final outcome and observable completion evidence.
- Split work into a small number of verifiable phases.
- Start execution after the minimum useful plan exists.
- Maintain a compact state record and update it only when state changes materially.
- Verify each risky or dependency-forming phase before building on it.
- Resume from the last verified phase after interruption.
- End when the completion evidence is satisfied.

### Mode D — Complex / Open-ended Task

Use when important facts are unknown, several approaches are plausible, research is required, or failure probability is high.

Loop: **Explore → Decide → Execute → Validate → Update State → Continue**

- Make exploration answer a named decision or uncertainty.
- Time-box or evidence-bound each exploration branch.
- Compare viable approaches, record the decision and its basis, then execute.
- Prefer tests, tools, primary evidence, or small experiments over prolonged speculation.
- If discovery reduces uncertainty, downgrade to Mode C or B rather than remaining in exploration mode.

## 4. Universal Execution Loop

For every task:

1. **Goal:** Identify the requested outcome, constraints, and what would count as done.
2. **Assess:** Choose the lightest adequate execution mode.
3. **Act:** Take the next action that produces evidence or moves the artifact toward completion.
4. **Verify:** Check the action at a depth proportional to risk.
5. **Update state if necessary:** Record only information needed for coordination, continuation, or recovery.
6. **Continue or finish:** Continue only if a completion condition remains unsatisfied; otherwise deliver and stop.

Step frequency:

| Frequency | Steps |
| --- | --- |
| Always | identify outcome, act, verify proportionally, evaluate completion, stop when done |
| Usually | identify critical constraints, inspect relevant existing state, use a brief plan for dependent actions |
| Long-task only | phase decomposition, durable checkpoints, explicit state ledger, milestone reporting, resume logic |
| Exception only | broad exploration, rollback, escalation, repeated retries, extra progress reporting |

## 5. Long-Horizon Rules

For Modes C and D:

1. Define completion in observable terms before deep execution.
2. Use phases that produce evidence, a decision, or a usable artifact; avoid phases such as “think more.”
3. Keep a compact state ledger containing only:
   - final goal and completion checks;
   - current phase and next action;
   - verified completed work;
   - decisions and evidence that must not be rediscovered;
   - artifact locations or handles for running work;
   - active blockers or failed attempts relevant to recovery.
4. Update the ledger at meaningful milestones, before a likely interruption, and after a decision or failure changes the path. Do not rewrite it after every tool call.
5. Reconfirm the final goal at phase boundaries or when new work would expand scope.
6. Build on verified outputs. Do not repeat completed research, edits, or tests unless evidence makes them stale or invalid.
7. For asynchronous work, prefer event-driven or long safe waits that return early on completion. Poll only when new output can change the next action. Preserve the job or session handle needed to resume.
8. Report progress only when a milestone completes, the plan changes, user action is required, or a failure affects the outcome.
9. When completion checks pass, provide the result, limitations, and relevant verification, then stop.

## 6. Short-Horizon Rules

For Modes A and B:

- Do not create a state ledger, milestone system, or formal checkpoint unless interruption becomes likely.
- Do not restate the request or narrate obvious steps.
- Avoid broad discovery when a targeted inspection can answer the question.
- Prefer one direct execution path over comparing many hypothetical approaches.
- Verify the changed behavior, output, or key claim with the smallest meaningful check.
- If the task unexpectedly grows, preserve completed work and promote it to Mode C; do not restart.
- Deliver immediately once the requested result is complete.

## 7. Tool Usage Rules

- Every tool call must answer a question, change the artifact, verify a result, or advance an active asynchronous operation.
- Batch independent reads or checks when the harness supports it and doing so reduces latency without obscuring failures.
- Reuse existing results, handles, and sessions. Do not repeat a call merely because the model resumed.
- Prefer targeted search before broad search. Stop exploring when the evidence is sufficient for the current decision.
- Use the least expensive tool that can produce reliable evidence; use a more powerful tool when risk or ambiguity requires it.
- For long-running asynchronous operations, use the longest safe event-driven wait supported by the environment when no intermediate input is needed. Ensure any enclosing timeout outlasts the nested wait. Keep interactive input responsive rather than attaching a long wait to it.
- Treat numeric timeout values as harness-specific configuration, not universal rules.
- Before retrying a state-changing action, determine whether the previous attempt may already have succeeded. Use idempotency, status inspection, or artifact checks when available.
- Stop retrying when the same failure repeats without new evidence; change the approach or surface the blocker.

## 8. Context Management

- Keep the user’s requested outcome and completion conditions more prominent than process narration.
- Preserve facts that affect future decisions: confirmed constraints, chosen approach, evidence, completed phases, artifact locations, and unresolved blockers.
- Drop transient logs, superseded hypotheses, duplicate summaries, and details that can be cheaply re-read.
- Prefer references to durable artifacts over pasting their full contents into repeated summaries.
- Summarize only when context is at risk, a handoff or interruption is likely, or accumulated detail obscures the next action.
- After resuming, read the latest state and verify artifacts or external status that may have changed; continue from the last verified point.

## 9. Error Recovery

When an action fails:

1. Preserve successful prior work.
2. Capture the exact failure and the operation that produced it.
3. Classify the cause as input, environment, permission, dependency, transient service, implementation, or unknown.
4. Run the smallest diagnostic that can distinguish the leading causes.
5. Correct the cause and retry only the affected step.
6. Verify whether partial side effects occurred before repeating a mutation.
7. If retries produce no new evidence, choose a materially different approach or report the blocker and required next action.

Do not restart the whole task unless prior state is corrupt, invalid, or more expensive to recover than to rebuild.

## 10. Verification

Verification should be proportional to risk and should test observable outcomes rather than the existence of activity.

- **Code:** run the narrow relevant test, lint, type, build, or behavior check; expand only when impact warrants it.
- **Research:** trace important claims to suitable sources, distinguish evidence from inference, and resolve material contradictions.
- **Writing:** check requested meaning, audience, structure, factual support, and format.
- **Data:** validate inputs, transformations, key totals, edge cases, and output shape.
- **Tool use:** confirm the intended external state or artifact, especially after ambiguous or asynchronous operations.

Do not claim full verification when checks were unavailable. State what was verified, what was not, and the practical consequence.

## 11. Completion Criteria

A task is complete when:

- every requested deliverable exists in the requested form;
- critical constraints are satisfied;
- relevant verification passes or any unverified limitation is disclosed;
- no known blocker prevents normal use of the result;
- no remaining action is required within the authorized scope.

Before finishing, perform one concise completion check against the original request. Do not invent optional follow-up work to keep the task active.

## 12. Anti-patterns

- **Endless planning:** refining the plan after there is already enough information to take a safe next action. Fix: act and let evidence refine the plan.
- **Premature planning:** building a detailed plan before inspecting the minimum facts needed to make it valid. Fix: do one targeted discovery step first.
- **Repeated summarization:** restating unchanged goals or history on every turn. Fix: update only changed state.
- **Unnecessary checkpointing:** recording trivial actions that are cheap to repeat. Fix: checkpoint only expensive, decision-forming, or interruption-sensitive work.
- **Excessive tool calls:** calling tools without a decision or verification purpose. Fix: name the expected information or state change before calling.
- **Excessive exploration:** continuing research after evidence is sufficient to choose and execute. Fix: set an evidence threshold or decision question.
- **Restarting completed work:** discarding verified progress after an interruption or local failure. Fix: resume from the last valid checkpoint.
- **Scope creep:** improving adjacent areas or adding unrequested features. Fix: tie every action to a requested deliverable or necessary verification.
- **Premature completion:** stopping after activity rather than confirming the outcome. Fix: check deliverables and observable behavior.
- **Continuing after completion:** adding analysis, tools, or features after all completion checks pass. Fix: deliver and stop.

The governing rule is:

> Do the work, preserve enough state to continue, verify the result, and stop when done.
