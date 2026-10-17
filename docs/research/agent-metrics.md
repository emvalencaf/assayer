# Research: agent metric catalog

Resolves issue #3 (child of map #2).

**Question.** Which agent evaluation metrics exist in the literature and market
sources (AWS Bedrock AgentCore Evaluations, Medium, papers)? For each: definition,
required inputs, deterministic vs judge-based, and maturity.

**Method and caveats.** Primary sources were fetched for AWS (blog and developer
guide), DeepEval, Ragas, tau-bench and the Yehudai et al. survey. Medium items
come from search snippets only and were not read in full. Exact formulas not
confirmed in a primary source are marked "unverified". Maturity is our judgment:
**high** = documented by a vendor/library or a peer-reviewed benchmark with a stable
definition; **medium** = documented but definitions vary between sources;
**low** = appears only in practitioner posts.

## 1. Sources

| Source | Kind | Notes |
|---|---|---|
| [AWS News Blog: AgentCore quality evaluations](https://aws.amazon.com/blogs/aws/amazon-bedrock-agentcore-adds-quality-evaluations-and-policy-controls-for-deploying-trusted-ai-agents/) | vendor | Preview announced 2025-12-02; page notes GA on 2026-03-31. |
| [AgentCore devguide: Evaluators](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/evaluators.html), [prompt templates](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/prompt-templates-builtin.html), [code-based evaluators](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/code-based-evaluators.html) | vendor docs | Authoritative for evaluator names, levels, inputs. |
| [DeepEval: Tool Correctness](https://deepeval.com/docs/metrics-tool-correctness) | OSS library | Also exposed inside AgentCore as a third-party evaluator. |
| [Ragas: agent metrics](https://docs.ragas.io/en/stable/concepts/metrics/available_metrics/agents/) | OSS library | |
| [tau-bench (arXiv 2406.12045)](https://arxiv.org/pdf/2406.12045) | paper | Introduces pass^k and end-state comparison. |
| [Survey on Evaluation of LLM-based Agents (arXiv 2503.16416)](https://arxiv.org/abs/2503.16416) | paper | Taxonomy, not a metric list; flags gaps in cost-efficiency, safety, robustness, fine-grained evaluation. |
| Medium: [Agent Evaluation for LLMs (Chapter 8)](https://medium.com/@vinodkrane/chapter-8-agent-evaluation-for-llms-how-to-test-tools-trajectories-and-llm-as-judge-788f6f3e0d52), [Evaluating AI Agents: Metrics, Challenges, and Practices](https://medium.com/@TechforHumans/evaluating-ai-agents-metrics-challenges-and-practices-c5a0444876cd), [LLM Evaluation Metrics](https://medium.com/@jaberi.mohamedhabib/llm-evaluation-metrics-choose-the-right-metric-for-every-task-667b45d1a432), [Field Guide](https://medium.com/@vfcarida/a-strategic-field-guide-for-generative-ai-and-agent-evaluation-techniques-metrics-and-maturity-e425b394181e) | practitioner | Snippet-level only. Names overlap, definitions differ. |
| [Beyond Task Completion (arXiv 2512.12791)](https://arxiv.org/pdf/2512.12791) | paper | Seen in search results only; not read. |

## 2. Catalog

Legend for "Type": **D** deterministic (code comparison), **J** judge-based (LLM),
**H** hybrid.

### 2.1 Outcome metrics

| Metric | Definition | Required inputs | Type | Maturity | Sources |
|---|---|---|---|---|---|
| Task completion / goal success | Did the agent achieve the user's goal? Usually binary (Ragas Agent Goal Accuracy: 1/0) or a rating scale (AgentCore Goal Success Rate, session level). | Full trajectory (messages + tool calls); optional reference outcome. | J (AgentCore, Ragas). D when an end state is checkable. | high | AWS, Ragas, Medium |
| Goal success with ground truth | Same, judged against a supplied expected outcome or assertions. | Trajectory + reference. | J | high (AgentCore ships a distinct "with ground truth" template) | AWS, Ragas ("with reference" variant) |
| End-state match | Compare final environment/database state with an annotated goal state; no transcript grading. | Final state + annotated goal state. | D | high | tau-bench |
| Response correctness | Factual accuracy of the final answer; ground-truth variant exists. | Turn context + response; optional reference. | J | high | AWS |
| Faithfulness | Response supported by provided context/tool output. | Context + response. | J | high | AWS |
| Helpfulness | 1-5 usefulness from user's view (AgentCore scale: Very Unhelpful to Very Helpful). | Turn context + response. | J | medium | AWS |
| Coherence, conciseness, instruction following, refusal, response relevance | Additional AgentCore trace-level quality evaluators. | Turn context + response. | J | medium | AWS |
| Harmfulness, stereotyping, safety | Content-safety checks. | Prompt + response. | J | medium | AWS |
| Topic adherence | Stays inside predefined domains; reports precision/recall/F1. | Conversation + reference topics. | J | medium | Ragas |

### 2.2 Tool-use metrics

| Metric | Definition | Required inputs | Type | Maturity | Sources |
|---|---|---|---|---|---|
| Tool selection accuracy | Did the agent pick the right tool at this step? AgentCore evaluates per tool call. | Available tools (id, params, description) + context + the tool call. No reference needed. | J | high | AWS |
| Tool parameter accuracy | Are arguments correct and faithful to the user request/context? AgentCore prompt focuses on "parameter faithfulness". | Same as above. | J | high | AWS |
| Tool correctness | `correct tools / total tools called`. Name match by default; stricter via input-parameter/output matching, ordering, exact-match options. Optional LLM optimality check when `available_tools` given (final = min of both). Default threshold 0.5. | `input`, `actual_output`, `tools_called`, `expected_tools`; optionally `available_tools`. | D core, optional J (H) | high | DeepEval |
| Tool call accuracy | Score of agent tool calls vs expected calls covering sequence and arguments; strict or flexible order; 0-1. | `user_input`, `reference_tool_calls`. | D (inferred from examples; unverified) | high | Ragas |
| Tool call F1 | Precision/recall F1 of calls vs expected, unordered, exact argument match. | `user_input`, `reference_tool_calls`. | D (inferred; unverified) | medium | Ragas |
| Tool call accuracy, binary variant | Correct tools with correct args, with LLM-judged functional equivalence. | Trajectory + reference. | J | low | arXiv result snippet (unverified) |
| Skill selection accuracy / skill instruction following | Whether a loaded skill was the right one and was followed. AgentCore-specific. | Skill catalog, skill content, user message. | J | low (new) | AWS |

### 2.3 Trajectory and efficiency metrics

| Metric | Definition | Required inputs | Type | Maturity | Sources |
|---|---|---|---|---|---|
| Trajectory quality | Judge of the step-by-step decision path, not just the final output. | Full trajectory; optionally reference trajectory. | J | medium | Medium, AWS ground-truth (expected tool trajectories) |
| Trajectory / step efficiency | Minimal unnecessary calls and queries; fewer steps means lower cost, latency and failure risk. No agreed formula found. | Trajectory; optional optimal step count. | D (step count vs reference) or J | medium (concept) / low (formula) | Medium |
| Non-productive loops, premature completion, missing validation | Failure-mode labels from judges, mostly for coding agents. | Trajectory. | J | low | arXiv snippet (AgentLens, unverified) |
| Milestone-level evaluation | Score intermediate milestones as well as end result; the survey distinguishes turn-, milestone- and trajectory-level. | Trajectory + milestone definitions. | D or J | medium | secondary summary of the survey (unverified) |

### 2.4 Reliability, cost and system metrics

| Metric | Definition | Required inputs | Type | Maturity | Sources |
|---|---|---|---|---|---|
| pass^k | Success in all k independent trials of the same task (stricter than pass@k = any of k). tau-bench: gpt-4o-class agents < 50% task success, pass^8 < 25% on retail. | k runs per task + a per-run success signal. | D over a success signal | high | tau-bench |
| Token usage, latency, tool-call frequency, failure recovery | System metrics reported alongside quality. | Telemetry/traces. | D | medium | Medium |
| Cost-efficiency | Called out as an under-served area. | Telemetry. | D | low | Yehudai et al. |

## 3. Cross-cutting findings

1. **Three evaluation levels recur.** AgentCore scores at session, trace (turn) and
   tool-call level, and its code-based evaluators receive `evaluationLevel` of
   `SESSION`, `TRACE` or `TOOL_CALL`. The survey's turn/milestone/trajectory split
   is similar. A metric API should declare which level it operates on.
2. **Reference-free vs reference-based is the key input split.** AgentCore tool
   selection/parameter accuracy need no reference (tool catalog + context only).
   DeepEval and Ragas tool metrics need an expected tool list. Goal success exists
   in both forms (Ragas with/without reference; AgentCore with/without ground
   truth).
3. **Deterministic metrics are the minority.** Deterministic: tool correctness core,
   tool call accuracy/F1 (likely), end-state match, pass^k, token/latency counts.
   Most outcome and quality metrics are judge-based. AgentCore built-ins are all
   LLM-judge and not modifiable; deterministic checks go through custom
   code-based evaluators (Lambda returning `label`, optional `value` 0-1, optional
   `explanation`).
4. **Naming is inconsistent.** "Tool correctness" (DeepEval), "tool call accuracy"
   (Ragas), "tool selection accuracy" (AWS) differ in whether they check
   arguments, order, or optimality. A catalog needs explicit definitions rather
   than relying on names.
5. **Judge caveats.** Medium sources note position and verbosity bias in LLM
   judges and recommend calibration against human labels and layering
   deterministic checks, statistical metrics and judges.
6. **Variance matters.** Single-run scores overstate reliability; pass^k is the only
   reliability metric with a primary-source definition.
7. **Gaps.** No primary-source formula for trajectory/step efficiency. Cost,
   safety and robustness are flagged as under-served by the survey.

## 4. Suggested starting set (for the map #2 decision)

Highest maturity and clearest inputs, in rough priority:

1. Task completion / goal success (binary, with optional reference), judge-based.
2. Tool correctness and tool call accuracy/F1 against a reference tool list
   (deterministic, cheapest to test).
3. Tool selection and parameter accuracy, reference-free, judge-based.
4. End-state match, where a final state is available.
5. pass^k over repeated runs.
6. Step count / efficiency as a simple deterministic ratio against a reference,
   explicitly documented as our own definition.

## 5. Open questions

- Confirm Ragas tool call accuracy/F1 are non-LLM by reading the implementation.
- Read the full Yehudai et al. survey for its metric-level taxonomy, and
  arXiv 2512.12791, before citing them for metrics.
- Medium articles were summarised from snippets; re-read before quoting.
- Settle a single definition for trajectory efficiency.
