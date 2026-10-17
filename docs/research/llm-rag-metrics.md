# Research: LLM and RAG metric catalog and LLM-as-Judge best practices

Resolves the research question of issue #4 (child of map #2). Researched 2026-10-16.

**Question.** Which LLM and RAG metrics (RAGAS, DeepEval, G-Eval, etc.) and which
LLM-as-Judge practices (rubrics, judge bias, calibration) are worth adopting in
Assayer? For each metric: definition, inputs, deterministic or judge-based, and
overlap with what Assayer already has.

**Sources.** Primary only: the RAGAS and DeepEval official documentation, and the
G-Eval, MT-Bench and RAGAS papers on arXiv. Each claim carries a bracketed source tag
listed in [Sources](#sources). Claims marked *(repo)* come from this repository's code.
Claims marked *(inference)* are the researcher's judgment, not a source's statement.

## Summary

- Assayer today covers reference-based text metrics (BLEU, ROUGE-L, BERTScore,
  semantic similarity), classification (accuracy, precision, recall, F1), NER macro-F1,
  an NLI/Jaccard `FaithfulnessEvaluator`, a single-prompt `LLMJudgeEvaluator`, and
  consistency statistics (agreement rate, entropy, pass@k) *(repo)*.
- The largest gap is **RAG-specific metrics** (retrieval quality and claim-level
  faithfulness) and a **configurable, rubric-based judge**.
- Recommended adoption order: (1) claim-level faithfulness, (2) context
  precision/recall with the non-LLM and ID-based variants first, (3) a G-Eval-style
  custom judge with explicit steps and a rubric, (4) answer relevancy, (5) factual
  correctness. Defer agentic, multimodal, safety and conversational metrics.
- Judge practices worth building in from the start: swap-order double judging for
  pairwise use, explicit rubrics/steps instead of free criteria, recorded judge
  prompt hash and model (already partly there), and human calibration on a small
  labeled set.

## What Assayer already has *(repo)*

| Area | Existing | Kind |
|---|---|---|
| Text generation | `bleu`, `rouge_l`, `bert_score`, `make_semantic_similarity` in `assayer/metrics/chat.py` | deterministic (model-based embeddings for BERTScore and similarity) |
| Classification | `accuracy`, `make_precision`, `make_recall`, `make_f1` | deterministic |
| NER | `ner_macro_f1` | deterministic |
| Hallucination | `FaithfulnessEvaluator` (NLI cross-encoder entailment, Jaccard fallback) | model-based, not an LLM judge |
| Judge | `LLMJudgeEvaluator`: one system prompt, returns a single float in [0, 1], no explanation | LLM-as-judge |
| Consistency | agreement rate, entropy, score std, correct rate, pass@k, recall@k | deterministic over repeated runs |

Metrics are pure functions `(predictions, references) -> float`; evaluators are
`BaseEvaluator` subclasses. A claim-level or retrieval metric needs more inputs than
`(predictions, references)` (for example retrieved contexts), so most RAG metrics fit
the evaluator interface, not the metric-function one *(inference)*.

## RAG metric catalog

Scores are 0 to 1 unless noted. Overlap column refers to the table above.

| Metric | Definition | Inputs | Deterministic or judge | Overlap with Assayer |
|---|---|---|---|---|
| Faithfulness (RAGAS) | Share of response claims supported by the retrieved context. An LLM splits the response into claims and checks each against context [R-faith]. A variant swaps verification for the HHEM-2.1-Open classifier [R-faith]. | `user_input`, `response`, `retrieved_contexts` [R-faith] | LLM judge (HHEM variant: small classifier) | Partial: `FaithfulnessEvaluator` scores whole-text entailment, not per-claim |
| Faithfulness (DeepEval) | Truthful claims divided by total claims, where a claim is truthful if it does not contradict `retrieval_context` [D-faith] | `input`, `actual_output`, `retrieval_context` [D-faith] | LLM judge by default; `hybrid` and `system_one` modes use the Jev model [D-faith] | Same as above |
| Hallucination (DeepEval) | Share of provided `context` documents the output stays consistent with. Source of truth is curated `context`, not retrieved chunks; DeepEval says not to use it on a live RAG system [D-halluc] | `input`, `actual_output`, `context` [D-halluc] | LLM judge (also hybrid, system_one) | Close to `LLMJudgeEvaluator` and `FaithfulnessEvaluator` |
| Context Precision | Mean precision@k over ranked retrieved chunks, so relevant chunks ranked higher score better [R-cp] | LLM variant: `user_input`, `reference`, `retrieved_contexts`. Without-reference variant (`ContextUtilization`) uses `response`. Non-LLM: `retrieved_contexts`, `reference_contexts`. ID-based: `retrieved_context_ids`, `reference_context_ids` [R-cp] | LLM, non-LLM (string similarity) or ID matching | None |
| Context Recall | Reference claims supported by retrieved context divided by reference claims [R-cr]. Non-LLM and ID-based variants count reference contexts that were retrieved [R-cr] | `user_input`, `retrieved_contexts`, `reference`; non-LLM: `reference_contexts`; ID: context ids [R-cr] | LLM, non-LLM or ID | None |
| Answer / Response Relevancy | An LLM generates artificial questions (3 by default) from the response; score is mean cosine similarity of their embeddings to the user input embedding. Does not check factual accuracy; can dip below 0 [R-ar] | `user_input`, `response` [R-ar] | LLM plus an embedding model | Partial: semantic similarity machinery exists but compares to a reference |
| Noise Sensitivity | Share of response claims that are incorrect, optionally attributed to relevant or irrelevant retrieved context. Lower is better [R-ns] | `user_input`, `reference`, `response`, `retrieved_contexts` [R-ns] | LLM judge | None |
| Factual Correctness | Claim decomposition of response and reference, NLI between them, then precision, recall or F1 (default F1) [R-fc] | `response`, `reference` [R-fc] | LLM judge | Partial overlap with BERTScore/semantic similarity goals, but claim-level |
| G-Eval / custom criteria | User-defined criteria turned into evaluation steps, scored by an LLM, normalized by token probabilities [G-Eval, D-geval] | Any chosen test-case fields (`evaluation_params`) [D-geval] | LLM judge | Generalizes `LLMJudgeEvaluator` |
| Rubric / criteria scoring (RAGAS) | Aspect Critic, Simple Criteria Scoring, Rubrics-Based Scoring, Instance-Specific Rubrics Scoring exist as general-purpose metrics; the catalog page does not describe them [R-catalog] | Not stated on the catalog page | Not stated | Generalizes `LLMJudgeEvaluator` |
| Semantic Similarity, BLEU, ROUGE, chrF, exact match, string presence (RAGAS) | Listed in the RAGAS catalog under natural-language comparison [R-catalog] | Not stated on the catalog page | Listed as non-LLM string or embedding comparisons | Already covered (BLEU, ROUGE-L, semantic similarity); chrF, exact match, string presence are cheap additions |

Out of Assayer's current scope, noted for completeness: agent and tool-use metrics
(Tool Call Accuracy, Tool Call F1, Agent Goal Accuracy, Topic Adherence in RAGAS;
Task Completion, Tool Correctness and others in DeepEval), multi-turn chatbot metrics,
safety metrics (Bias, Toxicity, PII leakage), image metrics, SQL metrics
[R-catalog][D-intro]. Revisit only if Assayer grows agent or safety evaluation.

Notes on the sources:

- The RAGAS paper frames the suite as reference-free evaluation across three
  dimensions: retrieval relevance, faithful use of passages, and generation quality
  [RAGAS-paper]. The current RAGAS docs, however, require a `reference` for Context
  Recall, Noise Sensitivity and Factual Correctness [R-cr][R-ns][R-fc]. Treat
  "reference-free" as true only for faithfulness, answer relevancy and
  `ContextUtilization`.
- RAGAS marks the `LLMContextPrecision*` and `LLMContextRecall` legacy classes for
  deprecation in 0.4 and removal in 1.0 [R-cp][R-cr]. Assayer should copy the
  definitions, not the class names or API.
- DeepEval says almost all predefined metrics are LLM-as-judge (QAG, DAG, G-Eval), and
  every metric returns a 0 to 1 score plus a reason with a default pass threshold of
  0.5 [D-intro]. Its `system_one` scores are not comparable to LLM-mode scores [D-faith].

## LLM-as-Judge practices

### Known judge biases and mitigations [MT-Bench]

| Issue | Evidence | Mitigation in the source |
|---|---|---|
| Position bias | GPT-4 with the default prompt gave consistent verdicts under swapped order only 65.0% of the time; it favored the first slot 30.0% and the second 5.0% [MT-Bench] | Judge twice with positions swapped; declare a win only if both runs agree, otherwise tie. Three few-shot examples raised consistency to 77.5% at about 4x prompt cost [MT-Bench] |
| Verbosity bias | In a repetitive-list attack, Claude-v1 and GPT-3.5 failed 91.3% of cases and GPT-4 failed 8.7% [MT-Bench] | None specified in the paper [MT-Bench] |
| Self-enhancement bias | Named as a studied bias [MT-Bench abstract]; this research did not retrieve the quantitative result | Not retrieved |
| Weak math and reasoning grading | Judge can be misled by the answer it grades. Failure rate on 20 math cases: 70% baseline, 30% with chain-of-thought, 15% with reference-guided grading [MT-Bench] | Have the judge solve the problem first, or give it a reference answer [MT-Bench] |
| Bias toward LLM-generated text | G-Eval authors flag it as a potential issue in preliminary analysis [G-Eval] | Not specified |

Agreement with humans: strong judges such as GPT-4 reach over 80% agreement with
human preferences, "the same level of agreement between humans" [MT-Bench abstract].

### Rubrics, steps and score stability [D-geval][G-Eval]

- G-Eval has the LLM reason step by step and fill a structured evaluation form
  without needing human references [G-Eval]. With GPT-4 it reached Spearman 0.514
  with human judgments on summarization [G-Eval].
- DeepEval's G-Eval: giving only `criteria` makes the metric generate its own steps,
  so scores can vary between runs. Supplying fixed `evaluation_steps`, adding a
  `rubric` that confines scores to defined bands, or using `strict_mode` (binary 1/0)
  reduces variation. DeepEval's own workflow is to start with `criteria`, review the
  generated steps, then freeze them as `evaluation_steps` [D-geval].
- Token-probability weighting of the score is used to reduce scoring bias, and needs
  log probabilities from the judge model; without them DeepEval falls back to the raw
  integer score [D-geval]. Whether Assayer's LangChain `BaseChatModel` path can expose
  logprobs depends on the provider *(inference, not verified)*.
- List only the test-case fields the criteria reference; extra fields add irrelevant
  context and can lower the score [D-geval].
- G-Eval is not deterministic; DeepEval points to `DAGMetric` for fully rule-based
  control [D-geval].

### Calibration

None of the sources fetched prescribes a calibration procedure beyond measuring
agreement with human labels, as MT-Bench does [MT-Bench]. A practical calibration
step is *(inference)*: keep a small human-labeled set per metric, report judge-vs-human
agreement (for example Spearman or Cohen's kappa) alongside the metric, and re-run it
whenever the judge model or prompt changes.

## Recommendations for Assayer

All recommendations are *(inference)* drawn from the evidence above.

1. **Claim-level faithfulness** (RAGAS/DeepEval definition: supported claims over
   total claims). Highest value, closest to the existing hallucination focus. Keep
   `FaithfulnessEvaluator` as the cheap deterministic-ish baseline and add the
   claim-level variant as a judge-based sibling.
2. **Context precision and recall, non-LLM and ID-based variants first.** They need
   no judge, are reproducible, and fit Assayer's deterministic metric style. Add the
   LLM variants later.
3. **Upgrade `LLMJudgeEvaluator` toward G-Eval style.** Today it returns an
   unexplained float from one fixed prompt. Allow configurable criteria with explicit
   `evaluation_steps` and an optional rubric, return a reason, and persist the prompt
   hash and judge model with each result (`hash_prompt` already exists).
4. **Answer relevancy** once an embedding dependency is acceptable; it needs an LLM and
   an embedding model [R-ar].
5. **Factual correctness** for reference-based claim-level checks when a ground-truth
   answer exists [R-fc].
6. **Judge hygiene by default**: swap-order double judging for any pairwise or
   ranking use [MT-Bench]; reference-guided judging for math or reasoning-like
   fields [MT-Bench]; never use the candidate model as its own judge where avoidable
   (self-enhancement) *(inference)*; report judge-vs-human agreement on a labeled
   sample.
7. **Defer** agent, multi-turn, safety, image and SQL metrics, and DeepEval's
   Jev/`system_one` mode, which is a proprietary-model dependency whose scores are not
   comparable to LLM-mode scores [D-faith].

### Open questions

- Metric-function signature `(predictions, references)` cannot carry retrieved
  contexts. Decide whether RAG metrics are evaluators (needs per-field context) or
  whether the metric interface is extended. Out of scope for this research.
- The RAGAS rubric metrics were listed but not described on the page fetched; read
  their individual pages before copying them.
- Self-enhancement bias numbers were not retrieved from the MT-Bench full text.

## Sources

- [R-catalog] RAGAS, available metrics: https://docs.ragas.io/en/stable/concepts/metrics/available_metrics/
- [R-faith] RAGAS, Faithfulness: https://docs.ragas.io/en/stable/concepts/metrics/available_metrics/faithfulness/
- [R-cp] RAGAS, Context Precision: https://docs.ragas.io/en/stable/concepts/metrics/available_metrics/context_precision/
- [R-cr] RAGAS, Context Recall: https://docs.ragas.io/en/stable/concepts/metrics/available_metrics/context_recall/
- [R-ar] RAGAS, Answer Relevancy: https://docs.ragas.io/en/stable/concepts/metrics/available_metrics/answer_relevance/
- [R-ns] RAGAS, Noise Sensitivity: https://docs.ragas.io/en/stable/concepts/metrics/available_metrics/noise_sensitivity/
- [R-fc] RAGAS, Factual Correctness: https://docs.ragas.io/en/stable/concepts/metrics/available_metrics/factual_correctness/
- [D-intro] DeepEval, metrics introduction: https://deepeval.com/docs/metrics-introduction
- [D-faith] DeepEval, Faithfulness: https://deepeval.com/docs/metrics-faithfulness
- [D-halluc] DeepEval, Hallucination: https://deepeval.com/docs/metrics-hallucination
- [D-geval] DeepEval, G-Eval: https://deepeval.com/docs/metrics-llm-evals
- [G-Eval] Liu et al., G-Eval, arXiv:2303.16634: https://arxiv.org/abs/2303.16634
- [MT-Bench] Zheng et al., Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena, arXiv:2306.05685: https://arxiv.org/abs/2306.05685 (full text: https://arxiv.org/html/2306.05685)
- [RAGAS-paper] Es et al., RAGAS, arXiv:2309.15217: https://arxiv.org/abs/2309.15217

Limits of this research: pages were read through a summarizing fetch tool, so
formulas and figures are as reported by that tool and should be spot-checked against
the linked pages before being copied into code.
