"""Corpus metrics: scores computed over all the outputs of an Experiment at once.

BLEU, ROUGE, BERTScore, semantic similarity, classification and NER compare the
predictions of a whole Experiment with the references of its Cases, so they sit at
the Experiment level. Run per Field, they see that Field's values only.
"""

from collections.abc import Callable
from typing import Any

from assayer.metrics.chat import bert_score, bleu, make_semantic_similarity, rouge_l
from assayer.metrics.classification import accuracy, make_f1, make_precision, make_recall
from assayer.metrics.metric import Metric
from assayer.metrics.ner import ner_macro_f1
from assayer.models import Experiment


def corpus_metric(name: str, fn: Callable[[list[Any], list[Any]], float]) -> Metric:
    """Lift a `(predictions, references)` function into an Experiment-level Metric.

    Each Trajectory is one prediction (its `final_output`) paired with the
    `expected_output` of its Case, so a Case run k times counts k times (the
    corpus is pooled, not averaged per Case).

    Args:
        name: Name of the metric; becomes the name of its Score.
        fn: Corpus function returning a number in [0, 1].

    Returns:
        A Metric that requires `expected_output` on every Case.
    """

    def over_experiment(experiment: Experiment, case=None) -> float:
        references = {c.id: c.expected_output for c in experiment.cases}
        predictions = [t.final_output for t in experiment.trajectories]
        return fn(predictions, [references[t.case_id] for t in experiment.trajectories])

    return Metric(name=name, level="experiment", fn=over_experiment, requires=("expected_output",))


def register_corpus_metrics(registry) -> None:
    """Register the corpus metrics into a registry.

    Registers bleu, rouge_l, bert_score, semantic_similarity, accuracy, precision,
    recall, f1 (the last three macro-averaged) and ner_macro_f1.

    Args:
        registry: The Registry to fill.

    Raises:
        KeyError: If one of the names is already registered.
    """
    corpus_fns = {
        "bleu": bleu,
        "rouge_l": rouge_l,
        "bert_score": bert_score,
        "semantic_similarity": make_semantic_similarity(),
        "accuracy": accuracy,
        "precision": make_precision("macro"),
        "recall": make_recall("macro"),
        "f1": make_f1("macro"),
        "ner_macro_f1": ner_macro_f1,
    }
    for name, fn in corpus_fns.items():
        registry.register(corpus_metric(name, fn))
