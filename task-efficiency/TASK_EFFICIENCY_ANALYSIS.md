# 高效任务执行 Prompt / Skill 分析与设计

## 1. 原 Prompt 中文解释

原 Prompt 可自然地解释为：

> 对需要长时间运行的异步工作：
>
> - 如果只是用空输入轮询一个仍在运行的进程，等待时间必须至少设为 180 秒；不需要中间输出时，优先等 300 秒。
> - 使用 `functions.wait` 等待仍在运行的执行单元时，等待时间也必须至少为 180 秒。
> - 如果外层 `functions.exec` 中还嵌套了会等待的工具调用，外层执行单元的让出时间至少要比内部最长等待再多 30 秒，避免外层先于内层暂停并唤醒模型。
> - 如果 `write_stdin` 是在发送真实的交互输入，而不是空轮询，就不要套用上述长等待；交互输入应保持及时响应。
> - 这些等待工具会在进程或执行单元提前结束时立即返回。因此，不要为了重复说明“任务仍在运行”而主动唤醒模型。

这里的 `yield_time_ms` 更接近“本次工具调用在把控制权交回模型之前，最多等待多久”，而不是“强制进程至少运行多久”。如果底层操作提前完成，工具应提前返回。

这段 Prompt 的直接目标不是提高模型的推理能力，而是减少对长时间异步任务的短周期空轮询，以及避免内外两层等待的时序错配。

## 2. 原 Prompt 可能有效的机制

### 2.1 证据边界

应先区分三类结论：

1. **可由文本直接推出：** Prompt 明确改变了等待参数、轮询频率、交互输入的等待方式，以及内外层等待的相对时长。
2. **合理但未经验证：** 更少的模型唤醒可能降低 token 消耗、上下文切换、重复推理和误操作概率，但仅凭 Prompt 文本不能证明实际改善幅度或因果关系。
3. **更可能取决于 Harness：** 模型是否在每次 yield 后重新推理、等待是否占用上下文、会话句柄是否持久、输出如何缓冲、超时如何嵌套、失败后能否恢复，都由 Harness 和工具实现决定。

因此，更准确的因果表述是：

> 如果 Harness 会在短等待结束后重新唤醒模型，并把每次轮询及输出计入上下文，那么延长无操作等待、避免外层先返回，通常会减少无价值的控制权切换；这可能间接提升长任务稳定性和效率。

不能直接写成“长等待一定让模型更聪明”或“已经证明 Prompt 提升了任务成功率”。

### 2.2 具体设计到行为变化

| 具体设计 | 模型或系统行为变化 | 为什么可能改善执行 | 结论类型 |
| --- | --- | --- | --- |
| 空轮询等待至少 180 秒，优先 300 秒 | 仍在运行时更少把控制权交回模型 | 减少“检查一下仍没完成”的空回合、状态复述和重复决策 | 直接改变轮询；收益大小是未验证假设 |
| `functions.wait` 使用长等待 | 等待中的执行单元不被频繁查询 | 减少调度开销和上下文噪声，使模型把调用预算留给实际行动 | 直接改变等待；token 与稳定性收益取决于 Harness |
| 外层等待比内部最长等待多至少 30 秒 | 内部等待更可能先返回，外层不会抢先 yield | 避免嵌套等待竞态、失去内部结果或多一次模型续跑 | 时序关系可直接推出；具体 30 秒是否足够未经验证 |
| 真实交互输入不使用长等待 | 发送输入后快速交回控制或观察响应 | 防止需要问答、密码、确认或 REPL 输入的操作被人为延迟 | 直接机制 |
| 完成时提前返回 | 长上限不等于固定延迟 | 可以在减少轮询的同时保持完成后的响应速度 | 依赖工具确实支持 early return |
| 不为“仍在运行”唤醒模型 | 模型只在可行动事件出现时恢复 | 提高实际执行回合占比，降低无意义进度播报 | 直接行为要求；整体收益未经实验验证 |

### 2.3 对各维度的实际影响

#### 任务目标保持

**长等待与少唤醒 → 减少模型重新进入任务的次数 → 降低每次恢复时重新解释目标、发生局部漂移的机会。**

这是间接收益。原 Prompt 没有定义目标、成功条件或目标复核机制，所以它不能单独保证目标保持。

#### 长程任务分解

原 Prompt 没有任务分解规则。它只优化某一类“等待中的工具调用”。如果观察到分解能力提升，更可能是因为上下文噪声减少，而不是 Prompt 教会了模型如何分阶段。

#### 上下文管理与 token 效率

**减少空轮询 → 减少工具调用记录、状态说明和重复推理 → 可能降低上下文占用与 token 消耗。**

