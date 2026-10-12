---
name: jev-work-judgment
description: 通过 Jev 的结构化判断辅助工作中的分类、选项比较、优先级和材料核验。用户明确要求使用 Jev，或工作任务需要一个边界清楚的选择、是非判断或分级评分时使用；不用于开放式写作、长链推理、精确计算或图像理解。
---

# Jev 工作判断

Jev 是 TypeSafe 的 System One 决策模型。它接收 state 和一组 typed questions，返回 Choice、Score、Noul 及概率；它不生成解释、文案或推理过程。把 Jev 当作某个具体判断的信号来源，再由你结合证据和用户目标给出可读建议。

## 适用方式

- 适合有限答案空间：分类、排序信号、优先级、候选方案筛选、规则或草稿核验。
- 不要把“分析并给出最佳方案”整句交给 Jev。先拆成互相独立、可由当前 state 判断的问题；开放式分析与写作由你完成。
- 一次请求中的所有问题共享同一 state，彼此独立。针对同一材料的多个判断尽量放在一个请求里；每个问题只测一个维度。
- 仅发送回答这些问题所需的最少上下文。不要把 API key、密码、访问令牌或无关个人资料放进 state；可先匿名化。用户要求用 Jev 本身授权将完成判断所必需的内容发送给 OpenRouter，但对敏感资料仍先删减或匿名化；无法在不发送敏感内容的情况下判断时，先向用户说明并询问。

## 设计问题

- `choice`：从有限且互斥的选项中选一个。`criteria` 是选项名到具体适用描述的映射；可能漏项时加 `other` 或 `insufficient_evidence`。
- `score`：衡量单一连续维度。`criteria` 是从低到高排列的 2–10 条具体情形描述，不要只写数字或“好/一般/差”。分数是加权位置，可以落在两个等级之间。
- `noul`：问一个清晰的是非命题，返回“是”的概率；必要时用 `criteria.true` 和 `criteria.false` 明确判断边界。
- 问题说明要点名 state 中相关字段、给出判断边界，并避免重叠选项。若判断依赖几个因素，分别提问；不要把人为权重交给 Jev，除非用户提供了权重。

## 调用

使用本 skill 目录中的 `scripts/jev_decide.py`。通过 stdin 传入 JSON，包含 `state` 和 `questions`；问题格式遵循 TypeSafe 的 typed question schema。脚本默认使用 OpenRouter 模型别名 `~typesafe/jev-latest`，也可用 `--model` 覆盖。它只从环境变量 `OPRT_API_KEY` 读取密钥，不要打印、回显或写入密钥。

示例：

```sh
python3 /absolute/path/to/jev-work-judgment/scripts/jev_decide.py <<'JSON'
{
  "state": {"request": "这项工作需不需要今天优先处理？", "known_deadline": "今天 17:00"},
  "questions": {
    "priority": {
      "type": "choice",
      "instructions": "根据 request 和 known_deadline，这项工作现在应如何处理？",
      "criteria": {
        "do_now": "今天有明确截止时间，延后会错过交付或造成实质影响。",
        "schedule_today": "需要今天完成，但暂时等待不会影响结果。",
        "defer": "没有近期截止或可见的延迟成本。",
        "insufficient_evidence": "现有信息不足以区分以上情况。"
      }
    }
  }
}
JSON
```

根据已加载的 `SKILL.md` 位置解析脚本的绝对路径。用用户已配置的 shell 环境运行脚本，使 `.zshrc` 导出的 `OPRT_API_KEY` 可用；若变量不可用就停止并说明，不要读取或打印整个配置文件。不要通过 `echo`、`env`、调试日志或命令参数暴露 key。脚本只把 `state`、`questions`、`model` 发往 `https://openrouter.ai/api/alpha/decisions`。

## 解读并回答

- 展示答案类型、所选项/分数/是的概率，以及返回的 probabilities 和 confidence（若有）。Noul 的 `noul` 是“是”的概率，不带单独 confidence。
- Choice/Score 的 confidence 描述概率分布是否集中，不代表答案正确的保证；任何单次判断都可能出错。分布分散、置信度低或选项接近时，明确说结果不确定，必要时补充证据或请用户决定。不要套用通用置信度阈值。
- Score 要同时解释等级和概率分布；相同分数可能来自不同的分布。不要只把小数分数说成客观测量。
- 把模型输出与可核验事实、规则和用户提供的偏好分开。精确日期、计数、计算和权限判断交给事实来源或确定性逻辑核对。
- 向用户给出简洁结论、关键概率与主要不确定性。Jev 的选择不是对外发送、发布、购买、删除或其他有后果操作的授权。

## 参考

- TypeSafe System One 概念与限制：https://docs.typesafe.ai/concepts/system-one
- TypeSafe 问题类型与格式：https://docs.typesafe.ai/primitives
- TypeSafe HTTP API：https://docs.typesafe.ai/api
- OpenRouter Jev Decisions API 用法：https://openrouter.ai/blog/tutorials/jev-vs-llm-when-to-use-each/