这一推断成立的前提是 Harness 会把这些回合保留在模型上下文或计入调用成本。如果轮询完全在模型外部完成，收益可能主要体现在调度和延迟，而不是 token。

#### 工作状态维护

**保留同一运行会话并等待 → 进程状态继续存在 → 比重新启动命令更容易保持工作连续性。**

但原 Prompt 没有要求保存会话句柄、当前阶段、已完成事项或恢复点。会话能否跨模型唤醒保持，同样是 Harness 能力。

#### 中间结果与 checkpoint / milestone

原 Prompt 没有保存中间结果，也没有 milestone 规则。长等待甚至可能减少观察中间输出的频率。真正的 checkpoint 需要另行保存关键决策、产物位置和已验证阶段，而不是简单地“等得更久”。

#### 错误恢复与中断恢复

避免外层先 yield 可以减少一种等待层级错配，但并不等于错误恢复。原 Prompt 没有规定：

- 如何识别进程失败；
- 如何判断部分副作用；
- 如何安全重试；
- 会话丢失后从哪里恢复；
- 哪些结果已经完成且不应重做。

因此，恢复能力主要仍取决于 Harness 的会话持久化和额外的状态记录策略。

#### 避免重复工作

**减少无意义恢复 → 减少模型误判“上一调用没在运行”并重复启动的机会。**

这能降低某类工具级重复，但不能防止逻辑级重复研究、重复编辑或重复测试。后者需要完成状态、幂等性检查和 artifact 验证。

#### 避免无限探索

原 Prompt 只减少等待期间的空转，并不限制研究分支或思考循环。无限探索需要“当前决策问题”“证据阈值”“停止条件”之类的明确规则。

#### 工具调用策略

这是原 Prompt 最直接、最强的部分：

- 把无输入轮询和真实交互输入区分开；
- 让内外层超时形成正确包含关系；
- 利用 early return，兼顾低轮询和完成响应速度；
- 只在产生可行动信息时恢复模型。

#### 验证、测试与完成判断

工具完成可以更及时地被观察，但“进程结束”不等于“任务成功”。原 Prompt 没有要求检查退出码、产物、测试、用户约束或最终完成条件。因此需要新增验证闭环。

#### 推理与执行比例

**减少轮询回合与过程播报 → 模型用于协调自身的回合更少 → 实际工具执行和结果验证占比可能提高。**

这是原 Prompt 最可信的间接收益之一，但仍需通过 A/B 数据验证，例如：模型唤醒次数、空轮询次数、总 token、重复工具调用、任务完成率和端到端时间。

### 2.4 更可能属于 Harness 或调度层的因素

以下问题不应仅靠 Prompt 解决：

- 工具是否支持事件驱动完成通知与 early return；
- model turn 是否在每次 yield 后自动触发；
- 内外层 timeout、网关 timeout 与作业 timeout 如何组合；
- 长等待是否占用 worker、并发槽、计费时间或连接资源；
- 输出是否缓冲、截断或丢失；
- 会话 ID、PTY、cell 和后台作业能否持久恢复；
- 新用户消息是否能打断等待；
- Harness 是否自动压缩上下文，压缩是否遗漏状态；
- 失败重试是否可能重复产生副作用；
- 系统是否有最大等待值、心跳要求或 60 秒通信约束。

更理想的 Harness 会在可行动事件发生时唤醒模型，并把“仍在运行”当作调度状态而不是新一轮推理任务。若 Harness 已如此实现，Prompt 中的固定长等待可能几乎没有额外价值。

## 3. 存在的问题与可以进一步优化的地方

### 3.1 原 Prompt 的问题

1. **固定数值被写成普遍真理。** 180、300 和“多 30 秒”可能适合某一实现，却可能超过另一 Harness 的最大值、通信时限或网关 timeout。
2. **绑定具体工具名。** `write_stdin`、`functions.wait`、`functions.exec` 不能直接迁移到其他 Agent Harness。
3. **只解决等待调度。** 它没有覆盖目标定义、阶段分解、状态账本、验证、恢复和完成条件。
4. **隐含 Harness 假设。** “工具会提前返回”“yield 会唤醒模型”“外层可包住内层”等前提没有显式声明。
5. **缺少失活上限。** 如果进程卡死、丢失或永不完成，单纯延长等待会延迟发现问题。
6. **缺少句柄持久化。** 没有要求保存 job/session/cell ID，恢复后可能无法继续等待。
7. **缺少幂等与部分成功检查。** 工具返回不确定时，重复调用可能产生重复副作用。
8. **可能与用户沟通约束冲突。** 有些环境要求在 60 秒内更新状态，或者用户明确需要中间输出。
9. **没有区分机器等待和模型计划。** 降低轮询并不会自动产生更好的任务分解或验证。
10. **没有评价指标。** 无法仅凭主观感觉判断是 Prompt、模型还是调度器带来的改善。

### 3.2 优化方向

- 把固定数字改为语义规则：在无需交互时使用 Harness 支持的最长安全、可提前返回的等待；外层 timeout 必须覆盖内层等待和合理余量。
- 把轮询触发条件改为“是否会产生可行动信息”，而不是机械定时。
- 明确长等待的例外：交互输入、健康检查、用户要求中间结果、无 early-return 能力、存在严格租约或超时。
- 保存运行句柄和当前状态，以便中断后恢复。
- 将调度纪律嵌入完整执行闭环：目标、模式选择、行动、验证、必要状态更新、继续或结束。
- 使用风险比例化验证，而不是对所有任务套用同样完整的流程。
- 用观测指标验证效果：完成率、端到端耗时、模型唤醒次数、空轮询次数、总 token、重复调用数、恢复成功率和无效状态播报数。

## 4. Long-Horizon Prompt

以下 Prompt 可直接复制使用：

```text
LONG-HORIZON TASK EXECUTION

Objective: Complete multi-stage work reliably while minimizing coordination overhead.

Core rule: Plan enough to execute, but do not let planning replace execution.

1. Establish the target
- Identify the final deliverables, critical constraints, and observable completion checks.
- If a missing choice would materially change the result or authorization, ask; otherwise make a reasonable, reversible assumption and state it briefly.

2. Build a minimal execution plan
- Divide the task into a small number of phases that each produce evidence, a decision, or a usable artifact.
- Identify dependencies and the next executable phase.
- Begin work as soon as this minimal plan is sufficient. Do not keep refining the plan without new evidence.

3. Execute and maintain compact state
- Prefer actions that create progress or evidence over process narration.
- Maintain a compact state record containing: final goal and completion checks; current phase and next action; verified completed work; decisions and evidence that must not be rediscovered; artifact locations or running-job handles; active blockers.
- Update state only at meaningful milestones, before likely interruption, or when a decision or failure changes the path.
- Do not repeat completed work unless evidence shows it is stale or invalid.

4. Use tools deliberately
- Each tool call must answer a question, change an artifact, verify a result, or advance an active operation.
- Prefer targeted inspection before broad search. Stop exploring when evidence is sufficient for the current decision.
- For asynchronous work, prefer event-driven or long safe waits that return early on completion. Poll only when new output can change the next action. Ensure enclosing timeouts outlast nested waits, preserve the operation handle, and keep real interactive input responsive.
- Treat timeout numbers as harness-specific rather than universal.

5. Verify and recover
- Verify every risky or dependency-forming phase before building on it.
- When an action fails, preserve successful work, capture the exact failure, diagnose the smallest relevant cause, and retry only the affected step.
- Before repeating a mutation, check whether the prior attempt partially or fully succeeded.
- If the same failure repeats without new evidence, change approach or report the blocker; do not loop.

6. Control scope and context
- Reconfirm the final goal at phase boundaries and before accepting new work that would expand scope.
- Preserve decision-relevant facts; discard transient logs, duplicate summaries, and superseded hypotheses.
- Report progress only when a milestone completes, the plan changes, user action is required, or a failure affects the outcome.

7. Finish deliberately
- Compare the result with the original deliverables and completion checks.
- Run verification proportional to risk and state any material limitation that could not be checked.
- When all in-scope completion checks pass, deliver the result and stop. Do not add unrequested improvements or continue exploring after completion.

Governing loop:
Goal → Assess → Plan minimally → Act → Verify → Update state if needed → Continue or Finish
```

## 5. Short-Horizon Prompt

以下 Prompt 可直接复制使用：

```text
SHORT-HORIZON TASK EXECUTION

Core rule: Understand → Execute → Verify → Finish.

- Identify the requested outcome and the few constraints that affect execution.
- If the task is clear, act immediately. Use at most a brief mental or one-line plan for dependent steps.
- Make the smallest sufficient change or analysis. Match existing conventions and do not expand scope.
- Use targeted tools only when they directly inform the next action or verify the result. Reuse available evidence and stop searching when it is sufficient.
- Run the narrowest meaningful verification for the requested outcome and its practical risk.
- If blocked, diagnose the specific failed step; do not restart successful work or repeat the same attempt without new evidence.
- Do not create formal checkpoints, repeat the request, narrate obvious actions, or continue after completion.
- Deliver the result, relevant verification, and any material limitation, then stop.
```

## 6. Long vs Short 对比

| 维度 | Short-Horizon | Long-Horizon |
| --- | --- | --- |
| Planning | 无计划或一行计划；足以立即行动 | 少量阶段计划；明确依赖和完成证据 |
| Decomposition | 只拆开必要的相邻步骤 | 拆成可验证、可恢复的阶段 |
| State Management | 通常依赖当前上下文 | 维护精简状态账本和产物位置 |
| Checkpoint | 默认不创建 | 在里程碑、关键决策和可能中断前创建 |
| Tool Usage | 最少、定向、快速闭环 | 有目的地组合工具，复用句柄与结果，管理异步等待 |
| Exploration | 只做回答当前问题所需的搜索 | 围绕明确不确定性探索，并设证据/决策停止条件 |
| Verification | 最小充分验证 | 阶段验证加最终整体验证，深度按风险调整 |
| Error Recovery | 修复失败步骤后快速重试 | 保留已完成阶段，分类故障，从最后有效点恢复 |
| Context Management | 保留当前任务所需信息即可 | 保存决定未来行动的事实，压缩日志与旧假设 |
| Progress Reporting | 通常只交付结果 | 仅在里程碑、路线变化、阻塞或需用户行动时报告 |
| Completion Criteria | 请求结果已产生且关键检查通过 | 所有交付物、约束、阶段依赖和最终检查闭环 |

### 不应直接移植到短任务的长程策略

- **持久状态账本：** 对单文件小改动，维护账本的成本可能高于重读变更本身。
- **阶段 checkpoint：** 若一步即可重做，记录每一步反而增加上下文与沟通负担。
- **周期性目标复核：** 短任务通常只需在完成前检查一次原始要求。
- **里程碑播报：** 会把简单执行拆成多个无价值回合。
- **恢复协议：** 没有异步作业、外部副作用或中断风险时，复杂恢复流程是过度设计。
- **广泛探索与方案矩阵：** 已有明显、低风险实现路径时，多方案比较会推迟行动。
- **阶段级全面验证：** 短任务应做最小充分验证，而不是重复执行全套测试。

判断原则不是“长程机制越多越可靠”，而是：只有当信息丢失、任务中断或错误传播的预期成本高于协调成本时，才引入相应机制。

## 7. 通用执行模型

```text
Goal and completion evidence
          ↓
Assess complexity and risk
          ↓
Choose the lightest reliable mode
          ↓
Act on the next decision or artifact
          ↓
Verify the observable outcome
          ↓
Update state only if continuation needs it
          ↓
Unmet completion check? ── yes → Continue
          │
          no
          ↓
Deliver and stop
```

| 频率 | 应包含的步骤 | 原因 |
| --- | --- | --- |
| Always | 识别结果、实际行动、比例化验证、完成判断、完成即停止 | 构成最小闭环 |
| Usually | 提取关键约束、检查相关现状、多步时用简短计划 | 多数任务受益，成本较低 |
| Long-task only | 阶段分解、状态账本、checkpoint、恢复句柄、里程碑汇报 | 只有在中断和遗忘成本较高时才划算 |
| Exception only | 广泛探索、回滚、升级权限、反复重试、额外状态报告 | 仅由不确定性、失败、风险或用户需求触发 |

协调开销可以近似理解为：模型花在“管理工作”而不是“完成工作”上的 token、回合、工具调用和延迟。降低它不等于取消所有计划和状态，而是让每一项协调行为都有明确用途：防止昂贵重做、支持正确决策、允许恢复，或者证明完成。

## 8. TASK_EFFICIENCY_SKILL.md

完整、独立、可直接使用的 Skill 已保存为 [TASK_EFFICIENCY_SKILL.md](./TASK_EFFICIENCY_SKILL.md)。它包含以下完整结构：

1. Purpose
2. Task Complexity Classification
3. Execution Modes
4. Universal Execution Loop
5. Long-Horizon Rules
6. Short-Horizon Rules
7. Tool Usage Rules
8. Context Management
9. Error Recovery
10. Verification
11. Completion Criteria
12. Anti-patterns

该文件带有通用 Skill frontmatter，但正文不依赖 Codex、Claude Code、Cursor 或任何特定 Harness。作为 system prompt 或 developer prompt 使用时，可保留或删除 frontmatter；正文语义不受影响。

## 9. Design Principles

1. 选择能够可靠完成任务的最轻执行模式。
2. 计划到足以行动即可，不让计划替代执行。
3. 每个工具调用都应产生信息、状态变化、验证或实际进展。
4. 只保存继续、恢复或避免重做所必需的状态。
5. 用可行动事件驱动模型恢复，减少无意义轮询与播报。
6. 探索必须服务于明确决策，并在证据充分时停止。
7. 失败时保留成功工作，只诊断和重试受影响步骤。
8. 验证深度与风险成比例，活动完成不等于结果正确。
9. 所有新增工作都必须追溯到原始目标或必要验证。
10. 完成条件满足后主动交付并停止。

总原则：**Do the work, preserve enough state to continue, verify the result, and stop when done.**
